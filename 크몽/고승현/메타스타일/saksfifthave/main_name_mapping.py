import os
import pandas as pd

# 엑셀 파일 불러오기
excel_file = 'products.xlsx'
df = pd.read_excel(excel_file)

# productId 컬럼이 있는지 확인
if 'productId' not in df.columns:
    raise ValueError('엑셀 파일에 productId 컬럼이 없습니다.')

# metastyle 폴더 경로
metastyle_dir = 'metastyle'

# page 번호를 담을 리스트
page_numbers = []

# metastyle 폴더 내의 page_1, page_2, ... 폴더 순회
for page_folder in os.listdir(metastyle_dir):
    # page_n 형식의 폴더만 처리
    if page_folder.startswith('page_'):
        page_num = int(page_folder.split('_')[1])  # page 번호 추출
        page_path = os.path.join(metastyle_dir, page_folder)

        # 각 page 폴더 내의 ID 폴더 순회
        for id_folder in os.listdir(page_path):
            id_path = os.path.join(page_path, id_folder)

            # 폴더 이름이 ID로 되어 있는지 확인
            if os.path.isdir(id_path) and id_folder.isdigit():
                # 해당 ID가 엑셀의 productId에 존재하는지 확인
                if id_folder in df['productId'].astype(str).values:
                    # 존재하면 page 번호를 추가
                    df.loc[df['productId'] == int(id_folder), 'page'] = page_num

# 엑셀 파일에 page 컬럼 추가 후 저장
df.to_excel('updated_products.xlsx', index=False)
print('page 번호가 추가된 엑셀 파일을 저장했습니다.')
