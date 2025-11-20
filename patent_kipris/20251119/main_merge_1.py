# -*- coding: utf-8 -*-
"""
data_new_20251109_3_out.xlsx 보강 스크립트 (모든 값 문자열 처리)

- data_new_20251109_3_out.xlsx 읽기
  - 각 행의 "등록번호2" 사용
- data_result_list_2.json 로드
  - GN == 등록번호2 인 객체를 찾아 매핑
- 아래 컬럼(전부 문자열) 채움:
  출원인
  최종권리자
  출원년도
  심사청구항수
  피인용(수)
  출원번호(일자)
  발명자수
  패밀리정보(수)
  법적상태(등록/소멸-등록료불납/존속기간만료)
  IPC코드
  권리만료일  <-- === 신규 ===

결과: data_new_20251109_3_filled.xlsx
"""

import json
import re
from typing import Any, Dict, List
from datetime import datetime, date  # === 신규 ===
import pandas as pd

EXCEL_PATH_IN = "data_new_20251109_3_out.xlsx"
JSON_PATH = "data_result_list_2.json"
EXCEL_PATH_OUT = "data_new_20251109_3_filled.xlsx"


# =========================
# 헬퍼 (모두 문자열 반환)
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
    """
    s = _clean(bctc_field).replace(",", "")
    return str(int(s)) if s.isdigit() else ""


def normalize_ipc_full(ipc_field: Any) -> str:
    """
    IPC를 문자열로 정규화.
    - 리스트/튜플이면 각 요소 문자열화 후 ' | ' 조인
    - 그 외는 문자열 반환
    """
    if ipc_field is None:
        return ""
    if isinstance(ipc_field, (list, tuple)):
        parts: List[str] = []
        for x in ipc_field:
            xs = _clean(x)
            if xs:
                parts.append(xs)
        return " | ".join(parts)
    return _clean(ipc_field)


def extract_year_from_fields(item: Dict[str, Any]) -> str:
    """
    출원년도(문자열) 추출:
    - APD, AD 순으로 검사해 YYYY 패턴 찾기
    - 없으면 AN 에서도 YYYY 패턴 검색
    - 없으면 "" (전부 문자열 반환)
    """
    cand = None

    for key in ("APD", "AD"):
        v = item.get(key)
        if v:
            cand = _clean(v)
            break

    if not cand:
        cand = _clean(item.get("AN"))

    if not cand:
        return ""

    m = re.search(r"(19|20)\d{2}", cand)
    return m.group(0) if m else ""


# === 신규: 권리만료일 계산 ===
def compute_expiry_date(item: Dict[str, Any]) -> str:
    """
    권리만료일(YYYY-MM-DD) 계산:
    - AD(출원일, 'YYYY-MM-DD') 기준 + 20년
    - AD 없으면 EDT('YYYY.MM.DD') 시도
    - 둘 다 없으면 ""
    """
    ad = _clean(item.get("AD"))
    base_date: date | None = None

    # 1) AD 우선
    if ad:
        try:
            base_date = datetime.strptime(ad, "%Y-%m-%d").date()
        except Exception:
            base_date = None

    # 2) AD가 없거나 파싱 실패 → EDT 시도
    if base_date is None:
        edt = _clean(item.get("EDT"))
        if edt:
            # 'YYYY.MM.DD' 또는 섞여있는 포맷 대비
            edt_norm = edt.replace(".", "-")
            try:
                base_date = datetime.strptime(edt_norm, "%Y-%m-%d").date()
            except Exception:
                base_date = None

    if base_date is None:
        return ""

    # 3) 20년 더하기 (윤년 예외 처리)
    try:
        expiry = base_date.replace(year=base_date.year + 20)
    except ValueError:
        # 2/29 같은 경우 -> 2/28로 보정
        expiry = base_date.replace(month=2, day=28, year=base_date.year + 20)

    return expiry.strftime("%Y-%m-%d")


# =========================
# JSON 인덱스 (GN → item)
# =========================
def load_json_index(path: str) -> Dict[str, Dict[str, Any]]:
    """
    GN 기준 인덱스 구성: { GN(정제) : item }
    동일 GN 여러 개면 첫 번째만 사용.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON 최상위 구조는 리스트여야 합니다.")

    index: Dict[str, Dict[str, Any]] = {}
    for it in data:
        gn = _clean(it.get("GN"))
        if not gn:
            continue
        gn_norm = gn.replace("&nbsp;", "").replace(" ", "")
        if gn_norm and gn_norm not in index:
            index[gn_norm] = it

    print(f"[INFO] JSON 인덱스 GN 개수: {len(index)}")
    return index


# =========================
# 메인
# =========================
def main():
    # 1) 엑셀 로드
    try:
        df = pd.read_excel(EXCEL_PATH_IN)
    except Exception as e:
        print(f"[ERROR] 엑셀 로드 실패: {e}")
        return

    if "등록번호2" not in df.columns:
        print('[ERROR] "등록번호2" 컬럼이 없습니다. 먼저 매칭 스크립트를 수행하세요.')
        return

    # 2) JSON 인덱스 로드
    try:
        gn_index = load_json_index(JSON_PATH)
    except Exception as e:
        print(f"[ERROR] JSON 로드/인덱스 실패: {e}")
        return

    # 3) 결과 컬럼 준비 (문자열용)
    target_cols = [
        "출원인",
        "최종권리자",
        "출원년도",
        "심사청구항수",
        "피인용(수)",
        "출원번호(일자)",
        "발명자수",
        "패밀리정보(수)",
        "법적상태(등록/소멸-등록료불납/존속기간만료)",
        "IPC코드",
        "권리만료일",  # === 신규 ===
    ]
    for col in target_cols:
        if col not in df.columns:
            df[col] = ""
        else:
            # 기존 값이 있더라도 문자열화
            df[col] = df[col].apply(_clean)

    # 4) 각 행 매핑
    for idx in range(len(df)):
        reg2 = _clean(df.at[idx, "등록번호2"])
        if not reg2:
            continue

        reg2_norm = reg2.replace("&nbsp;", "").replace(" ", "")

        item = gn_index.get(reg2_norm)
        if not item:
            print(f"[MISS] row={idx+1}, 등록번호2={reg2_norm} → 매칭 없음")
            continue

        ap = _clean(item.get("AP"))                    # 출원인
        trh = _clean(item.get("TRH"))                  # 최종권리자
        year = _clean(extract_year_from_fields(item))  # 출원년도
        bic = _clean(item.get("BIC"))                  # 심사청구항수
        bctc = parse_cited_count(item.get("BCTC"))     # 피인용(수)
        an = _clean(item.get("AN"))                    # 출원번호(일자)
        in_cnt = parse_inventor_count(item.get("IN"))  # 발명자수
        fam = ""                                       # 패밀리정보(수) (현재 규칙상 빈값)
        lsto = _clean(item.get("LSTO"))                # 법적상태
        ipc_full = normalize_ipc_full(item.get("IPC")) # IPC코드

        # === 신규: 권리만료일 (존속기간만료인 경우에만 계산) ===
        expiry_date = ""
        if "존속기간만료" in lsto:
            expiry_date = compute_expiry_date(item)

        df.at[idx, "출원인"] = ap
        df.at[idx, "최종권리자"] = trh
        df.at[idx, "출원년도"] = year
        df.at[idx, "심사청구항수"] = bic
        df.at[idx, "피인용(수)"] = bctc
        df.at[idx, "출원번호(일자)"] = an
        df.at[idx, "발명자수"] = in_cnt
        df.at[idx, "패밀리정보(수)"] = fam
        df.at[idx, "법적상태(등록/소멸-등록료불납/존속기간만료)"] = lsto
        df.at[idx, "IPC코드"] = ipc_full
        df.at[idx, "권리만료일"] = expiry_date  # === 신규 ===

        print(f"[MATCH] row={idx+1}, 등록번호2={reg2_norm} → GN 매핑 완료")

    # 5) 저장 (엑셀에서도 전부 문자열로 보이도록 object 유지)
    try:
        df.to_excel(EXCEL_PATH_OUT, index=False)
        print(f"[OK] 저장 완료: {EXCEL_PATH_OUT} (rows={len(df)})")
    except Exception as e:
        print(f"[ERROR] 엑셀 저장 실패: {e}")


if __name__ == "__main__":
    main()
