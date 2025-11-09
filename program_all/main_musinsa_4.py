# -*- coding: utf-8 -*-
"""
1) '정영상 화장품&라이프스타일(G메일).csv'에서 A~U, 1~232 영역의 이메일 수집
2) '무신사 뷰티 이메일 사이트별 분류.xlsx'의 'gmail' 시트에서
   위에서 수집한 이메일이 있는 행 제거
3) 결과를 '무신사 뷰티 이메일 사이트별 분류_최종.xlsx'로 저장
"""

import pandas as pd
import re

CSV_PATH = '정영상 화장품&라이프스타일(G메일).csv'
SRC_XLSX_PATH = '무신사 뷰티 이메일 사이트별 분류.xlsx'
OUT_XLSX_PATH = '무신사 뷰티 이메일 사이트별 분류_최종.xlsx'
GMAIL_SHEET_NAME = 'gmail'


def read_csv_with_fallback(path: str) -> pd.DataFrame:
    """utf-8 → cp949 순으로 시도"""
    try:
        return pd.read_csv(path, header=None, dtype=str, encoding='utf-8')
    except UnicodeDecodeError:
        print('[WARN] UTF-8 디코딩 실패 → CP949로 재시도')
        return pd.read_csv(path, header=None, dtype=str, encoding='cp949')


def is_valid_email(email: str) -> bool:
    """간단한 이메일 형식 검증"""
    if not isinstance(email, str):
        return False
    email = email.strip()
    if not email:
        return False
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


def extract_emails_from_cell(value: str):
    """셀에서 이메일 후보들을 추출 (구분자: 콤마, 세미콜론, 공백 등)"""
    if not isinstance(value, str):
        return []
    text = value.strip()
    if not text:
        return []

    # 공통 구분자로 split
    parts = re.split(r'[,\s;/]+', text)
    return [p.strip() for p in parts if is_valid_email(p.strip())]


def collect_block_emails_from_csv() -> set:
    """
    CSV A~U, 1~232 영역에서 유효 이메일만 수집하여 set으로 반환
    """
    df = read_csv_with_fallback(CSV_PATH)

    # A~U = 0~20 컬럼, 1~232 행 = iloc[:232]
    sub = df.iloc[:232, :21]

    emails = set()
    for _, row in sub.iterrows():
        for val in row:
            for email in extract_emails_from_cell(val if isinstance(val, str) else str(val) if val is not None else ''):
                emails.add(email)

    print(f'[INFO] CSV에서 수집된 차단용 이메일 수: {len(emails)}')
    return emails


def row_contains_block_email(row, block_emails: set) -> bool:
    """
    한 행(row)에 block_emails에 포함되는 이메일이 하나라도 있으면 True
    - 행의 모든 셀을 검사
    """
    for val in row:
        if val is None:
            continue
        # 문자열로 변환 후 이메일 추출
        candidates = extract_emails_from_cell(str(val))
        for c in candidates:
            if c in block_emails:
                return True
    return False


def main():
    # 1) CSV에서 제거 대상 이메일 목록 생성
    block_emails = collect_block_emails_from_csv()
    if not block_emails:
        print('[WARN] CSV에서 추출된 유효 이메일이 없습니다. 원본 그대로 복사합니다.')

    # 2) 기존 엑셀 로드
    try:
        xls = pd.ExcelFile(SRC_XLSX_PATH)
    except Exception as e:
        print(f'[ERROR] 엑셀 로드 실패: {e}')
        return

    if GMAIL_SHEET_NAME not in xls.sheet_names:
        print(f"[ERROR] '{GMAIL_SHEET_NAME}' 시트를 찾을 수 없습니다. 시트 목록: {xls.sheet_names}")
        return

    # 3) 시트별 DF 로드
    sheets = {}
    for sheet_name in xls.sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)

    # 4) gmail 시트 필터링
    df_gmail = sheets[GMAIL_SHEET_NAME]

    if block_emails:
        # 각 행에 대해 block_emails 포함 여부 체크 후 제거
        mask_drop = df_gmail.apply(lambda row: row_contains_block_email(row, block_emails), axis=1)
        df_gmail_filtered = df_gmail[~mask_drop].reset_index(drop=True)
    else:
        df_gmail_filtered = df_gmail

    print(f"[INFO] gmail 시트 원본 행수: {len(df_gmail)}")
    print(f"[INFO] gmail 시트 필터링 후 행수: {len(df_gmail_filtered)}")

    sheets[GMAIL_SHEET_NAME] = df_gmail_filtered

    # 5) 새 엑셀로 저장
    try:
        with pd.ExcelWriter(OUT_XLSX_PATH, engine='openpyxl') as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"[OK] 최종 파일 저장 완료 → {OUT_XLSX_PATH}")
    except Exception as e:
        print(f"[ERROR] 엑셀 저장 실패: {e}")


if __name__ == '__main__':
    main()
