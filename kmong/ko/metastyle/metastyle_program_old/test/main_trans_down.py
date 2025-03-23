import os
import pandas as pd
import requests

def download_missing_images(csv_filename, destination_folder):
    # CSV 파일 읽기
    df = pd.read_csv(csv_filename)

    # 대상 폴더 생성
    os.makedirs(destination_folder, exist_ok=True)

    # trans_yn이 N인 항목들에 대해 이미지 다운로드
    for index, row in df[df['trans_yn'] == 'N'].iterrows():
        image_url = row['image_url']
        image_name = row['image_name']
        destination_path = os.path.join(destination_folder, image_name)

        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(destination_path, 'wb') as file:
                    file.write(response.content)
                df.at[index, 'trans_yn'] = 'Y'
                print(f"Downloaded: {image_url} -> {destination_path}")
            else:
                print(f"Failed to download: {image_url}")
        except Exception as e:
            print(f"Error downloading {image_url}: {e}")

    # 변경된 데이터 저장
    df.to_csv(csv_filename, index=False)

# Boys.csv 작업
download_missing_images("Boys.csv", "Boys")

# Toddler.csv 작업
download_missing_images("Maternity.csv", "Maternity")
