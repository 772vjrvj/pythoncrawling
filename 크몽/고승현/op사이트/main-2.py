import pandas as pd

# 엑셀 파일 로드
df = pd.read_excel("오피스타.xlsx")

# 1. 업소번호가 없는 행 제거
df = df[df['업소번호'].notna() & df['업소번호'].str.strip().ne("")]

# 2. 업소번호 중복 제거 (처음 것만 남기고 나머지 제거)
df = df.drop_duplicates(subset=['업소번호'], keep='first')

# 결과를 다시 엑셀 파일로 저장
df.to_excel("output_cleaned.xlsx", index=False)

print("데이터가 정리되어 output_cleaned.xlsx 파일에 저장되었습니다.")
