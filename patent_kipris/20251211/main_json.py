# -*- coding: utf-8 -*-
"""
KIPRIS /kpat/resulta.do 조건 검색기 (JSON 저장 버전)

- 입력 엑셀: kipris_request_list.xlsx
  컬럼:
    "NO"
    "AP"
    "AN"
    "IPC"

- 동작:
  1) 엑셀에서 NO, AP, AN, IPC 컬럼을 읽어 요청 목록 구성
  2) 각 행에 대해 expression = "AN=[...]*IPC=[...]*AP=[...]" 형식으로 검색
  3) 페이지가 끝날 때까지 모든 page의 resultList를 수집
  4) 수집한 각 JSON item에 "kipris_no" 필드로 해당 NO 값을 추가
     (한 조건에서 100건이 나오면 100건 모두 kipris_no=해당 NO)
  5) 전체 결과를 하나의 JSON 배열로 묶어
     result_json_YYYYMMDDHHMMSS.json 파일로 저장
"""

import json
import time
import threading
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# =========================
# 설정
# =========================
EXCEL_PATH_IN = "kipris_request_list.xlsx"

URL = "https://www.kipris.or.kr/kpat/resulta.do"
NUM_PER_PAGE = 90
REQUEST_TIMEOUT = 30  # sec
PAGE_SLEEP_SEC = 0.3
MAX_WORKERS = 8       # 동시 실행 스레드

# ★★ 여기 COOKIE는 반드시 최신값으로 바꿔서 사용하세요 ★★
HEADERS_BASE = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.kipris.or.kr",
    "referer": "https://www.kipris.or.kr/khome/search/searchResult.do",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
    # "cookie": "여기에_브라우저에서_복사한_최신_COOKIE_문자열",
}

_print_lock = threading.Lock()


def _log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


# =========================
# 공통 헬퍼
# =========================
def _clean(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def make_session() -> requests.Session:
    """재사용 가능한 requests.Session 생성 (Retry 포함)"""
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


def build_expression(ap: str, an: str, ipc: str) -> str:
    """
    검색 expression 구성
    - 예시: AN=[2002]*IPC=[F24F]*AP=[삼성전자주식회사]
    - AP/AN/IPC 중 비어있는 것은 제외
    """
    parts: List[str] = []

    ap = _clean(ap)
    an = _clean(an)
    ipc = _clean(ipc)

    if an:
        parts.append(f"AN=[{an}]")
    if ipc:
        parts.append(f"IPC=[{ipc}]")
    if ap:
        parts.append(f"AP=[{ap}]")

    return "*".join(parts)


def page_request(
        sess: requests.Session,
        headers: Dict[str, str],
        expression: str,
        current_page: int,
) -> Optional[Dict[str, Any]]:
    """단일 페이지 요청"""
    payload = {
        "queryText": expression,
        "expression": expression,
        "historyQuery": expression,
        "numPerPage": str(NUM_PER_PAGE),
        "numPageLinks": "10",
        "currentPage": str(current_page),
        "piSearchYN": "N",
        "beforeExpression": "",
        "prefixExpression": "",
        "downYn": "N",
        "downStart": "",
        "downEnd": "",
        "viewField": "",
        "fileType": "",
        "inclDraw": "",
        "inclJudg": "",
        "inclReg": "",
        "inclAdmin": "",
        "sortField": "RANK",
        "sortState": "Desc",
        "viewMode": "",
        "searchInTrans": "N",
        "pageLanguage": "",
    }
    try:
        r = sess.post(URL, headers=headers, data=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            _log("[WARN] JSON 파싱 실패. 응답 앞 300자: " + r.text[:300])
            return None
    except Exception as e:
        _log(f"[ERROR] 페이지 요청 실패(page={current_page}): {e}")
        return None


# =========================
# 한 조건(엑셀 한 행) 처리
# =========================
def crawl_one_condition(
        task_id: int,
        no: str,
        ap: str,
        an: str,
        ipc: str,
) -> List[Dict[str, Any]]:
    """
    한 조건(NO, AP, AN, IPC)에 대해
    - expression 생성
    - 페이지 끝까지 조회
    - 모든 resultList item에 "kipris_no" 필드 추가 후 리스트 반환
    """
    expr = build_expression(ap, an, ipc)
    if not expr:
        _log(f"[SKIP][#{task_id}] expression 비어 있음 (NO={no}, AP={ap}, AN={an}, IPC={ipc})")
        return []

    sess = make_session()
    headers = dict(HEADERS_BASE)

    _log(
        f"[START][#{task_id}] NO={no}, AP='{ap}', AN='{an}', IPC='{ipc}', expr='{expr}'"
    )

    collected: List[Dict[str, Any]] = []
    page = 1

    while True:
        data = page_request(sess, headers, expr, page)
        if not data or "resultList" not in data:
            _log(f"[END  ][#{task_id}] page={page} resultList 없음/파싱 실패 → 종료")
            break

        lst = data.get("resultList") or []
        _log(f"[PAGE ][#{task_id}] page={page} 수신 건수={len(lst)}")

        if not lst:
            _log(f"[END  ][#{task_id}] 빈 배열 → 종료")
            break

        for item in lst:
            # 원본 item을 그대로 두고 싶으면 copy()해서 사용
            obj = dict(item)
            obj["kipris_no"] = _clean(no)  # 요구사항: 모든 JSON에 NO값 부여
            collected.append(obj)

        page += 1
        time.sleep(PAGE_SLEEP_SEC)

    _log(f"[DONE ][#{task_id}] 수집 건수={len(collected)}")
    return collected


# =========================
# 요청 목록 로드
# =========================
def load_requests_from_excel(path: str) -> List[Dict[str, str]]:
    """
    엑셀에서 NO, AP, AN, IPC 컬럼을 읽어
    [{ "NO": ..., "AP": ..., "AN": ..., "IPC": ... }, ...] 형태로 반환
    """
    try:
        # dtype=str 로 읽어서 숫자/선행 0 보존
        df = pd.read_excel(path, dtype=str)
    except Exception as e:
        _log(f"[ERROR] 엑셀 로드 실패: {e}")
        return []

    required_cols = ["NO", "AP", "AN", "IPC"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        _log(f"[ERROR] 필수 컬럼 누락: {missing}")
        return []

    requests_list: List[Dict[str, str]] = []

    for idx, row in df.iterrows():
        no = _clean(row.get("NO"))
        ap = _clean(row.get("AP"))
        an = _clean(row.get("AN"))
        ipc = _clean(row.get("IPC"))

        # expression 모두 빈값이면 의미 없으니 스킵
        if not (ap or an or ipc):
            _log(
                f"[WARN] row={idx+1} 에서 AP/AN/IPC 모두 비어 → 스킵 "
                f"(NO={no}, AP='{ap}', AN='{an}', IPC='{ipc}')"
            )
            continue

        requests_list.append({
            "NO": no,
            "AP": ap,
            "AN": an,
            "IPC": ipc,
        })

    _log(f"[INFO] 유효 요청 건수: {len(requests_list)}")
    return requests_list


# =========================
# 메인 실행
# =========================
def run():
    # 1) 요청 목록 로드
    req_list = load_requests_from_excel(EXCEL_PATH_IN)
    if not req_list:
        _log("[WARN] 실행할 요청이 없습니다.")
        return

    # 2) 멀티스레드 실행
    all_items: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = []
        for i, req in enumerate(req_list, start=1):
            futures.append(
                ex.submit(
                    crawl_one_condition,
                    i,
                    req["NO"],
                    req["AP"],
                    req["AN"],
                    req["IPC"],
                )
            )

        for fut in as_completed(futures):
            try:
                items = fut.result()
                if items:
                    all_items.extend(items)
            except Exception as e:
                _log(f"[ERROR] 작업 처리 중 예외: {e}")

    if not all_items:
        _log("[WARN] 어떤 요청에서도 결과가 없습니다.")
        return

    # 3) JSON 파일 저장 (result_json_YYYYMMDDHHMMSS.json)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    out_path = f"result_json_{ts}.json"

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        _log(f"[OK] 결과 JSON 저장 완료: {out_path} (총 {len(all_items)} 건)")
    except Exception as e:
        _log(f"[ERROR] 결과 JSON 저장 실패: {e}")


if __name__ == "__main__":
    run()
