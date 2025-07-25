import pandas as pd

# 파일 경로
vip_path = 'vip 최종_추가됨.xlsx'
nabi_path = '나비야넷 최종_추가됨.xlsx'
output_path = '매핑결과_최종3.xlsx'

# 데이터 로딩
vip_df = pd.read_excel(vip_path)
nabi_df = pd.read_excel(nabi_path)

# 결과 저장용 리스트
result_rows = []

# 나비야넷에서 매핑된 인덱스 추적
mapped_nabi_indexes = set()

# vip 기준 매핑
for _, vip_row in vip_df.iterrows():
    vip_name_nm = str(vip_row.get('SHOP_NAME_NM', '')).strip()
    vip_loc = str(vip_row.get('SHOP_NAME_LOC', '')).strip()

    matched = nabi_df[
        nabi_df['SHOP_NAME_NM'].astype(str).str.contains(vip_name_nm, na=False, regex=False) &
        nabi_df['SHOP_NAME_LOC'].astype(str).str.contains(vip_loc, na=False, regex=False)
        ]

    if not matched.empty:
        for seq, (_, nabi_row) in enumerate(matched.iterrows(), start=1):
            combined = vip_row.copy()
            combined['LATITUDE'] = nabi_row.get('LATITUDE')
            combined['LONGITUDE'] = nabi_row.get('LONGITUDE')
            combined['SHOP_REAL_PHONE'] = nabi_row.get('SHOP_PHONE')  # 나비야넷의 번호
            combined['SHOP_NAME_TWO'] = nabi_row.get('SHOP_NAME')
            combined['MAPPING_YN'] = 'Y'
            combined['SEQ'] = seq
            result_rows.append(combined)

            mapped_nabi_indexes.add(nabi_row.name)
    else:
        no_match = vip_row.copy()
        no_match['LATITUDE'] = None
        no_match['LONGITUDE'] = None
        no_match['SHOP_REAL_PHONE'] = vip_row.get('SHOP_PHONE')
        no_match['SHOP_NAME_TWO'] = ''
        no_match['MAPPING_YN'] = 'N'
        no_match['SEQ'] = 1
        result_rows.append(no_match)

# 매핑되지 않은 나비야넷 데이터 추가
for idx, nabi_row in nabi_df.iterrows():
    if idx not in mapped_nabi_indexes:
        nabi_copy = nabi_row.copy()
        nabi_copy['SHOP_REAL_PHONE'] = None
        nabi_copy['SHOP_NAME_TWO'] = ''
        nabi_copy['MAPPING_YN'] = 'N'
        nabi_copy['SEQ'] = 1
        result_rows.append(nabi_copy)

# 결과 DataFrame 생성
result_df = pd.DataFrame(result_rows)

# 엑셀 저장
result_df.to_excel(output_path, index=False)
print(f"✅ 최종 결과 저장 완료: {output_path}")
