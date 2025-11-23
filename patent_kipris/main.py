# -*- coding: utf-8 -*-
"""
KIPRIS /kpat/resulta.do 조건 검색기

- 입력 엑셀: kipris_input_list.xlsx
  컬럼:
    "특허조건 NO."                (또는 "특허조건 NO")
    "출원인 (조건 : 완전히 일치)"
    "출원년도 (조건 : 완전히 일치)"
    "IPC (조건 : 해당 3자리 포함)"

- 동작:
  각 행에 대해
    1) AP, IPC 로 KIPRIS 검색 (expression)
    2) 결과 리스트에서
       - 출원인(AP) == 조건 출원인
       - 출원년도 == 조건 출원년도 (AD/EDT/APD/AN 에서 연도 추출)
       - IPC 문자열에 조건 IPC(3자리)가 포함
       인 것만 필터링

- 출력 엑셀: kipris_input_list_result.xlsx
  컬럼:
    "특허조건 NO."
    "출원인 (조건 : 완전히 일치)"
    "출원년도 (조건 : 완전히 일치)"
    "IPC (조건 : 해당 3자리 포함)"
    "출원인"
    "출원번호(일자)"
    "등록번호"
    "법적상태 (등록/소멸-등록료불납/존속기간만료)"
    "발명자수"
    "심사청구항수"
    "피인용 (수)"
    "패밀리정보 (수)"
    "IPC (풀코드로 추출 요청)"
    "출원일자"
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
import re

# =========================
# 설정
# =========================
EXCEL_PATH_IN = "kipris_input_list.xlsx"
EXCEL_PATH_OUT = "kipris_input_list_result.xlsx"

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
}

# 엑셀 조건 컬럼명
COND_NO_COL_1 = "특허조건 NO."
COND_NO_COL_2 = "특허조건 NO"
COND_AP_COL = "출원인 (조건 : 완전히 일치)"
COND_YEAR_COL = "출원년도 (조건 : 완전히 일치)"
COND_IPC_COL = "IPC (조건 : 해당 3자리 포함)"

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


def parse_inventor_count(in_field: Any) -> str:
    s = _clean(in_field)
    if not s:
        return ""
    return str(s.count("|") + 1)


def parse_cited_count(bctc_field: Any) -> str:
    s = _clean(bctc_field).replace(",", "")
    return str(int(s)) if s.isdigit() else ""


def extract_year_from_item(item: Dict[str, Any]) -> str:
    """
    출원년도 추출:
    AD, EDT, APD, AN 순으로 (19|20)YYYY 패턴 검색
    """
    for key in ("AD", "EDT", "APD", "AN"):
        v = _clean(item.get(key))
        if not v:
            continue
        m = re.search(r"(19|20)\d{2}", v)
        if m:
            return m.group(0)
    return ""


def get_full_ipc(item: Dict[str, Any]) -> str:
    """
    IPC 풀코드:
    - IPC 필드만 사용
    """
    return _clean(item.get("IPC"))


def match_ipc(item: Dict[str, Any], cond_ipc: str) -> bool:
    """
    IPC 조건 매칭:
    - cond_ipc: 'F25' 같은 문자열 (3자리 포함 조건)
    - 대상: IPC 문자열만 사용
    - 공백 제거, 대소문자 무시 후 substring 검색
    - cond_ipc 비어 있으면 True
    """
    cond = _clean(cond_ipc)
    if not cond:
        return True

    cond_norm = re.sub(r"\s+", "", cond).upper()

    src = _clean(item.get("IPC"))   # IPC만 사용
    if not src:
        return False

    src_norm = re.sub(r"\s+", "", src).upper()
    return cond_norm in src_norm


def get_family_count(item: Dict[str, Any]) -> str:
    """
    패밀리정보(수) 추출.
    실제 필드명이 파악되면 여기서 꺼내면 됨.
    현재는 빈값 반환.
    """
    # 예시:
    # fam = _clean(item.get("FAMC"))
    # return fam if fam.isdigit() else ""
    return ""


# =========================
# HTTP 세션 / 요청
# =========================
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


def build_expression(ap: str, ipc: str) -> str:
    """
    검색 expression 구성
    - AP: 출원인
    - IPC: IPC 조건 (3자리 포함이지만 여기선 그대로 사용)
    """
    parts = []
    if ap:
        parts.append(f"AP=[{ap}]")
    if ipc:
        parts.append(f"IPC=[{ipc}]")
    return "*".join(parts)


def page_request(
        sess: requests.Session,
        headers: Dict[str, str],
        expression: str,
        current_page: int,
) -> Optional[Dict[str, Any]]:
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


# =========================
# 한 조건(엑셀 한 행) 처리
# =========================
def crawl_condition(
        task_id: int,
        cond_no: str,
        cond_ap: str,
        cond_year: str,
        cond_ipc: str,
) -> List[Dict[str, str]]:
    """
    한 조건에 대해 KIPRIS 검색하고 필터링 후
    결과 행(엑셀용 dict) 리스트 반환
    """
    expr = build_expression(cond_ap, cond_ipc)
    if not expr:
        _log(f"[SKIP][#{task_id}] expr 비어 생략 (출원인/IPC 없음)")
        return []

    sess = make_session()
    headers = dict(HEADERS_BASE)

    _log(
        f"[START][#{task_id}] NO={cond_no}, 출원인='{cond_ap}', 출원년도='{cond_year}', "
        f"IPC조건='{cond_ipc}', expr='{expr}'"
    )

    results: List[Dict[str, str]] = []
    seen_docid = set()

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

        for item in lst:
            # 1차: 출원인 완전 일치
            ap = _clean(item.get("AP"))
            if ap != cond_ap:
                continue

            # 2차: 출원년도 일치
            year = extract_year_from_item(item)
            if cond_year and year != cond_year:
                continue

            # 3차: IPC 3자리 포함 조건
            if not match_ipc(item, cond_ipc):
                continue

            # DOCID 중복 방지 (같은 조건 내)
            docid = _clean(item.get("DOCID"))
            if docid and docid in seen_docid:
                continue
            if docid:
                seen_docid.add(docid)

            an = _clean(item.get("AN"))          # 출원번호(일자)
            gn = _clean(item.get("GN"))          # 등록번호 (GN 사용)
            lsto = _clean(item.get("LSTO"))      # 법적상태
            in_cnt = parse_inventor_count(item.get("IN"))
            bic = _clean(item.get("BIC"))        # 심사청구항수
            bctc = parse_cited_count(item.get("BCTC"))
            fam = get_family_count(item)
            full_ipc = get_full_ipc(item)
            ad = _clean(item.get("AD"))          # 출원일자

            row_out: Dict[str, str] = {
                # 조건 컬럼
                "특허조건 NO.": cond_no,
                "출원인 (조건 : 완전히 일치)": cond_ap,
                "출원년도 (조건 : 완전히 일치)": cond_year,
                "IPC (조건 : 해당 3자리 포함)": cond_ipc,
                # 결과 컬럼
                "출원인": ap,
                "출원번호(일자)": an,
                "등록번호": gn,
                "법적상태 (등록/소멸-등록료불납/존속기간만료)": lsto,
                "발명자수": in_cnt,
                "심사청구항수": bic,
                "피인용 (수)": bctc,
                "패밀리정보 (수)": fam,
                "IPC (풀코드로 추출 요청)": full_ipc,
                "출원일자": ad,
            }
            results.append(row_out)

        page += 1
        time.sleep(PAGE_SLEEP_SEC)

    _log(f"[DONE ][#{task_id}] 조건 매칭 결과 수={len(results)}")
    return results


# =========================
# 메인
# =========================
def main():
    # 1) 엑셀 로드
    try:
        df = pd.read_excel(EXCEL_PATH_IN)
    except Exception as e:
        _log(f"[ERROR] 조건 엑셀 로드 실패: {e}")
        return

    # 특허조건 NO 컬럼명 결정
    if COND_NO_COL_1 in df.columns:
        cond_no_col = COND_NO_COL_1
    elif COND_NO_COL_2 in df.columns:
        cond_no_col = COND_NO_COL_2
    else:
        _log(f"[ERROR] '{COND_NO_COL_1}' 또는 '{COND_NO_COL_2}' 컬럼이 없습니다.")
        return

    required_cols = [cond_no_col, COND_AP_COL, COND_YEAR_COL, COND_IPC_COL]
    miss = [c for c in required_cols if c not in df.columns]
    if miss:
        _log(f"[ERROR] 필수 컬럼 누락: {miss}")
        return

    # 2) 작업 목록 구성
    tasks = []
    for idx, row in df.iterrows():
        cond_no = _clean(row.get(cond_no_col))
        cond_ap = _clean(row.get(COND_AP_COL))
        cond_year = _clean(row.get(COND_YEAR_COL))
        cond_ipc = _clean(row.get(COND_IPC_COL))

        if not cond_ap or not cond_year:
            _log(
                f"[WARN] row={idx+1} 출원인/출원년도 조건 부족 → 스킵 "
                f"(NO={cond_no}, 출원인='{cond_ap}', 출원년도='{cond_year}')"
            )
            continue

        tasks.append((idx + 1, cond_no, cond_ap, cond_year, cond_ipc))

    _log(f"[INFO] 유효 조건 작업 수: {len(tasks)}, MAX_WORKERS={MAX_WORKERS}")

    if not tasks:
        _log("[WARN] 실행할 조건이 없습니다.")
        return

    # 3) 멀티쓰레드 실행
    all_rows: List[Dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [
            ex.submit(crawl_condition, task_id, cond_no, cond_ap, cond_year, cond_ipc)
            for (task_id, cond_no, cond_ap, cond_year, cond_ipc) in tasks
        ]

        for fut in as_completed(futures):
            try:
                rows = fut.result()
                if rows:
                    all_rows.extend(rows)
            except Exception as e:
                _log(f"[ERROR] 작업 처리 중 예외: {e}")

    if not all_rows:
        _log("[WARN] 어떤 조건에서도 매칭된 결과가 없습니다.")
        return

    # 4) 결과 엑셀 저장
    df_out = pd.DataFrame(all_rows)

    col_order = [
        "특허조건 NO.",
        "출원인 (조건 : 완전히 일치)",
        "출원년도 (조건 : 완전히 일치)",
        "IPC (조건 : 해당 3자리 포함)",
        "출원인",
        "출원번호(일자)",
        "등록번호",
        "법적상태 (등록/소멸-등록료불납/존속기간만료)",
        "발명자수",
        "심사청구항수",
        "피인용 (수)",
        "패밀리정보 (수)",
        "IPC (풀코드로 추출 요청)",
        "출원일자",
    ]

    for c in col_order:
        if c not in df_out.columns:
            df_out[c] = ""

    df_out = df_out[col_order]

    try:
        df_out.to_excel(EXCEL_PATH_OUT, index=False)
        _log(f"[OK] 결과 저장 완료: {EXCEL_PATH_OUT} (rows={len(df_out)})")
    except Exception as e:
        _log(f"[ERROR] 결과 엑셀 저장 실패: {e}")


if __name__ == "__main__":
    main()
