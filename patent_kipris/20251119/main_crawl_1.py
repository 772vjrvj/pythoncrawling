# -*- coding: utf-8 -*-
"""
data_new_20251109_3_out.xlsx 보강 스크립트 (모든 값 문자열 처리)

- data_new_20251109_3_out.xlsx 읽기
  - 각 행의 "등록번호2" 사용 (예: 10-0506897)
- data_result_list_2.json 로드
  - JSON의 GN / GNS 안에 있는 9자리 코어번호(예: 100506897)와
    엑셀의 등록번호 코어(10-0506897 -> 100506897)를 매칭
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
  권리만료일

결과: data_new_20251109_3_filled.xlsx
"""

import json
import re
from typing import Any, Dict, List
from datetime import datetime, date  # === 신규 ===
import pandas as pd

EXCEL_PATH_IN = "data_new_20251119_1.xlsx"
JSON_PATH = "data_result_list_2.json"
EXCEL_PATH_OUT = "data_new_20251119_1_end.xlsx"


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


# === 신규: 등록번호 코어 추출 (숫자만 + 앞 9자리) ===
def extract_reg_core(s: Any) -> str:
    """
    등록번호 코어 추출:
    - 문자열에서 숫자만 남김
      예) '10-0506897' -> '100506897'
          '1005068970000' -> '1005068970000'
    - 9자리 이상이면 앞 9자리만 사용
      예) '1005068970000' -> '100506897'
    """
    raw = _clean(s)
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if len(digits) >= 9:
        return digits[:9]
    return digits


# === 신규: 권리만료일 계산 ===
def compute_expiry_date(item: Dict[str, Any]) -> str:
    """
    권리만료일(YYYY-MM-DD) 계산:
    - AD(출원일, 'YYYY-MM-DD') 기준 + 20년
    - AD 없으면 EDT('YYYY.MM.DD' 또는 비슷한 포맷) 시도
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
# JSON 인덱스 (등록번호코어 → item)
# =========================
def load_json_index(path: str) -> Dict[str, Dict[str, Any]]:
    """
    등록번호 코어 기준 인덱스 구성: { reg_core(9자리) : item }

    - GN, GNS 둘 다에서 후보 추출
    - 예)
      GN = '1005068970000'
      GNS = '10, 05068970000, 100506897, 0506897, 1005068970000'
      -> 코어 '100506897' 로 인덱스
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON 최상위 구조는 리스트여야 합니다.")

    index: Dict[str, Dict[str, Any]] = {}
    for it in data:
        candidates: List[str] = []

        gn = it.get("GN")
        if gn:
            candidates.append(_clean(gn))

        gns = it.get("GNS")
        if gns:
            # 콤마/파이프/공백 등으로 나눠서 각각 후보로 사용
            for part in re.split(r"[,\|]+", _clean(gns)):
                if part.strip():
                    candidates.append(part.strip())

        for cand in candidates:
            core = extract_reg_core(cand)
            if core and core not in index:
                index[core] = it

    print(f"[INFO] JSON 인덱스 등록번호 코어 개수: {len(index)}")
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
        reg_index = load_json_index(JSON_PATH)
    except Exception as e:
        print(f"[ERROR] JSON 로드/인덱스 실패: {e}")
        return

    # 3) 결과 컬럼 준비 (문자열용)
    target_cols = [
        "출원인",
        "최종권리자",
        "출원번호(일자)",
        "권리만료일",  # === 신규 ===
        "법적상태 (등록/소멸-등록료불납/존속기간만료)",
        "발명자수",
        "심사청구항수",
        "피인용(수)",
        "패밀리정보(수)",
        "IPC코드(전체)",
    ]
    for col in target_cols:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].apply(_clean)

    # 4) 각 행 매핑
    for idx in range(len(df)):
        reg2_raw = df.at[idx, "등록번호2"]
        reg_core = extract_reg_core(reg2_raw)  # 예: 10-0506897 -> 100506897

        if not reg_core:
            print(f"[MISS] row={idx+1}, 등록번호2 비어있음")
            continue

        item = reg_index.get(reg_core)
        if not item:
            print(f"[MISS] row={idx+1}, 등록번호2={reg2_raw} (core={reg_core}) → 매칭 없음")
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

        # 권리만료일: 존속기간만료인 경우에만 계산
        expiry_date = ""
        if "존속기간만료" in lsto:
            expiry_date = compute_expiry_date(item)

        df.at[idx, "출원인"] = ap
        df.at[idx, "최종권리자"] = trh
        df.at[idx, "출원번호(일자)"] = an
        df.at[idx, "권리만료일"] = expiry_date
        df.at[idx, "법적상태 (등록/소멸-등록료불납/존속기간만료)"] = lsto
        df.at[idx, "발명자수"] = in_cnt
        df.at[idx, "심사청구항수"] = bic
        df.at[idx, "피인용(수)"] = bctc
        df.at[idx, "패밀리정보(수)"] = fam
        df.at[idx, "IPC코드(전체)"] = ipc_full

        print(f"[MATCH] row={idx+1}, 등록번호2={reg2_raw} (core={reg_core}) → 매핑 완료")

    # 5) 저장
    try:
        df.to_excel(EXCEL_PATH_OUT, index=False)
        print(f"[OK] 저장 완료: {EXCEL_PATH_OUT} (rows={len(df)})")
    except Exception as e:
        print(f"[ERROR] 엑셀 저장 실패: {e}")


if __name__ == "__main__":
    main()
