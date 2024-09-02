import pandas as pd

# 엑셀 파일 읽기
file_path = '오피스타.xlsx'
업종별_df = pd.read_excel(file_path, sheet_name='업종별')
지역별_df = pd.read_excel(file_path, sheet_name='지역별')

# 두 데이터프레임을 업소번호를 기준으로 병합
merged_df = pd.merge(지역별_df, 업종별_df[['업소번호', '업종']], on='업소번호', how='left')

# 새로운 객체 배열 생성 (DataFrame으로)
# 지역, 업소이름, 업소번호, 업종
final_df = merged_df[['지역', '업소이름', '업소번호', '업종']]

# 업종별로 나누기
업종_리스트 = ['건마', '립카페', '안마', '오피', '유흥주점', '패티쉬', '핸플.키스방', '휴게텔']

# 새 엑셀 파일 생성
with pd.ExcelWriter('업종별_지역별_분류.xlsx') as writer:
    for 업종 in 업종_리스트:
        # 업종별 필터링
        filtered_df = final_df[final_df['업종'] == 업종]

        # 업종 컬럼 제거
        filtered_df = filtered_df[['지역', '업소이름', '업소번호']]

        # 해당 업종 이름으로 시트 생성 및 데이터 저장
        filtered_df.to_excel(writer, sheet_name=업종, index=False)

print("작업이 완료되었습니다. '업종별_지역별_분류.xlsx' 파일이 생성되었습니다.")
