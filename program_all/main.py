# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import pandas as pd


def excel_to_csv(filename: str):
    base_dir = os.getcwd()  # 프로그램 실행 경로
    xlsx_path = os.path.join(base_dir, filename)

    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"엑셀 파일이 없습니다: {xlsx_path}")

    csv_path = os.path.splitext(xlsx_path)[0] + ".csv"

    # === 모든 셀을 문자열로 읽기 ===
    df = pd.read_excel(
        xlsx_path,
        dtype=str,
        engine="openpyxl"
    )

    # === NaN -> 빈 문자열 ===
    df = df.fillna("")

    # === CSV 저장 (그누보드 호환 최우선) ===
    df.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig"  # 한글 + Excel + PHP 호환
    )

    print(f"[OK] CSV 변환 완료: {csv_path}")


if __name__ == "__main__":
    excel_to_csv("남성.xlsx")
