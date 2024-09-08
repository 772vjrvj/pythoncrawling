import pandas as pd

# 엑셀 파일을 읽기
xlsx_file = 'products.xlsx'  # 변환할 .xlsx 파일 경로
df = pd.read_excel(xlsx_file)

# CSV 파일로 저장
csv_file = 'products.csv'  # 저장할 .csv 파일 경로
df.to_csv(csv_file, index=False)

print(f"'{xlsx_file}' 파일이 '{csv_file}'로 성공적으로 변환되었습니다.")