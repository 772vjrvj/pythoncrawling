import os
import pandas as pd
import requests
import re

# CSV 파일 경로
csv_file = "Women_Women’s Bottoms_Pants_20250312005644.csv"
output_csv_file = "Women_Women’s Bottoms_Pants_Processed.csv"

# 이미지 저장 폴더
image_folder = "re_images"
os.makedirs(image_folder, exist_ok=True)

# CSV 파일 읽기
df = pd.read_csv(csv_file, dtype=str)

# 'error' 값이 '[Errno 2]' 인 행 필터링
error_rows = df[df['error'].str.contains(r'Invalid URL', na=False)]


def sanitize_filename(text):
    print(f'text : {text}')
    """파일명에서 특수 문자 제거 및 '_'로 변환"""
    if text:
        return re.sub(r'[\\/:*?"<>|]', '_', text)  # 파일명에서 사용할 수 없는 문자 변환
    return text  # 값이 없을 경우 기본값 설정


for index, row in error_rows.iterrows():
    image_url = row['image_url']
    product = row['product']
    product_id = row['product_id']


    product_name = sanitize_filename(product)  # 특수 문자 제거된 파일명
    image_filename = f"{product_name}_{product_id}.jpg"
    image_path = os.path.join(image_folder, image_filename)

    try:
        # 이미지 다운로드
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(image_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            # 데이터프레임 업데이트
            df.at[index, 'image_name'] = image_filename
            df.at[index, 'error'] = ""  # 에러 제거
            df.at[index, 'success'] = "Y"  # 성공 표시
        else:
            print(f"Failed to download {image_url}")

    except requests.RequestException as e:
        print(f"Error downloading {image_url}: {e}")

# 처리된 데이터 저장
df.to_csv(output_csv_file, index=False, encoding='utf-8-sig')

print(f"Processing complete. Updated CSV saved as {output_csv_file}")
