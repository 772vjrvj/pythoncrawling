# -*- coding: utf-8 -*-
"""
KIPRIS 매칭 고속 버전 (BIC, BCTC 제외)
- 출원인(AP) 일치
- 등록번호(GN 포함)
- IPC코드(IPC 포함)
- 출원년도(AN 포함)
"""

import json
import math
import os
import time
import threading
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_XLSX  = "data_new_20251022_2.xlsx"
REF_JSON    = "old_1.json"
OUTPUT_XLSX = "data_new_20251022_2_filled.xlsx"

COL_AP      = "출원인"
COL_GN_SUB  = "등록번호"
COL_IPC_SUB = "IPC코드"
COL_AN_SUB  = "출원년도"

COL_TARGET_AN        = "출원번호(일자)"
COL_TARGET_IN_CNT    = "발명자수"
COL_TARGET_GN_FULL   = "전체등록번호"
COL_TARGET_IPC_FULL  = "IPC(풀코드로 추출 요청)"
COL_TARGET_LSTO      = "법적상태(등록/소멸-등록료불납/존속기간만료)"

FILL_ONLY_IF_EMPTY = True
NUM_WORKERS = 10

print_lock = threading.Lock()


# =========================
# 유틸
# =========================
def s(x: Any) -> str:
    """NaN/None 포함 모든 값을 안전하게 문자열화"""
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x).strip()

def parse_inventor_count(in_field) -> str:
    t = s(in_field)
    return "" if not t else str(t.count("|") + 1)

def contains(haystack: Any, needle: Any) -> bool:
    hs, nd = s(haystack), s(needle)
    return bool(hs and nd and nd in hs)

def equals(a: Any, b: Any) -> bool:
    return s(a) == s(b)

def row_is_empty(val: Any) -> bool:
    return s(val) == ""


# =========================
# JSON 인덱스 (AP 기준만)
# =========================
def build_index(ref_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    idx: Dict[str, List[Dict[str, Any]]] = {}
    for r in ref_list:
        r2 = {k: s(v) for k, v in r.items()}
        ap = r2.get("AP", "")
        if ap:
            idx.setdefault(ap, []).append(r2)
    return idx


# =========================
# 매칭
# =========================
def match_one_row(i: int, row: pd.Series, ref_idx: Dict[str, List[Dict[str, Any]]]) -> Tuple[int, Dict[str, str]]:
    ap = s(row.get(COL_AP))
    candidates = ref_idx.get(ap, [])
    if not candidates:
        return i, {}

    gn_sub, ipc_sub, an_sub = s(row.get(COL_GN_SUB)), s(row.get(COL_IPC_SUB)), s(row.get(COL_AN_SUB))

    for ref in candidates:
        if not contains(ref.get("GN", ""), gn_sub):
            continue
        if not contains(ref.get("IPC", ""), ipc_sub):
            continue
        if not contains(ref.get("AN", ""), an_sub):
            continue

        with print_lock:
            print(f"[{i+1}] {ap} - 성공 (AN={ref.get('AN', '')})")

        return i, {
            COL_TARGET_AN:       s(ref.get("AN")),
            COL_TARGET_IN_CNT:   parse_inventor_count(ref.get("IN")),
            COL_TARGET_GN_FULL:  s(ref.get("GN")),
            COL_TARGET_IPC_FULL: s(ref.get("IPC")),
            COL_TARGET_LSTO:     s(ref.get("LSTO")),
        }

    return i, {}


# =========================
# 메인
# =========================
def main():
    t0 = time.time()
    if not os.path.exists(INPUT_XLSX):
        raise FileNotFoundError(f"입력 엑셀 없음: {INPUT_XLSX}")
    if not os.path.exists(REF_JSON):
        raise FileNotFoundError(f"JSON 없음: {REF_JSON}")

    with open(REF_JSON, "r", encoding="utf-8") as f:
        ref_list = json.load(f)
        if not isinstance(ref_list, list):
            raise ValueError("JSON 형식 오류: 배열이어야 함")

    ref_index = build_index(ref_list)
    df = pd.read_excel(INPUT_XLSX, dtype=str).fillna("")

    for col in [COL_TARGET_AN, COL_TARGET_IN_CNT, COL_TARGET_GN_FULL, COL_TARGET_IPC_FULL, COL_TARGET_LSTO]:
        if col not in df.columns:
            df[col] = ""

    updates: List[Tuple[int, Dict[str, str]]] = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as ex:
        futures = [ex.submit(match_one_row, i, row, ref_index) for i, row in df.iterrows()]
        for fut in as_completed(futures):
            idx, vals = fut.result()
            if vals:
                updates.append((idx, vals))

    filled_cells = 0
    for i, vals in updates:
        for col, new_val in vals.items():
            if FILL_ONLY_IF_EMPTY and not row_is_empty(df.at[i, col]):
                continue
            df.at[i, col] = s(new_val)
            filled_cells += 1

    df.to_excel(OUTPUT_XLSX, index=False)
    elapsed = time.time() - t0
    print(f"\n[완료] 총 {len(df)}행 / 채워진 셀 {filled_cells}개 / {elapsed:.2f}s → {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
