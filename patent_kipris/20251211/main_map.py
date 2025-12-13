# -*- coding: utf-8 -*-
"""
KIPRIS 결과 JSON 필터링 후 엑셀로 내보내기

1) 입력:
   - 엑셀: kipris_request_list.xlsx
       컬럼(예상):
         "NO"
         "AP"
         "AN"
         "IPC"
         (선택) "발명자수"  ← 있으면 발명자 수까지 조건으로 비교
   - JSON : result_json_20251211021152.json
       배열 형태, 각 item 에 "kipris_no" 필드가 있음

2) 처리:
   - 엑셀 각 row 에 대해:
       a) NO 가 같은 kipris_no 를 가진 JSON item 리스트를 찾는다.
       b) 그 중에서
            - JSON 의 IPC(풀코드)가 엑셀 IPC 로 시작하는지 체크
            - (엑셀에 "발명자수" 컬럼이 있을 경우)
              JSON의 발명자수와 엑셀 발명자수가 같은지 체크
       c) 조건에 맞는 item들만 결과 배열에 추가
         (결과 row 에는 NO/AP/AN/IPC + JSON 추출 필드들을 채워 넣음)

3) 출력:
   - kipris_match_result.xlsx
   - 컬럼:
       "NO"
       "AP"
       "AN"
       "IPC"
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
       "TRH 최종권리자"
"""

import json
import threading
from typing import Any, Dict, List
import re

import pandas as pd

# =========================
# 설정
# =========================
EXCEL_PATH_IN = "kipris_request_list.xlsx"
JSON_PATH_IN = "result_json_20251211021152.json"
EXCEL_PATH_OUT = "kipris_match_result.xlsx"

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
    """
    JSON 의 IN 필드 기준으로 발명자 수 계산
    예: "홍길동|김철수|이영희" -> 3
    """
    s = _clean(in_field)
    if not s:
        return ""
    return str(s.count("|") + 1)


def parse_cited_count(bctc_field: Any) -> str:
    """
    BCTC: 피인용 수 (문자열 숫자, 콤마 제거)
    """
    s = _clean(bctc_field).replace(",", "")
    return str(int(s)) if s.isdigit() else ""


def get_family_count(item: Dict[str, Any]) -> str:
    """
    패밀리정보(수) 추출.
    실제 필드명이 확인되면 여기서 꺼내 쓰면 됨.
    일단은 빈 값 리턴.
    """
    # fam = _clean(item.get("FAMC"))
    # return fam if fam.isdigit() else ""
    return ""


def get_full_ipc(item: Dict[str, Any]) -> str:
    """
    IPC 풀코드: IPC 필드 그대로 사용
    """
    return _clean(item.get("IPC"))


def ipc_startswith(ipc_full: str, ipc_prefix: str) -> bool:
    """
    IPC가 엑셀 IPC로 시작하는지 판단
    - 공백 제거 후 대소문자 무시
    - ipc_prefix 가 비어있으면 True
    """
    prefix = _clean(ipc_prefix)
    if not prefix:
        return True

    prefix_norm = re.sub(r"\s+", "", prefix).upper()
    full_norm = re.sub(r"\s+", "", _clean(ipc_full)).upper()

    return full_norm.startswith(prefix_norm)


# =========================
# 메인 처리
# =========================
def run():
    # 1) 엑셀 로드
    try:
        df = pd.read_excel(EXCEL_PATH_IN, dtype=str)
    except Exception as e:
        _log(f"[ERROR] 엑셀 로드 실패: {e}")
        return

    required_cols = ["NO", "AP", "AN", "IPC"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        _log(f"[ERROR] 필수 컬럼 누락: {missing}")
        return

    has_inventor_col = "발명자수" in df.columns
    if has_inventor_col:
        _log("[INFO] 엑셀에 '발명자수' 컬럼이 있어, 발명자 수도 조건으로 사용합니다.")
    else:
        _log("[INFO] 엑셀에 '발명자수' 컬럼이 없어, IPC 조건만 사용합니다.")

    # 2) JSON 로드
    try:
        with open(JSON_PATH_IN, "r", encoding="utf-8") as f:
            json_list: List[Dict[str, Any]] = json.load(f)
    except Exception as e:
        _log(f"[ERROR] JSON 로드 실패: {e}")
        return

    _log(f"[INFO] JSON 전체 건수: {len(json_list)}")

    # 3) kipris_no 기준으로 인덱스 만들기
    by_kipris_no: Dict[str, List[Dict[str, Any]]] = {}
    for item in json_list:
        no = _clean(item.get("kipris_no"))
        if not no:
            continue
        by_kipris_no.setdefault(no, []).append(item)

    _log(f"[INFO] kipris_no 그룹 수: {len(by_kipris_no)}")

    # 4) 엑셀 각 행마다 매칭 및 필터링
    results: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        no = _clean(row.get("NO"))
        ap_cond = _clean(row.get("AP"))
        an_cond = _clean(row.get("AN"))
        ipc_cond = _clean(row.get("IPC"))
        inventor_cond = _clean(row.get("발명자수")) if has_inventor_col else ""

        if not no:
            _log(f"[WARN] row={idx+1} NO 비어 있음 → 스킵")
            continue

        candidates = by_kipris_no.get(no, [])
        if not candidates:
            _log(f"[INFO] row={idx+1} NO={no} 에 대한 JSON 결과 없음")
            continue

        _log(
            f"[ROW ][{idx+1}] NO={no}, AP='{ap_cond}', AN='{an_cond}', IPC='{ipc_cond}', "
            f"JSON 후보={len(candidates)}"
        )

        for item in candidates:
            full_ipc = get_full_ipc(item)
            if not ipc_startswith(full_ipc, ipc_cond):
                continue

            inv_cnt = parse_inventor_count(item.get("IN"))

            # 엑셀에 발명자수 조건이 있을 때만 비교
            if inventor_cond:
                if inv_cnt != inventor_cond:
                    continue

            cited_cnt = parse_cited_count(item.get("BCTC"))
            fam_cnt = get_family_count(item)

            row_out: Dict[str, Any] = {
                # 엑셀 조건 컬럼
                "NO": no,
                "AP": ap_cond,
                "AN": an_cond,
                "IPC": ipc_cond,
                # 결과 컬럼 (JSON 기반)
                "출원인": _clean(item.get("AP")),
                "출원번호(일자)": _clean(item.get("AN")),
                "등록번호": _clean(item.get("GN")),
                "법적상태 (등록/소멸-등록료불납/존속기간만료)": _clean(item.get("LSTO")),
                "발명자수": inv_cnt,
                "심사청구항수": _clean(item.get("BIC")),
                "피인용 (수)": cited_cnt,
                "패밀리정보 (수)": fam_cnt,
                "IPC (풀코드로 추출 요청)": full_ipc,
                "출원일자": _clean(item.get("AD")),
                "TRH 최종권리자": _clean(item.get("TRH")),
            }

            results.append(row_out)

    if not results:
        _log("[WARN] 조건에 맞는 결과가 하나도 없습니다.")
        return

    # 5) 엑셀로 저장
    df_out = pd.DataFrame(results)

    col_order = [
        "NO",
        "AP",
        "AN",
        "IPC",
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
        "TRH 최종권리자",
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
    run()
