import pandas as pd

# A와 B 엑셀 파일 경로
a_excel_path = '유튜브+링크+정리 필터.xlsx'
b_excel_path = '유튜브+링크+정리 종합.xlsx'

# 엑셀 파일 읽기
df_a = pd.read_excel(a_excel_path)
df_b = pd.read_excel(b_excel_path)

# 데이터 매핑 및 업데이트
url_to_update_date = dict(zip(df_a['URL'], df_a['최신 업데이트 일']))

# B의 '최신 업데이트 일' 컬럼 업데이트
df_b['최신 업데이트 일'] = df_b['URL'].map(url_to_update_date).fillna(df_b['최신 업데이트 일'])

# 결과를 B 엑셀 파일에 직접 저장
df_b.to_excel(b_excel_path, index=False)

print(f"B 엑셀 파일이 업데이트되었습니다: {b_excel_path}")