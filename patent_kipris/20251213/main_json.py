# -*- coding: utf-8 -*-
"""
KIPRIS /kpat/resulta.do
2002~2022년: (출원인 only) 삼성 / SK하이닉스 / 포스코홀딩스 전체 수집
- 각 출원인별 JSON 파일 "따로" 저장
- 조회(현실적 분할): AP=[출원인] * AN=[연도]
- 최종 필터(정확 판정): AD(출원일자) 연도 == 조회 연도
- 중복제거(용량 절감): DOCID 1순위, DOCID 없으면 AN 보조
- 저장: JSON (원본 KEY 그대로)
- 로그: [#] 원본 JSON 한 줄 + (아래) 한글명(KEY)=값 한 줄
        + 진행번호(출원인/연도/페이지/누적채택)

저장되는 JSON key (원본 그대로):
DOCID, AD, AP, TRH, AN, LSTO, IN, BCTC, IPC

주의:
- HEADERS["cookie"]는 반드시 최신 값으로 교체
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# 설정
# =========================
URL = "https://www.kipris.or.kr/kpat/resulta.do"

YEAR_FROM = 2002
YEAR_TO = 2022
TOTAL_YEARS = YEAR_TO - YEAR_FROM + 1

NUM_PER_PAGE = 90
REQUEST_TIMEOUT = 30
PAGE_SLEEP_SEC = 0.25

# 저장할 원본 KEY 목록
KEEP_KEYS = ["DOCID", "AD", "AP", "TRH", "AN", "LSTO", "IN", "BCTC", "IPC"]

# 로그용 한글명 매핑(저장은 원본키 그대로)
KEY_LABELS = {
    "DOCID": "고유번호",
    "AD": "출원일자",
    "AP": "출원인",
    "TRH": "최종권리자",
    "AN": "출원번호",
    "LSTO": "법적상태",
    "IN": "발명자",
    "BCTC": "피인용수",
    "IPC": "IPC코드",
}

# 수집 대상 출원인 (only)
APPLICANTS = [
    "삼성전자주식회사",
    "에스케이하이닉스주식회사",
    "포스코홀딩스주식회사",
]

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "ko-KR,ko;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.kipris.or.kr",
    "referer": "https://www.kipris.or.kr/khome/search/searchResult.do",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
    # ★ 반드시 최신 쿠키로 교체 ★
    # "cookie": "여기에_브라우저에서_복사한_최신_COOKIE",
}

_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()


def make_session() -> requests.Session:
    sess = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess


def build_expression(applicant: str, year: int) -> str:
    # 현실적 분할: 출원인 + 출원번호에 연도 문자열 포함
    return f"AP=[{applicant}]*AN=[{year}]"


def page_request(sess: requests.Session, expr: str, page: int) -> Dict[str, Any]:
    payload = {
        "queryText": expr,
        "expression": expr,
        "historyQuery": expr,
        "numPerPage": str(NUM_PER_PAGE),
        "numPageLinks": "10",
        "currentPage": str(page),
        "piSearchYN": "N",
        "sortField": "RANK",
        "sortState": "Desc",
    }
    r = sess.post(URL, headers=HEADERS, data=payload, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def ad_year_match(ad: Any, year: int) -> bool:
    s = clean(ad)
    return len(s) >= 4 and s[:4].isdigit() and int(s[:4]) == year


def pick_item_raw(item: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k in KEEP_KEYS:
        out[k] = item.get(k)
    return out


def korean_line(raw: Dict[str, Any]) -> str:
    parts = []
    for k in KEEP_KEYS:
        label = KEY_LABELS.get(k, k)
        parts.append(f"{label}({k})={clean(raw.get(k))}")
    return " / ".join(parts)


def safe_filename(name: str) -> str:
    # 파일명용 간단 치환(공백/특수문자 최소 처리)
    return (
        name.replace(" ", "")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )


def crawl_one_applicant(sess: requests.Session, applicant: str) -> str:
    """
    출원인 1명 전체 수집 → 중복 제거 → JSON 저장
    반환: 저장 파일명
    """
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    out_path = f"kipris_{safe_filename(applicant)}_{YEAR_FROM}_{YEAR_TO}_dedup_{ts}.json"

    # 중복제거 저장소 (출원인별로 독립)
    results: Dict[str, Dict[str, Any]] = {}
    seen_an_fallback = set()

    total_kept = 0
    total_dupe = 0
    total_filtered = 0

    log("\n" + "=" * 60)
    log(f"[출원인 시작] {applicant}")
    log("=" * 60)

    for year_idx, year in enumerate(range(YEAR_FROM, YEAR_TO + 1), start=1):
        expr = build_expression(applicant, year)
        log(f"\n[출원인={applicant}] [연도 {year_idx:02d}/{TOTAL_YEARS}] ▶ {year}년 시작 | expression={expr}")

        page = 1
        while True:
            try:
                data = page_request(sess, expr, page)
            except Exception as e:
                log(f"[오류] applicant={applicant} year={year} page={page} 요청 실패: {e}")
                break

            lst = (data or {}).get("resultList") or []
            log(
                f"[페이지] applicant={applicant} year={year} page={page} 수신={len(lst)}"
                f" | 누적채택={total_kept} | 중복={total_dupe} | 필터제외={total_filtered}"
            )

            if not lst:
                log(f"[종료] applicant={applicant} year={year} page={page} 결과 없음")
                break

            for item in lst:
                if not ad_year_match(item.get("AD"), year):
                    total_filtered += 1
                    continue

                docid = clean(item.get("DOCID"))
                an = clean(item.get("AN"))

                # === 중복 제거 ===
                if docid:
                    if docid in results:
                        total_dupe += 1
                        continue
                    store_key = docid
                else:
                    if an and an in seen_an_fallback:
                        total_dupe += 1
                        continue
                    store_key = f"AN::{an}" if an else f"NOID::{applicant}::{year}::{page}::{total_kept}"

                raw = pick_item_raw(item)
                results[store_key] = raw
                if (not docid) and an:
                    seen_an_fallback.add(an)

                total_kept += 1

                # ===== 로그: 1) 원본 JSON 한 줄  2) 한글 매핑 한 줄 =====
                raw_one_line = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
                log(f"[{applicant} #{total_kept}] {raw_one_line}")
                log(f"      {korean_line(raw)}")

            page += 1
            time.sleep(PAGE_SLEEP_SEC)

    log("\n" + "-" * 60)
    log(f"[출원인 완료] {applicant}")
    log(f"[통계] 중복 제거 후 총 건수: {len(results)}")
    log(f"[통계] 채택={total_kept}, 중복제거={total_dupe}, AD필터제외={total_filtered}")
    log(f"[저장] {out_path}")
    log("-" * 60)

    with open(out_path, "w", encoding="utf-8") as f:
        # indent 없이 저장(용량 절감)
        json.dump(list(results.values()), f, ensure_ascii=False)

    return out_path


def run():
    sess = make_session()
    saved_files = []

    for idx, applicant in enumerate(APPLICANTS, start=1):
        log(f"\n\n########## [{idx}/{len(APPLICANTS)}] 출원인 처리 시작: {applicant} ##########")
        out_path = crawl_one_applicant(sess, applicant)
        saved_files.append(out_path)

    log("\n====================")
    log("[전체 완료] 저장 파일 목록")
    for p in saved_files:
        log(f" - {p}")
    log("====================")


if __name__ == "__main__":
    run()
