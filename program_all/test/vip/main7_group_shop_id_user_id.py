import pandas as pd

# 엑셀 읽기
df = pd.read_excel('vipinfo_grouped_result.xlsx')

# 전화번호별 등장 횟수
phone_counts = df['전화번호'].value_counts()

# USER_ID 및 PARENT_SHOP_ID 매핑용
user_id_map = {}
parent_id_map = {}
user_ids = []
parent_shop_ids = []

user_counter = 1

for idx, row in df.iterrows():
    phone = row['전화번호']
    shop_id = row['SHOP_ID']  # 기존 고유 ID

    # USER_ID 부여
    if phone not in user_id_map:
        user_id_map[phone] = f"user{user_counter}"
        user_counter += 1
    user_ids.append(user_id_map[phone])

    # PARENT_SHOP_ID 부여 (2건 이상인 경우만)
    if phone_counts[phone] > 1:
        if phone not in parent_id_map:
            # 이 전화번호에 해당하는 첫 SHOP_ID를 대표로 지정
            parent_id_map[phone] = shop_id
        parent_shop_ids.append(parent_id_map[phone])
    else:
        parent_shop_ids.append('')  # 단독 전화번호는 빈 문자열

# 컬럼 추가
df['USER_ID'] = user_ids
df['GROUP_SHOP_ID'] = parent_shop_ids

# 저장
df.to_excel('vipinfo_with_user_and_parent.xlsx', index=False)

print("✅ USER_ID + PARENT_SHOP_ID 부여 완료 → vipinfo_with_user_and_parent.xlsx 저장됨")
