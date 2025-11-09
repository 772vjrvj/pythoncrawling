# -*- coding: utf-8 -*-
"""
data_result_list_2.json 매칭 스크립트

- 엑셀(data_new_20251109_3.xlsx)에서 "등록번호" 컬럼 읽기
- 각 등록번호에서 '-' 제거하여 '10xxxx' 형태로 만듦
- data_result_list_2.json 의 각 항목에서 GN 값에 이 문자열이 포함되는지 검사
- 매칭된 경우 엑셀에 "등록번호2" 컬럼 추가 후 매칭된 GN 값 기록
- 결과를 data_new_20251109_3_out.xlsx 로 저장
"""

import json
import pandas as pd
from typing import Any, List, Dict

EXCEL_PATH = "data_new_20251109_3.xlsx"
JSON_PATH = "data_result_list_2.json"
OUT_PATH = "data_new_20251109_3_out.xlsx"


def _clean(v: Any) -> str:
    if pd.isna(v):
        return ""
    return str(v).strip()


def normalize_regno(v: str) -> str:
    """등록번호에서 '-' 제거한 문자열 반환"""
    s = _clean(v)
    if not s:
        return ""
    return s.replace("-", "").replace(" ", "")


def load_json_list(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON 최상위 구조가 배열이 아닙니다.")
    print(f"[INFO] JSON 레코드 수: {len(data)}")
    return data


def find_matching_gn(json_list: List[Dict[str, Any]], key: str) -> str:
    """GN 값 중 key가 포함된 항목의 GN 반환. 여러 개면 첫 번째."""
    for item in json_list:
        gn_raw = _clean(item.get("GN", ""))
        gn = gn_raw.replace("&nbsp;", "").replace(" ", "")
        if key in gn:
            return gn
    return ""


def main():
    # 엑셀 로드
    df = pd.read_excel(EXCEL_PATH)
    if "등록번호" not in df.columns:
        print('[ERROR] 엑셀에 "등록번호" 컬럼이 없습니다.')
        return

    # JSON 로드
    json_list = load_json_list(JSON_PATH)

    matched_gns = []
    for idx, row in df.iterrows():
        regno_raw = _clean(row.get("등록번호"))
        regno_norm = normalize_regno(regno_raw)

        if not regno_norm:
            matched_gns.append("")
            continue

        # GN 안에 regno_norm이 포함되는 항목 찾기
        gn_val = find_matching_gn(json_list, regno_norm)
        matched_gns.append(gn_val)

        print(f"[{idx+1}] {regno_raw} → {regno_norm} → 매칭 GN: {gn_val}")

    # 엑셀에 등록번호2 컬럼 추가
    df["등록번호2"] = matched_gns

    # 저장
    df.to_excel(OUT_PATH, index=False)
    print(f"[OK] 저장 완료: {OUT_PATH}")


if __name__ == "__main__":
    main()
