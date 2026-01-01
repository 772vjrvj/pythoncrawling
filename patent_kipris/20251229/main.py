# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import time
import pandas as pd

INPUT_XLSX = "20251229_data.xlsx"
OUTPUT_XLSX = "20251229_data_filled_fast.xlsx"
SHEETS = ["A사", "K사", "P사"]

COL_GUBUN = "구분"
COL_T1 = "시점1"
COL_T2 = "시점2"
COL_IPC = "대표IPC"

COL_T1_CNT = "시점1(건)"
COL_T2_CNT = "시점2(건)"
COL_T1_PCT = "시점1(%)"
COL_T2_PCT = "시점2(%)"


def log(msg: str):
    print(f"[LOG] {msg}")


def _norm_series(s: pd.Series) -> pd.Series:
    # dtype 섞여도 안전하게 문자열 정규화
    return s.astype("string").fillna("").str.strip()


def _attach_counts(df: pd.DataFrame, time_col: str, out_cnt_col: str, out_pct_col: str, sheet_name: str):
    """
    df에 (time_col, 대표IPC) 기준:
      - 기부건수
      - 전체건수(기부+비기부)
      를 merge로 붙이고, pct 계산해서 out_* 컬럼에 넣는다.
    """
    t0 = time.time()
    tmp = pd.DataFrame({
        "_t": _norm_series(df[time_col]),
        "_ipc": _norm_series(df[COL_IPC]),
        "_g": _norm_series(df[COL_GUBUN]),
    })

    # === 신규 === 전체 건수 (기부+비기부)
    total = (
        tmp.groupby(["_t", "_ipc"], dropna=False)
        .size()
        .reset_index(name="_total")
    )

    # === 신규 === 기부 건수
    donor = (
        tmp.loc[tmp["_g"].eq("기부")]
        .groupby(["_t", "_ipc"], dropna=False)
        .size()
        .reset_index(name="_donor")
    )

    # === 신규 === (t, ipc)별 donor/total 한 테이블로 만들기
    agg = total.merge(donor, on=["_t", "_ipc"], how="left")
    agg["_donor"] = agg["_donor"].fillna(0).astype("int64")

    # === 신규 === pct 계산 (0 나눗셈 방지)
    agg["_pct"] = (agg["_donor"] / agg["_total"] * 100.0).where(agg["_total"] > 0, 0.0)

    # === 신규 === 원본 df에 붙이기 위한 key 프레임
    key_df = pd.DataFrame({
        "_t": tmp["_t"],
        "_ipc": tmp["_ipc"],
    })

    # === 신규 === merge (원본 row 수 그대로 유지)
    merged = key_df.merge(agg[["_t", "_ipc", "_donor", "_pct"]], on=["_t", "_ipc"], how="left")

    # 결과 컬럼에 주입
    df[out_cnt_col] = merged["_donor"].astype("int64")
    df[out_pct_col] = merged["_pct"].astype("float64")

    log(f"[{sheet_name}] {time_col} 집계/머지 완료 (소요 {time.time()-t0:.2f}s)")
    return df


def _fill_sheet_fast(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    t0 = time.time()
    n = len(df)
    log(f"[{sheet_name}] row 수: {n:,}")

    # 결과 컬럼 보장
    for c in [COL_T1_CNT, COL_T2_CNT, COL_T1_PCT, COL_T2_PCT]:
        if c not in df.columns:
            df[c] = None

    log(f"[{sheet_name}] 시점1 처리 시작")
    df = _attach_counts(df, time_col=COL_T1, out_cnt_col=COL_T1_CNT, out_pct_col=COL_T1_PCT, sheet_name=sheet_name)

    log(f"[{sheet_name}] 시점2 처리 시작")
    df = _attach_counts(df, time_col=COL_T2, out_cnt_col=COL_T2_CNT, out_pct_col=COL_T2_PCT, sheet_name=sheet_name)

    log(f"[{sheet_name}] 시트 완료 (총 {time.time()-t0:.2f}s)")
    return df


def main():
    if not os.path.exists(INPUT_XLSX):
        raise FileNotFoundError(f"파일 없음: {os.path.abspath(INPUT_XLSX)}")

    t_all = time.time()
    log("전체 시작")

    results = []
    for sheet in SHEETS:
        log(f"[{sheet}] 시트 로드")
        df = pd.read_excel(INPUT_XLSX, sheet_name=sheet, dtype=object)
        df2 = _fill_sheet_fast(df, sheet)
        results.append((sheet, df2))

    log("엑셀 저장 시작")
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        for sheet, df2 in results:
            df2.to_excel(writer, sheet_name=sheet, index=False)

    log(f"전체 완료 (총 {time.time()-t_all:.2f}s)")
    log(f"결과 파일: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
