import pandas as pd

# 파일 읽기
df = pd.read_excel('vipinfo_all.xlsx')

# 결과 리스트
result_list = []

# SHOP_ID로 그룹화
grouped = df.groupby('SHOP_ID')

for shop_id, group in grouped:
    # 각 그룹의 MAIN_CATEGORY를 추출하고 중복 제거
    categories = group['MAIN_CATEGORY'].dropna().unique()
    merged_category = ", ".join(categories)

    # 첫 번째 행을 복사
    first_row = group.iloc[0].copy()

    # MAIN_CATEGORY를 병합된 값으로 대체
    first_row['MAIN_CATEGORY'] = merged_category

    # 결과 리스트에 추가
    result_list.append(first_row)

# 결과를 데이터프레임으로 변환
result_df = pd.DataFrame(result_list)

# 엑셀로 저장
result_df.to_excel('vipinfo_grouped_result.xlsx', index=False)

print("✅ vipinfo_grouped_result.xlsx 생성 완료.")
