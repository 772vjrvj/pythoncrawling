import pandas as pd

# 엑셀 파일 및 시트명
EXCEL_FILENAME = "prism_data_report.xlsx"
SHEET_NAME = "전체"
OUTPUT_FILENAME = "prism_data_processed.xlsx"

# 엑셀 파일 읽기
df = pd.read_excel(EXCEL_FILENAME, sheet_name=SHEET_NAME, engine="openpyxl")

# 필요한 컬럼만 선택 (사업명, 연구명이 중복 판단 기준)
columns_needed = ["No", "사업명", "연구명"] + [col for col in df.columns if col not in ["No", "사업명", "연구명"]]
df = df[columns_needed]

# 객체 리스트로 변환
data_list = df.to_dict(orient="records")

# 중복된 데이터 저장할 리스트
duplicate_list = []
unique_list = []

# (사업명, 연구명) 기준으로 중복 찾기
grouped = df.groupby(["사업명", "연구명"])

for _, group in grouped:
    if len(group) > 1:  # 중복된 경우
        records = group.to_dict(orient="records")
        duplicate_list.extend(records)  # 모든 중복 데이터 저장
        unique_list.append(records[-1])  # 마지막 데이터만 저장
    else:
        unique_list.append(group.to_dict(orient="records")[0])

# 중복 제거된 데이터프레임
df_unique = pd.DataFrame(unique_list)

# 중복된 데이터 저장용 데이터프레임
df_duplicate = pd.DataFrame(duplicate_list)

# 엑셀 파일로 저장
with pd.ExcelWriter(OUTPUT_FILENAME, engine="openpyxl") as writer:
    df_unique.to_excel(writer, sheet_name="중복제거", index=False)
    df_duplicate.to_excel(writer, sheet_name="중복", index=False)

print(f"중복 제거된 데이터는 '중복제거' 시트에, 중복 데이터는 '중복' 시트에 저장되었습니다. ({OUTPUT_FILENAME})")
