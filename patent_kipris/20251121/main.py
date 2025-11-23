# -*- coding: utf-8 -*-
"""
KIPRIS 조건 엑셀 → JSON 매칭 스크립트

- 입력 엑셀: kipris_input_list.xlsx
  컬럼:
    "특허조건 NO"
    "출원인 (조건 : 완전히 일치)"
    "출원년도 (조건 : 완전히 일치)"
    "IPC (조건 : 해당 3자리 포함)"

- 입력 JSON: kipris_input_json_list.json
  (KIPRIS 검색 결과 리스트)

- 매칭 조건:
  1) JSON.AP == "출원인 (조건 : 완전히 일치)" (완전 일치, 공백 trim)
  2) JSON의 출원년도 == "출원년도 (조건 : 완전히 일치)"
     - 출원년도 추출 로직:
       AD, EDT, APD, AN 순서로 문자열에서 (19|20)YYYY 패턴 검색 후 첫 번째 매칭 사용
  3) "IPC (조건 : 해당 3자리 포함)" 값이 JSON IPC 계열 필드에 포함
     - IPC 검색 대상: IPC → IPCO → IPCS (순서)
     - 공백 제거, 대소문자 무시 후 substring 매칭

- 매칭 결과가 N개면, 해당 조건 row는 N행으로 풀림
  (각 행마다 "특허조건 NO" 등 조건 컬럼 값은 그대로 복제)

- 출력 엑셀: kipris_input_list_result.xlsx
  컬럼:
    "특허조건 NO"
    "출원인 (조건 : 완전히 일치)"
    "출원년도 (조건 : 완전히 일치)"
    "IPC (조건 : 해당 3자리 포함)"
    "출원인"
    "출원번호(일자)"
    "등록번호 법적상태 (등록/소멸-등록료불납/존속기간만료)"
    "발명자수"
    "심사청구항수"
    "피인용 (수)"
    "패밀리정보 (수)"
    "IPC (풀코드로 추출 요청)"
    "출원일자"
"""

import json
import re
from typing import Any, Dict, List, Tuple, DefaultDict
from collections import defaultdict

import pandas as pd

# =========================
# 경로 설정
# =========================
EXCEL_PATH_IN = "kipris_input_list.xlsx"
JSON_PATH = "kipris_input_json_list.json"
EXCEL_PATH_OUT = "kipris_input_list_result.xlsx"

# 조건 컬럼명 (엑셀 헤더와 정확히 동일하게!)
COND_NO_COL = "특허조건 NO"
COND_AP_COL = "출원인 (조건 : 완전히 일치)"
COND_YEAR_COL = "출원년도 (조건 : 완전히 일치)"
COND_IPC_COL = "IPC (조건 : 해당 3자리 포함)"

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
    IN: '이재연|한준석' -> '2'
        '홍길동' -> '1'
        빈값/None -> ""
    """
    s = _clean(in_field)
    if not s:
        return ""
    return str(s.count("|") + 1)


def parse_cited_count(bctc_field: Any) -> str:
    """
    BCTC가 숫자면 정수 문자열, 아니면 "".
    예: '0000' -> '0', '12' -> '12'
    """
    s = _clean(bctc_field).replace(",", "")
    return str(int(s)) if s.isdigit() else ""


def extract_year_from_item(item: Dict[str, Any]) -> str:
    """
    출원년도(문자열) 추출:
    - AD, EDT, APD, AN 순으로 (19|20)YYYY 패턴 검색
    - 없으면 ""
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
    - 우선순위: IPCO → IPC → IPCS
    """
    for key in ("IPCO", "IPC", "IPCS"):
        v = _clean(item.get(key))
        if v:
            return v
    return ""


def match_ipc(item: Dict[str, Any], cond_ipc: str) -> bool:
    """
    IPC 조건 매칭:
    - cond_ipc: 'F25' 같은 문자열 (3자리 포함 조건)
    - 대상: IPC / IPCO / IPCS 중 우선순위 매칭
    - 공백 제거, 대소문자 무시 후 substring 검색
    - cond_ipc 비어 있으면 True(필터 없음) 처리
    """
    cond = _clean(cond_ipc)
    if not cond:
        return True  # IPC 조건이 없으면 무조건 통과

    cond_norm = re.sub(r"\s+", "", cond).upper()

    src = (
            _clean(item.get("IPC"))
            or _clean(item.get("IPCO"))
            or _clean(item.get("IPCS"))
    )
    if not src:
        return False

    src_norm = re.sub(r"\s+", "", src).upper()
    return cond_norm in src_norm


def get_family_count(item: Dict[str, Any]) -> str:
    """
    패밀리정보(수) 추출.
    - JSON에 별도 패밀리 카운트 필드가 있으면 여기서 꺼내면 됨.
    - 현재 예시에는 명확한 필드가 없으므로, 일단 "" 반환.
    """
    # 예: 필드명이 'FAMC' 라면:
    # fam = _clean(item.get("FAMC"))
    # return fam if fam.isdigit() else ""
    return ""


# =========================
# JSON 로드 & 인덱스 구축
# =========================
def load_json_list(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON 최상위 구조는 리스트여야 합니다.")
    return data


def build_index_by_applicant_year(
        items: List[Dict[str, Any]]
) -> DefaultDict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    (출원인(AP), 출원년도) → item 리스트 인덱스
    """
    index: DefaultDict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    for it in items:
        ap = _clean(it.get("AP"))  # 출원인
        year = extract_year_from_item(it)
        if not ap or not year:
            continue
        index[(ap, year)].append(it)

    print(f"[INFO] JSON 레코드 수: {len(items)}")
    print(f"[INFO] (출원인, 출원년도) 인덱스 키 개수: {len(index)}")
    return index


# =========================
# 메인 처리
# =========================
def main():
    # 1) 엑셀 로드
    try:
        df_cond = pd.read_excel(EXCEL_PATH_IN)
    except Exception as e:
        print(f"[ERROR] 조건 엑셀 로드 실패: {e}")
        return

    # 필요한 컬럼 체크
    required_cols = [COND_NO_COL, COND_AP_COL, COND_YEAR_COL, COND_IPC_COL]
    for col in required_cols:
        if col not in df_cond.columns:
            print(f"[ERROR] 조건 엑셀에 '{col}' 컬럼이 없습니다.")
            return

    # 2) JSON 로드 및 인덱스 구축
    try:
        json_items = load_json_list(JSON_PATH)
        idx_by_ap_year = build_index_by_applicant_year(json_items)
    except Exception as e:
        print(f"[ERROR] JSON 로드/인덱스 실패: {e}")
        return

    # 3) 조건별 매칭 수행
    result_rows: List[Dict[str, str]] = []

    for i in range(len(df_cond)):
        cond_no = _clean(df_cond.at[i, COND_NO_COL])
        cond_ap = _clean(df_cond.at[i, COND_AP_COL])
        cond_year = _clean(df_cond.at[i, COND_YEAR_COL])
        cond_ipc = _clean(df_cond.at[i, COND_IPC_COL])

        if not cond_ap or not cond_year:
            print(f"[WARN] row={i+1} 조건 불충분 (출원인/출원년도 없음) → 스킵")
            continue

        key = (cond_ap, cond_year)
        candidates = idx_by_ap_year.get(key, [])

        print(
            f"[COND] row={i+1}, NO={cond_no}, 출원인='{cond_ap}', 출원년도='{cond_year}', IPC조건='{cond_ipc}', "
            f"1차 후보 수={len(candidates)}"
        )

        hit_count = 0

        for item in candidates:
            if not match_ipc(item, cond_ipc):
                continue

            # 매칭 성공
            hit_count += 1

            ap = _clean(item.get("AP"))
            an = _clean(item.get("AN"))
            lsto = _clean(item.get("LSTO"))
            in_cnt = parse_inventor_count(item.get("IN"))
            bic = _clean(item.get("BIC"))
            bctc = parse_cited_count(item.get("BCTC"))
            fam = get_family_count(item)
            full_ipc = get_full_ipc(item)
            ad = _clean(item.get("AD"))  # 출원일자

            row_out = {
                COND_NO_COL: cond_no,
                COND_AP_COL: cond_ap,
                COND_YEAR_COL: cond_year,
                COND_IPC_COL: cond_ipc,
                "출원인": ap,
                "출원번호(일자)": an,
                "등록번호 법적상태 (등록/소멸-등록료불납/존속기간만료)": lsto,
                "발명자수": in_cnt,
                "심사청구항수": bic,
                "피인용 (수)": bctc,
                "패밀리정보 (수)": fam,
                "IPC (풀코드로 추출 요청)": full_ipc,
                "출원일자": ad,
            }
            result_rows.append(row_out)

        if hit_count == 0:
            print(f"[MISS] row={i+1}, 조건에 맞는 특허 없음")
            # 매칭 0개일 때도 결과 엑셀에서 보고 싶으면 아래 주석 해제
            # result_rows.append({
            #     COND_NO_COL: cond_no,
            #     COND_AP_COL: cond_ap,
            #     COND_YEAR_COL: cond_year,
            #     COND_IPC_COL: cond_ipc,
            #     "출원인": "",
            #     "출원번호(일자)": "",
            #     "등록번호 법적상태 (등록/소멸-등록료불납/존속기간만료)": "",
            #     "발명자수": "",
            #     "심사청구항수": "",
            #     "피인용 (수)": "",
            #     "패밀리정보 (수)": "",
            #     "IPC (풀코드로 추출 요청)": "",
            #     "출원일자": "",
            # })

        else:
            print(f"[HIT] row={i+1}, 매칭 건수={hit_count}")

    # 4) 결과 저장
    if not result_rows:
        print("[WARN] 매칭된 결과가 없습니다. 엑셀은 생성하지 않습니다.")
        return

    df_out = pd.DataFrame(result_rows)

    # 컬럼 순서 명시적으로 지정
    col_order = [
        COND_NO_COL,
        COND_AP_COL,
        COND_YEAR_COL,
        COND_IPC_COL,
        "출원인",
        "출원번호(일자)",
        "등록번호 법적상태 (등록/소멸-등록료불납/존속기간만료)",
        "발명자수",
        "심사청구항수",
        "피인용 (수)",
        "패밀리정보 (수)",
        "IPC (풀코드로 추출 요청)",
        "출원일자",
    ]
    # 혹시 누락된 컬럼이 있으면 자동 추가
    for c in col_order:
        if c not in df_out.columns:
            df_out[c] = ""

    df_out = df_out[col_order]

    try:
        df_out.to_excel(EXCEL_PATH_OUT, index=False)
        print(f"[OK] 결과 저장 완료: {EXCEL_PATH_OUT} (rows={len(df_out)})")
    except Exception as e:
        print(f"[ERROR] 결과 엑셀 저장 실패: {e}")


if __name__ == "__main__":
    main()
