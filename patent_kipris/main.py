# -*- coding: utf-8 -*-
"""
[전체] KIPRIS dedup JSON(출원인별) → 엑셀 변환 → family.do로 패밀리정보(수)/국내여부 채움 → 출원인별 엑셀 3개 저장
+ 작업상황(제출/완료/속도/ETA) 로그가 계속 찍히도록 배치(Chunk) 방식으로 개선

입력:
- kipris_삼성전자주식회사_2002_2022_dedup_20251213224155.json
- kipris_에스케이하이닉스주식회사_2002_2022_dedup_20251213231015.json
- kipris_포스코홀딩스주식회사_2002_2022_dedup_20251213231523.json

출력(각각 1개씩):
- out_삼성전자주식회사.xlsx
- out_에스케이하이닉스주식회사.xlsx
- out_포스코홀딩스주식회사.xlsx

중요:
- 쿠키 없이 family.do 요청 시 서버가 막으면 패밀리수가 0으로만 나올 수 있음.
- 대량 처리 시 'submit만 오래 걸려 로그가 멈춘 것처럼' 보이던 문제를 해결하기 위해:
  1) 배치 단위로 submit → 완료 로그 → 다음 배치
  2) 스레드별 requests.Session 사용(안정)
  3) 주기적 진행상황 로그(속도/ETA 포함)
"""

import json
import re
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd
import requests


# =========================
# 입력/출력 설정
# =========================
INPUTS: List[Tuple[str, str, str]] = [
    ("삼성전자주식회사", "kipris_삼성전자주식회사_2002_2022_dedup_20251213224155.json", "out_삼성전자주식회사.xlsx"),
    ("에스케이하이닉스주식회사", "kipris_에스케이하이닉스주식회사_2002_2022_dedup_20251213231015.json", "out_에스케이하이닉스주식회사.xlsx"),
    ("포스코홀딩스주식회사", "kipris_포스코홀딩스주식회사_2002_2022_dedup_20251213231523.json", "out_포스코홀딩스주식회사.xlsx"),
]

FAMILY_URL = "https://kopd.kipo.go.kr:8888/family.do"

# 동시성/배치
MAX_WORKERS = 8
BATCH_SIZE = 800            # ✅ 진행 로그 잘 보이면서 안정적인 단위 (500~2000 추천)
LOG_EVERY_N_DONE = 200      # ✅ 완료 로그 출력 주기
MID_SAVE_EVERY_BATCH = 5    # ✅ 배치 5개마다 중간 저장(원하면 0으로 두면 꺼짐)

# 요청/재시도
REQ_TIMEOUT = 15
RETRY = 3
BACKOFF_SEC = 1

# 너무 공격적이면 차단될 수 있어 약간 딜레이(필요 없으면 0.0)
SUBMIT_SLEEP_SEC = 0.0

FAMILY_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://kopd.kipo.go.kr:8888",
    "referer": "https://kopd.kipo.go.kr:8888/index.do",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    # cookie intentionally removed
}

_print_lock = threading.Lock()


def log(*msg):
    with _print_lock:
        print(*msg, flush=True)


def _clean(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_eta(seconds: Optional[float]) -> str:
    if seconds is None:
        return "-"
    if seconds < 0:
        seconds = 0
    sec = int(seconds)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


# =========================
# JSON 로드/파싱
# =========================
def load_json_list(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise Exception(f"JSON 최상위가 배열(list)이 아님: {path}")
    return data


def parse_inventor_count(in_field: Any) -> Any:
    s = _clean(in_field)
    if not s:
        return ""
    return s.count("|") + 1


def parse_cited_count(bctc_field: Any) -> Any:
    s = _clean(bctc_field).replace(",", "")
    if not s:
        return ""
    return int(s) if s.isdigit() else ""


# =========================
# family.do 조회
# =========================
def build_docdb_number_from_ori(ori_number: str) -> str:
    """
    기존 로직 유지:
    ori_number: 1020040090349 -> core=20040090349 -> KR.20040090349.A
    """
    s = _clean(ori_number)
    if len(s) < 3:
        return ""
    core = s[2:]
    return f"KR.{core}.A"


def extract_family_from_html(html: str) -> Tuple[int, str]:
    """
    familyTable 내 input[name=countryCode] value 들을 모아:
    - 패밀리정보(수) = len(set(codes))
    - 국내여부 = set이 KR만이면 "국내"
    """
    codes = re.findall(r'name="countryCode"\s+value="([^"]+)"', html, flags=re.IGNORECASE)
    codes = [c.strip() for c in codes if c and c.strip()]

    if not codes:
        return 0, ""

    all_codes = set(codes)
    fam_cnt = len(all_codes)
    domestic = "국내" if all_codes and all_codes.issubset({"KR"}) else ""
    return fam_cnt, domestic


def fetch_family_info(row_idx: int, ori_number: str, session: requests.Session) -> Tuple[int, int, str]:
    """
    return: (row_idx, family_count, domestic_flag)
    """
    ori_number = _clean(ori_number)
    if not ori_number or ori_number.lower() == "nan":
        return row_idx, 0, ""

    docdb_number = build_docdb_number_from_ori(ori_number)
    if not docdb_number:
        return row_idx, 0, ""

    payload = {
        "numberType1": "original",
        "ori_country": "KR",
        "ori_numberType": "U1301",
        "ori_number": ori_number,
        "docdb_numberType": "U1301",
        "docdb_number": docdb_number,
    }

    for attempt in range(1, RETRY + 1):
        try:
            resp = session.post(FAMILY_URL, headers=FAMILY_HEADERS, data=payload, timeout=REQ_TIMEOUT)
            if resp.status_code != 200:
                log(f"[패밀리][idx={row_idx}] 응답코드 {resp.status_code} (시도 {attempt}/{RETRY})")
                time.sleep(BACKOFF_SEC)
                continue

            fam_cnt, domestic = extract_family_from_html(resp.text)
            return row_idx, fam_cnt, domestic

        except Exception as e:
            log(f"[패밀리][idx={row_idx}] 예외 (시도 {attempt}/{RETRY}): {str(e)}")
            time.sleep(BACKOFF_SEC)

    return row_idx, 0, ""


# =========================
# DF 생성/채우기
# =========================
def json_to_dataframe(items: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for it in items:
        rows.append({
            "출원일자": _clean(it.get("AD")),
            "출원인": _clean(it.get("AP")),
            "TRH 최종권리자": _clean(it.get("TRH")),
            "출원번호(일자)": _clean(it.get("AN")),  # family.do ori_number
            "법적상태": _clean(it.get("LSTO")),
            "발명자수": parse_inventor_count(it.get("IN")),
            "피인용 (수)": parse_cited_count(it.get("BCTC")),
            "패밀리정보 (수)": 0,
            "국내여부": "",
            "IPC (풀코드)": _clean(it.get("IPC")),
            "DOCID": _clean(it.get("DOCID")),
        })
    df = pd.DataFrame(rows)

    col_order = [
        "출원일자",
        "출원인",
        "TRH 최종권리자",
        "출원번호(일자)",
        "법적상태",
        "발명자수",
        "피인용 (수)",
        "패밀리정보 (수)",
        "국내여부",
        "IPC (풀코드)",
        "DOCID",
    ]
    for c in col_order:
        if c not in df.columns:
            df[c] = ""
    return df[col_order]


def fill_family_counts_batched(df: pd.DataFrame, label: str, excel_out: str) -> pd.DataFrame:
    total = len(df)
    if total == 0:
        return df

    start = datetime.now()
    done = 0
    ok_nonzero = 0
    zero_cnt = 0
    err_cnt = 0

    # 스레드별 session
    thread_local = threading.local()

    def get_session():
        s = getattr(thread_local, "session", None)
        if s is None:
            s = requests.Session()
            thread_local.session = s
        return s

    def task(row_idx: int, ori_number: str):
        try:
            return fetch_family_info(row_idx, ori_number, get_session())
        except Exception:
            # fetch_family_info 안에서 대부분 처리하지만, 혹시 몰라서
            return row_idx, 0, ""

    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    log(f"\n=== [{label}] 패밀리 조회 시작 === total={total:,}, workers={MAX_WORKERS}, batch={BATCH_SIZE}, start={start} ===")

    for b in range(total_batches):
        batch_start = b * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch_df = df.iloc[batch_start:batch_end]

        log(f"[{label}] [배치 {b+1}/{total_batches}] 제출: {batch_start+1:,} ~ {batch_end:,} / {total:,} ({now_str()})")

        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {}
            for idx, row in batch_df.iterrows():
                ori_number = str(row["출원번호(일자)"]).strip()
                fut = ex.submit(task, idx, ori_number)
                futures[fut] = idx
                if SUBMIT_SLEEP_SEC > 0:
                    time.sleep(SUBMIT_SLEEP_SEC)

            # 배치 내 완료 처리
            for fut in as_completed(futures):
                try:
                    idx, fam_cnt, domestic = fut.result()
                except Exception:
                    idx, fam_cnt, domestic = futures[fut], 0, ""
                    err_cnt += 1

                done += 1
                if fam_cnt > 0:
                    ok_nonzero += 1
                else:
                    zero_cnt += 1

                results.append((idx, fam_cnt, domestic))

                # 진행 로그(너무 과다 출력 방지)
                if (done <= 20) or (done % LOG_EVERY_N_DONE == 0):
                    elapsed = (datetime.now() - start).total_seconds()
                    rate = done / elapsed if elapsed > 0 else 0.0
                    remain = total - done
                    eta = remain / rate if rate > 0 else None
                    progress = (done / total) * 100.0

                    log(
                        f"[{label}] 진행 {done:,}/{total:,} ({progress:.2f}%)"
                        f" | nonzero={ok_nonzero:,} zero={zero_cnt:,} err={err_cnt:,}"
                        f" | rate={rate:.2f} rows/s | ETA={format_eta(eta)}"
                    )

        # 배치 결과 적용
        for idx, fam_cnt, domestic in results:
            df.at[idx, "패밀리정보 (수)"] = fam_cnt
            df.at[idx, "국내여부"] = domestic

        # 중간 저장(원하면)
        if MID_SAVE_EVERY_BATCH and (b + 1) % MID_SAVE_EVERY_BATCH == 0:
            tmp_path = excel_out.replace(".xlsx", f".tmp_batch{b+1}.xlsx")
            df.to_excel(tmp_path, index=False)
            log(f"[{label}] [중간저장] {tmp_path} ({now_str()})")

    end = datetime.now()
    elapsed = end - start
    log(f"=== [{label}] 패밀리 조회 완료 === end={end}, elapsed={elapsed} ===")
    log(f"=== [{label}] 요약: nonzero={ok_nonzero:,}, zero={zero_cnt:,}, err={err_cnt:,} ===")
    return df


# =========================
# 출원인별 처리
# =========================
def process_one(applicant: str, json_path: str, excel_out: str):
    log("\n" + "=" * 80)
    log(f"[START] {applicant}")
    log(f"  JSON:  {json_path}")
    log(f"  EXCEL: {excel_out}")
    log("=" * 80)

    items = load_json_list(json_path)
    log(f"[INFO] {applicant} JSON 건수: {len(items):,}")

    df = json_to_dataframe(items)
    log(f"[INFO] {applicant} 엑셀 변환 rows: {len(df):,}")

    df = fill_family_counts_batched(df, applicant, excel_out)

    df.to_excel(excel_out, index=False)
    log(f"[OK] 저장 완료: {excel_out} ({now_str()})")


def run():
    for applicant, json_path, excel_out in INPUTS:
        try:
            process_one(applicant, json_path, excel_out)
        except Exception as e:
            log(f"[ERROR] {applicant} 처리 실패: {e}")

    log("\n[ALL DONE] 3개 엑셀 저장 완료")


if __name__ == "__main__":
    run()
