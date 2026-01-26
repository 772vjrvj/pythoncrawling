# clean_thairath_csv_dedup_sort.py
# -*- coding: utf-8 -*-

"""
요구사항(최종)
0) E경로에 없는 이미지 미리 제거 ID 숫자 아닌거 제거 후 작업시작
1) 실행 경로의 thairath.csv 읽기
2) id 중복이면 "처음 1개만" 남기고 나머지 제거
3) id 오름차순 정렬
4) 결과를 thairath_clean.csv 로 저장

주의
- image_path 관련 필터링(E로 시작 등)은 사용자께서 수동으로 이미 정리했다고 가정 → 코드에서 제외
- 컬럼명 뒤 공백/중복 컬럼명 같은 CSV 깨짐 방지용 안전장치 포함
"""

import pandas as pd
from pathlib import Path


SRC_CSV = "../../thairath.csv"
OUT_CSV = "thairath_clean.csv"


def _safe_int(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None


def main():
    base = Path.cwd()
    src = base / SRC_CSV
    out = base / OUT_CSV

    if not src.exists():
        raise FileNotFoundError(f"CSV not found: {src}")

    df = pd.read_csv(src, dtype=str, keep_default_na=False)
    before = len(df)

    # =========================
    # 0) 컬럼명/중복 컬럼 방어
    # =========================
    df.columns = [str(c).strip() for c in df.columns]
    if df.columns.duplicated().any():
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        print("[WARN] duplicated columns detected ->", dup_cols)
        df = df.loc[:, ~df.columns.duplicated()].copy()

    if "id" not in df.columns:
        raise ValueError(f"Missing required column: id (columns={list(df.columns)})")

    # =========================
    # 1) id 중복 제거 (첫 번째만 유지)
    # =========================
    df = df.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)
    after_dedup = len(df)

    # =========================
    # 2) id 오름차순 정렬 (숫자/문자 혼합 안전)
    # =========================
    df["_id_int"] = df["id"].apply(_safe_int)
    df = df.sort_values(by=["_id_int", "id"], ascending=True).reset_index(drop=True)
    df = df.drop(columns=["_id_int"])

    # =========================
    # 3) 저장
    # =========================
    df.to_csv(out, index=False, encoding="utf-8-sig")

    print("=" * 70)
    print(f"Original rows   : {before}")
    print(f"After dedupe    : {after_dedup} (removed {before - after_dedup})")
    print(f"Final rows      : {len(df)}")
    print(f"Output CSV      : {out}")
    print("=" * 70)


if __name__ == "__main__":
    main()
