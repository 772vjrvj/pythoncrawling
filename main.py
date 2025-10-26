# -*- coding: utf-8 -*-
"""
KIPRIS /kpat/resulta.do 멀티쓰레드 수집기
- 엑셀(data_new_20251022_1.xlsx) AP/AN/IPC/TRH 행 단위로 병렬 처리
- 각 행은 currentPage=1부터 증가하며 resultList 없을 때까지 순차 페이지네이션
- numPerPage=90
- 모든 resultList 합집합을 DOCID 기준 중복 제거 후 data_result_list.json 저장
"""
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# =========================
# 설정
# =========================
EXCEL_PATH = "data_new_20251022_2.xlsx"
URL = "https://www.kipris.or.kr/kpat/resulta.do"
NUM_PER_PAGE = 90
REQUEST_TIMEOUT = 30  # sec
PAGE_SLEEP_SEC = 0.3  # 페이지 사이 소량 대기(서버 부담/차단 완화)
MAX_WORKERS = 6       # 동시 실행 스레드(조건 병렬 개수)

# ★ 최신 세션 쿠키로 교체해서 사용하세요.
COOKIE = (
    "JSESSIONID=MOw4bqzTtHo3I6rA3z5UIZHbsx1MEUN8fxh4KRaUVLlZOPkwlp9yFdZ13UEiD1bi.amV1c19kb21haW4va3BhdDE=; "
    "_ga=GA1.1.1858042139.1761006044; "
    "_ga_6RVR9V6306=GS2.1.s1761216402$o7$g1$t1761216823$j60$l0$h0; "
    "_ga_XYF3QRKKDC=GS2.1.s1761216823$o14$g0$t1761216823$j60$l0$h0; "
    "_ga_4R5CJZBQXD=GS2.1.s1761216823$o14$g0$t1761216823$j60$l0$h0"
)

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
    # cookie는 스레드별 세션에서 공통 사용. 필요시 갱신 가능.
    "cookie": COOKIE,
}

_print_lock = threading.Lock()

def _log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)

# =========================
# 유틸
# =========================
def _clean(v: Any) -> str:
    if pd.isna(v):
        return ""
    return str(v).strip()

def build_expression(ap: str, an: str, ipc: str, trh: str) -> str:
    parts = []
    if an:  parts.append(f"AN=[{an}]")
    if ipc: parts.append(f"IPC=[{ipc}]")
    if ap:  parts.append(f"AP=[{ap}]")
    if trh: parts.append(f"TRH=[{trh}]")
    return "*".join(parts)

def make_session() -> requests.Session:
    sess = requests.Session()
    retry = Retry(
        total=5, read=5, connect=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess

def page_request(sess: requests.Session, headers: Dict[str, str], expression: str, current_page: int) -> Optional[Dict[str, Any]]:
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
        _log(f"[ERROR] 페이지 요청 실패(page={current_page}): {str(e)}")
        return None

def crawl_condition(task_id: int, ap: str, an: str, ipc: str, trh: str) -> Tuple[int, str, List[Dict[str, Any]]]:
    """
    한 조건(엑셀 한 행) 페이지네이션 수집 (순차)
    반환: (task_id, expression, results)
    """
    expr = build_expression(ap, an, ipc, trh)
    if not expr:
        _log(f"[SKIP][#{task_id}] 조건 비어 생략")
        return task_id, expr, []

    sess = make_session()
    headers = dict(HEADERS_BASE)  # 필요 시 스레드별로 쿠키 갱신 가능

    _log(f"[START][#{task_id}] expr='{expr}'")
    collected: List[Dict[str, Any]] = []
    page = 1
    while True:
        data = page_request(sess, headers, expr, page)
        if not data or "resultList" not in data:
            _log(f"[END  ][#{task_id}] page={page} resultList 없음/파싱 실패 → 종료")
            break
        lst = data.get("resultList") or []
        _log(f"[PAGE ][#{task_id}] page={page} 수신={len(lst)}")
        if not lst:
            _log(f"[END  ][#{task_id}] 빈 배열 → 종료")
            break
        collected.extend(lst)
        page += 1
        time.sleep(PAGE_SLEEP_SEC)

    _log(f"[DONE ][#{task_id}] 총 수집={len(collected)}")
    return task_id, expr, collected

def dedupe_by_docid(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        docid = str(it.get("DOCID", "")).strip()
        if docid and docid in seen:
            continue
        if docid:
            seen.add(docid)
        out.append(it)
    return out

def main():
    # 엑셀 로드
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        _log(f"[ERROR] 엑셀 읽기 실패: {str(e)}")
        return

    required = ["AP", "AN", "IPC", "TRH"]
    miss = [c for c in required if c not in df.columns]
    if miss:
        _log(f"[ERROR] 필수 컬럼 누락: {miss}")
        return

    # 작업 목록 준비
    tasks = []
    for i, row in df.iterrows():
        ap  = _clean(row.get("AP"))
        an  = _clean(row.get("AN"))
        ipc = _clean(row.get("IPC"))
        trh = _clean(row.get("TRH"))
        tasks.append( (i+1, ap, an, ipc, trh) )

    _log(f"[INFO] 총 작업 수: {len(tasks)}, MAX_WORKERS={MAX_WORKERS}")

    all_results: List[Dict[str, Any]] = []

    # 멀티쓰레드 실행 (조건 병렬)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(crawl_condition, *t) for t in tasks]
        for fut in as_completed(futures):
            try:
                task_id, expr, results = fut.result()
                _log(f"[MERGE][#{task_id}] expr='{expr}' 결과 병합 {len(results)}건")
                all_results.extend(results)
            except Exception as e:
                _log(f"[ERROR] 작업 처리 중 예외: {str(e)}")

    _log(f"[INFO] 전체 원본 합계: {len(all_results)}건")
    deduped = dedupe_by_docid(all_results)
    _log(f"[INFO] DOCID 중복 제거 후: {len(deduped)}건")

    # 저장
    out_path = "data_result_list.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(deduped, f, ensure_ascii=False, indent=2)
        _log(f"[OK] 저장 완료: {out_path}")
    except Exception as e:
        _log(f"[ERROR] 저장 실패: {str(e)}")

if __name__ == "__main__":
    main()
