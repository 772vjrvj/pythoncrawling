import pandas as pd

def convert_excel_to_csv(excel_path, csv_path, sheet_name=0):
    # 엑셀 파일 읽기
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # CSV로 저장 (인코딩: UTF-8-sig → Excel 호환용)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

# 사용 예시
convert_excel_to_csv("vip_review_result a.xlsx", "vip_review_result a.csv")
