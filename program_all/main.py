import pandas as pd

# 파일 읽기 (한글 인코딩 고려)
df = pd.read_csv("리플 최종.csv", encoding='utf-8')  # 또는 encoding='cp949'

# SHOP_ID 앞에 'V_' 붙이기
df['SHOP_ID'] = df['SHOP_ID'].astype(str).apply(lambda x: f'V_{x}')

# CSV 저장 (한글 인코딩 설정)
df.to_csv("리플 최종_V.csv", index=False, encoding='utf-8-sig')
