import pandas as pd

# 엑셀 파일 읽기
product_no_data = pd.read_excel("product_no_data.xlsx")
saphir1612 = pd.read_excel("saphir1612.xlsx")

# product_no를 기준으로 'no' 값 매핑
merged_df = saphir1612.merge(product_no_data[['product_no', 'no']], on='product_no', how='left')

# 엑셀 파일로 저장 (encoding 옵션 제거, openpyxl 엔진 사용)
merged_df.to_excel("merged_saphir1612.xlsx", index=False, engine="openpyxl")

print("✅ Excel file 'merged_saphir1612.xlsx' has been saved.")
