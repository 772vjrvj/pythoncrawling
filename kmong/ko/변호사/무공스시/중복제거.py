import pandas as pd

# 엑셀 파일 경로
file_path = r"D:\GitHub\pythoncrawling\test2.xlsx"

# 엑셀 파일 읽기
df = pd.read_excel(file_path)

# 컬럼 이름 설정 (글번호와 키워드)
df.columns = ['글번호', '키워드']

# 중복 제거
unique_mappings = df.drop_duplicates()

# 키워드별 고유 글번호 개수 계산
keyword_mapping_count = unique_mappings.groupby('키워드')['글번호'].nunique()

# 결과 출력
print("키워드별 고유 글번호 개수:")
print(keyword_mapping_count)

# 필요한 경우 결과를 엑셀로 저장
output_path = r"D:\GitHub\pythoncrawling\keyword_mapping_count.xlsx"
keyword_mapping_count.to_excel(output_path, sheet_name='키워드별 글번호 개수')
print(f"결과가 {output_path}에 저장되었습니다.")
