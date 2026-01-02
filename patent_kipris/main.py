# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import time
import pandas as pd

INPUT_XLSX = "20260101_data.xlsx"
OUTPUT_XLSX = "20260101_data_filled_fast.xlsx"
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


def _clean_col_name(x) -> str:
    # BOM/공백/탭/개행/NBSP 등 제거
    s = "" if x is None else str(x)
    return (
        s.replace("\ufeff", "")
        .replace("\u00a0", " ")
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def _norm_series(s: pd.Series) -> pd.Series:
    return s.astype("string").fillna("").str.strip()


def _read_sheet_with_auto_header(path: str, sheet_name: str) -> pd.DataFrame:
    """
    '구분/시점1/시점2/대표IPC'가 들어있는 행을 header로 자동 탐지해서 읽는다.
    """
    required = {COL_GUBUN, COL_T1, COL_T2, COL_IPC}

    # 1) 일단 header 없이 일부만 읽어서 "어떤 행이 헤더인지" 찾기
    preview = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=30, dtype=object)

    header_row = None
    for r in range(min(len(preview), 30)):
        row_vals = [_clean_col_name(v) for v in preview.iloc[r].tolist()]
        row_set = set([v for v in row_vals if v != ""])
        if required.issubset(row_set):
            header_row = r
            break

    if header_row is None:
        # 못 찾으면 디버그용으로 상단 10행 덤프하고 종료
        dump = []
        for r in range(min(len(preview), 10)):
            dump.append([_clean_col_name(v) for v in preview.iloc[r].tolist()])
        log(f"[{sheet_name}] ❌ 헤더 행 자동탐지 실패. 상단 10행 덤프:")
        for i, rr in enumerate(dump):
            log(f"  row{i}: {rr}")
        raise RuntimeError(f"[{sheet_name}] 헤더 행을 찾지 못했습니다. (구분/시점1/시점2/대표IPC)")

    log(f"[{sheet_name}] ✅ header 행 감지: {header_row} (0-base)")

    # 2) 찾은 header_row로 다시 제대로 읽기
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row, dtype=object)

    # 3) 컬럼명 정리
    df.columns = [_clean_col_name(c) for c in df.columns]

    # 4) 필수 컬럼 존재 검증
    cols = set(df.columns)
    missing = [c for c in [COL_GUBUN, COL_T1, COL_T2, COL_IPC] if c not in cols]
    if missing:
        log(f"[{sheet_name}] ❌ 필수 컬럼 누락: {missing}")
        log(f"[{sheet_name}] columns: {list(df.columns)}")
        raise KeyError(f"[{sheet_name}] 필수 컬럼 누락: {missing}")

    return df


def _attach_counts_by_gubun(
        df: pd.DataFrame,
        time_col: str,
        out_cnt_col: str,
        out_pct_col: str,
        sheet_name: str
) -> pd.DataFrame:
    """
    (구분, 시점, 대표IPC) 기준:
      - 분자: 해당 구분(기부/비기부) 건수  (구분+시점+IPC)
      - 분모: "해당 시점(년도)" 전체 row 수 = (기부+비기부) 합계  (시점만으로 집계)
    """
    t0 = time.time()

    tmp = pd.DataFrame({
        "_g": _norm_series(df[COL_GUBUN]),
        "_t": _norm_series(df[time_col]),
        "_ipc": _norm_series(df[COL_IPC]),
    })

    # === 신규 === 분모: 시점(년도)별 전체 건수 (기부+비기부 전체)
    denom = (
        tmp.groupby(["_t"], dropna=False)
        .size()
        .reset_index(name="_denom")
    )
    denom["_denom"] = denom["_denom"].fillna(0).astype("int64")

    # === 분자 === (구분, 시점, IPC) 건수
    part = (
        tmp.groupby(["_g", "_t", "_ipc"], dropna=False)
        .size()
        .reset_index(name="_part")
    )
    part["_part"] = part["_part"].fillna(0).astype("int64")

    # === 신규 === part에 분모(년도 전체) 붙이기
    part = part.merge(
        denom[["_t", "_denom"]],
        on=["_t"],
        how="left"
    )

    # === pct === (해당 시점(년도) 분모)
    # 분모 0이면 0.0 처리
    part["_pct"] = 0.0
    nz = part["_denom"].fillna(0).astype("int64") > 0
    part.loc[nz, "_pct"] = (part.loc[nz, "_part"] / part.loc[nz, "_denom"]) * 100.0

    # === 원본 row 유지하며 붙이기 ===
    key_df = pd.DataFrame({
        "_g": tmp["_g"],
        "_t": tmp["_t"],
        "_ipc": tmp["_ipc"],
    })

    merged = key_df.merge(
        part[["_g", "_t", "_ipc", "_part", "_pct"]],
        on=["_g", "_t", "_ipc"],
        how="left"
    )

    df[out_cnt_col] = merged["_part"].fillna(0).astype("int64")
    df[out_pct_col] = merged["_pct"].fillna(0.0).astype("float64")

    # === 신규 === 로그(분모 정책 명확히)
    # 시점 종류 수 / 예시 분모 일부 찍기(너무 길면 앞 5개만)
    denom_preview = denom.head(5).to_dict(orient="records")
    log(f"[{sheet_name}] {time_col} 집계/머지 완료 (분모=해당시점(년도) 전체, 시점종류={len(denom):,}, 예시={denom_preview}, 소요 {time.time() - t0:.2f}s)")
    return df


def _fill_sheet_fast(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    t0 = time.time()
    log(f"[{sheet_name}] row 수: {len(df):,}")

    # 결과 컬럼 보장
    for c in [COL_T1_CNT, COL_T2_CNT, COL_T1_PCT, COL_T2_PCT]:
        if c not in df.columns:
            df[c] = None

    log(f"[{sheet_name}] 시점1 처리 시작")
    df = _attach_counts_by_gubun(
        df,
        time_col=COL_T1,
        out_cnt_col=COL_T1_CNT,
        out_pct_col=COL_T1_PCT,
        sheet_name=sheet_name
    )

    log(f"[{sheet_name}] 시점2 처리 시작")
    df = _attach_counts_by_gubun(
        df,
        time_col=COL_T2,
        out_cnt_col=COL_T2_CNT,
        out_pct_col=COL_T2_PCT,
        sheet_name=sheet_name
    )

    log(f"[{sheet_name}] 시트 완료 (총 {time.time() - t0:.2f}s)")
    return df


def main():
    if not os.path.exists(INPUT_XLSX):
        raise FileNotFoundError(f"파일 없음: {os.path.abspath(INPUT_XLSX)}")

    t_all = time.time()
    log("전체 시작")

    results = []
    for sheet in SHEETS:
        log(f"[{sheet}] 시트 로드(자동 헤더 탐지)")
        df = _read_sheet_with_auto_header(INPUT_XLSX, sheet_name=sheet)
        df2 = _fill_sheet_fast(df, sheet)
        results.append((sheet, df2))

    log("엑셀 저장 시작")
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        for sheet, df2 in results:
            df2.to_excel(writer, sheet_name=sheet, index=False)

    log(f"전체 완료 (총 {time.time() - t_all:.2f}s)")
    log(f"결과 파일: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
