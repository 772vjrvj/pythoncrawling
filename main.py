import os
import pandas as pd

# 경로 설정
base_path = r"D:\GIT\pythoncrawling\kmong\ko\prism_research"
excel_path = os.path.join(base_path, "prism_data_work.xlsx")
output_excel = os.path.join(base_path, "prism_data_work_결과.xlsx")

# 엑셀 파일 확인
if not os.path.exists(excel_path):
    print(f"엑셀 파일이 존재하지 않습니다: {excel_path}")
    exit()

# 엑셀 파일 읽기 (Sheet1)
df = pd.read_excel(excel_path, sheet_name="Sheet1")

# '사업명'과 '과제명'이 모두 동일한 데이터 찾기
duplicate_rows = df[df.duplicated(subset=["사업명", "과제명"], keep=False)]

# '사업명'과 '과제명'이 동일한 데이터 중 첫 번째만 유지
# 중복되지 않은 데이터 (1개만 존재하는 경우)
non_duplicated_rows = df.groupby(["사업명", "과제명"]).filter(lambda x: len(x) == 1)

# 중복된 데이터 중 첫 번째 행만 유지
unique_rows = pd.concat([
    df[df.duplicated(subset=["사업명", "과제명"], keep="first") == False],
    non_duplicated_rows
])
# 엑셀 파일로 저장
with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
    duplicate_rows.to_excel(writer, sheet_name="중복", index=False)
    unique_rows.to_excel(writer, sheet_name="중복제거", index=False)

print(f"결과 파일이 생성되었습니다: {output_excel}")
print("비교 작업 완료! 🚀")
