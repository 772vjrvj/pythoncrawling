import os
import shutil
import pandas as pd

# 경로 설정
base_path = r"D:\GIT\pythoncrawling\kmong\ko\prism_research"
input_excel = os.path.join(base_path, "prism_data_report.xlsx")
source_folder = os.path.join(base_path, "prism_data_report_전체")
dest_folder_unique = os.path.join(base_path, "prism_data_report_전체_중복제거")
dest_folder_duplicates = os.path.join(base_path, "prism_data_report_전체_중복")
output_excel_unique = os.path.join(base_path, "prism_data_report_중복제거.xlsx")
output_excel_duplicates = os.path.join(base_path, "prism_data_report_중복.xlsx")

# 폴더 생성 (없으면 생성)
os.makedirs(dest_folder_unique, exist_ok=True)
os.makedirs(dest_folder_duplicates, exist_ok=True)

# 엑셀 파일 읽기
df = pd.read_excel(input_excel)

# '보고서명'과 '파일명'이 동일한 것들 찾기
duplicated_groups = df.groupby(["보고서명", "파일명"]).filter(lambda x: len(x) >= 2)
non_duplicated_groups = df.groupby(["보고서명", "파일명"]).filter(lambda x: len(x) == 1)

# 중복 제거할 데이터 및 중복된 데이터 분리
unique_rows = []
duplicated_rows = []
copied_files = set()

for (report_name, file_name), group in duplicated_groups.groupby(["보고서명", "파일명"]):
    sorted_group = group.sort_values(by=["다운로드 파일"])  # 정렬 기준
    first_row = sorted_group.iloc[0]  # 첫 번째 행 (유지할 것)
    duplicate_rows = sorted_group.iloc[1:]  # 나머지 3개 (제외할 것)

    unique_rows.append(first_row)
    duplicated_rows.extend(sorted_group.to_dict('records'))

    # 첫 번째 행의 다운로드 파일명 찾기
    file_name = first_row["다운로드 파일"].strip()
    source_file = os.path.join(source_folder, file_name)

    if os.path.exists(source_file) and source_file not in copied_files:
        shutil.copy(source_file, dest_folder_unique)
        copied_files.add(source_file)

    # 중복 파일들 복사
    for _, row in sorted_group.iterrows():
        file_name = row["다운로드 파일"].strip()
        source_file = os.path.join(source_folder, file_name)

        if os.path.exists(source_file):
            shutil.copy(source_file, dest_folder_duplicates)

# 중복되지 않은 파일들도 이동
for _, row in non_duplicated_groups.iterrows():
    file_name = row["다운로드 파일"].strip()
    source_file = os.path.join(source_folder, file_name)

    if os.path.exists(source_file) and source_file not in copied_files:
        shutil.copy(source_file, dest_folder_unique)
        copied_files.add(source_file)

# 새로운 엑셀 파일 저장
df_unique = pd.DataFrame([row.to_dict() for row in unique_rows] + non_duplicated_groups.to_dict(orient='records'))
df_duplicates = pd.DataFrame(duplicated_rows)

df_unique.to_excel(output_excel_unique, index=False)
df_duplicates.to_excel(output_excel_duplicates, index=False)

# 중복되지 않은 파일들을 마지막에 옮김
for _, row in df_unique.iterrows():
    file_name = row["다운로드 파일"].strip()
    source_file = os.path.join(source_folder, file_name)

    if os.path.exists(source_file) and source_file not in copied_files:
        shutil.copy(source_file, dest_folder_unique)
        copied_files.add(source_file)

# 새로운 엑셀 파일 저장
df_unique = pd.DataFrame([row.to_dict() for row in unique_rows] + non_duplicated_groups.to_dict(orient='records'))
df_duplicates = pd.DataFrame(duplicated_rows)

df_unique.to_excel(output_excel_unique, index=False)
df_duplicates.to_excel(output_excel_duplicates, index=False)

print("작업 완료!")
