# -*- coding: utf-8 -*-
"""
1) 정영상 화장품&라이프스타일(Sheet1).csv, (Sheet2).csv 에서
   A~Z, 1~591 범위 내의 모든 셀에서 유효한 이메일 추출 (공백 제외)
   → block_emails 집합 생성

2) 무신사 뷰티 이메일 사이트별 분류.xlsx 로드
   - 'naver daum' 시트에서 block_emails 에 포함된 이메일이 있는 행 제거
   - '그외' 시트에서도 동일하게 제거
   - 다른 시트는 원본 유지

3) 무신사 뷰티 이메일 사이트별 분류_최종.xlsx 로 저장
"""

import pandas as pd
import re

CSV1_PATH = "정영상 화장품&라이프스타일(Sheet1).csv"
CSV2_PATH = "정영상 화장품&라이프스타일(Sheet2).csv"
SRC_XLSX_PATH = "무신사 뷰티 이메일 사이트별 분류.xlsx"
OUT_XLSX_PATH = "무신사 뷰티 이메일 사이트별 분류_최종.xlsx"

SHEET_NAVER_DAUM = "naver daum"
SHEET_ETC = "그외"


def read_csv_with_fallback(path: str) -> pd.DataFrame:
    """utf-8 → cp949 순으로 시도해서 CSV 읽기 (header 없음)."""
    try:
        return pd.read_csv(path, header=None, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        print(f"[WARN] {path} UTF-8 실패 → CP949로 재시도")
        return pd.read_csv(path, header=None, dtype=str, encoding="cp949")


def is_valid_email(email: str) -> bool:
    """간단한 이메일 형식 검증."""
    if not isinstance(email, str):
        return False
    email = email.strip()
    if not email:
        return False
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


def extract_emails_from_cell(value: str):
    """
    셀에서 이메일 후보 추출.
    콤마, 세미콜론, 공백, 슬래시 등으로 구분된 값들 중 유효 이메일만 반환.
    """
    if not isinstance(value, str):
        return []
    text = value.strip()
    if not text:
        return []
    parts = re.split(r"[,\s;/]+", text)
    return [p for p in (s.strip() for s in parts) if is_valid_email(p)]


def collect_block_emails_from_csv(paths) -> set:
    """
    다수 CSV에서 A~Z, 1~591 범위 내 이메일 수집 → set 반환.
    (A~Z = 0~25, 1~591 = iloc[0:591])
    """
    emails = set()
    for path in paths:
        df = read_csv_with_fallback(path)

        # 범위 제한: 행 0~590, 열 0~25
        sub = df.iloc[:591, :26]

        for _, row in sub.iterrows():
            for val in row:
                if val is None:
                    continue
                for email in extract_emails_from_cell(str(val)):
                    emails.add(email)

    print(f"[INFO] 차단용 이메일 총 수: {len(emails)}")
    return emails


def row_contains_block_email(row, block_emails: set) -> bool:
    """
    한 행(row)에 block_emails 에 속한 이메일이 하나라도 있으면 True.
    - 행의 모든 셀을 검사.
    """
    for val in row:
        if val is None:
            continue
        for email in extract_emails_from_cell(str(val)):
            if email in block_emails:
                return True
    return False


def main():
    # 1) CSV 두 개에서 차단 대상 이메일 수집
    block_emails = collect_block_emails_from_csv([CSV1_PATH, CSV2_PATH])
    if not block_emails:
        print("[WARN] 수집된 이메일이 없습니다. 원본 그대로 복사합니다.")

    # 2) 기존 엑셀 로드
    try:
        xls = pd.ExcelFile(SRC_XLSX_PATH)
    except Exception as e:
        print(f"[ERROR] 엑셀 로드 실패: {e}")
        return

    sheets = {}
    for sheet_name in xls.sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)

    # 3) 'naver daum' 시트 필터링
    if SHEET_NAVER_DAUM in sheets and block_emails:
        df_nd = sheets[SHEET_NAVER_DAUM]
        mask_drop = df_nd.apply(lambda row: row_contains_block_email(row, block_emails), axis=1)
        df_nd_filtered = df_nd[~mask_drop].reset_index(drop=True)
        print(f"[INFO] 'naver daum' 원본: {len(df_nd)}, 필터링 후: {len(df_nd_filtered)}")
        sheets[SHEET_NAVER_DAUM] = df_nd_filtered
    elif SHEET_NAVER_DAUM not in sheets:
        print(f"[WARN] '{SHEET_NAVER_DAUM}' 시트를 찾을 수 없습니다. 시트 목록: {list(sheets.keys())}")

    # 4) '그외' 시트 필터링
    if SHEET_ETC in sheets and block_emails:
        df_etc = sheets[SHEET_ETC]
        mask_drop = df_etc.apply(lambda row: row_contains_block_email(row, block_emails), axis=1)
        df_etc_filtered = df_etc[~mask_drop].reset_index(drop=True)
        print(f"[INFO] '그외' 원본: {len(df_etc)}, 필터링 후: {len(df_etc_filtered)}")
        sheets[SHEET_ETC] = df_etc_filtered
    elif SHEET_ETC not in sheets:
        print(f"[WARN] '{SHEET_ETC}' 시트를 찾을 수 없습니다. 시트 목록: {list(sheets.keys())}")

    # 5) 새 엑셀 저장
    try:
        with pd.ExcelWriter(OUT_XLSX_PATH, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"[OK] 최종 파일 저장 완료 → {OUT_XLSX_PATH}")
    except Exception as e:
        print(f"[ERROR] 엑셀 저장 실패: {e}")


if __name__ == "__main__":
    main()
