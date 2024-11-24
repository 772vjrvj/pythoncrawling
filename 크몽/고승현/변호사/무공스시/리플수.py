import pandas as pd

# 엑셀 파일 경로
file_path = r"D:\GitHub\pythoncrawling\test2.xlsx"

# 엑셀 파일 읽기
df = pd.read_excel(file_path)

# 키워드 컬럼 이름 설정 (엑셀 파일에 맞게 수정)
df.columns = ['키워드']

# 키워드별 개수 계산
keyword_counts = df['키워드'].value_counts()

# 결과 출력
print("키워드별 개수:")
for keyword, count in keyword_counts.items():
    print(f"{keyword}: {count}")
