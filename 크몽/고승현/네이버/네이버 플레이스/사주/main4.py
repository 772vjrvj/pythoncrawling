import pandas as pd

# 엑셀 파일 읽기
file_name = "your_excel_file.xlsx"  # 엑셀 파일 이름
df = pd.read_excel(file_name)

# 전화번호 있는 행과 없는 행을 분리
df_with_phone = df.dropna(subset=['전화번호'])
df_without_phone = df[df['전화번호'].isna()]

# 중복되는 주소를 기준으로 그룹화하여 처리
def process_group(group):
    if len(group) == 1:
        return group
    group_with_phone = group.dropna(subset=['전화번호'])
    if not group_with_phone.empty:
        last_with_phone = group_with_phone.iloc[[-1]]
        return last_with_phone
    else:
        return group.iloc[[-1]]

# 그룹화된 열을 제외한 나머지 열에 대해서만 적용
df_processed_with_phone = df_with_phone.groupby(['주소', '도로명 주소', '상세주소'], group_keys=False).apply(process_group).reset_index(drop=True)
df_processed_without_phone = df_without_phone.groupby(['주소', '도로명 주소', '상세주소'], group_keys=False).apply(process_group).reset_index(drop=True)

# 두 데이터프레임 병합
df_processed = pd.concat([df_processed_with_phone, df_processed_without_phone]).reset_index(drop=True)

# 엑셀 파일로 저장
output_file_name = "processed_" + file_name
df_processed.to_excel(output_file_name, index=False)

print(f"Processed data saved to {output_file_name}")
