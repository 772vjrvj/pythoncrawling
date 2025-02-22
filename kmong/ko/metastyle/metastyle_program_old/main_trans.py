import os
import shutil
import pandas as pd

def move_images(csv_filename, destination_folder):
    # CSV 파일 읽기
    df = pd.read_csv(csv_filename)

    # 대상 폴더 생성
    os.makedirs(destination_folder, exist_ok=True)

    # 이미지 파일이 있는 폴더 경로
    source_folder = "images"

    # image_name 컬럼에서 파일명 리스트 추출
    df['trans_yn'] = 'N'  # 이동 전 기본값 설정

    # 이미지 이동
    for index, row in df.iterrows():
        image_name = row['image_name']
        source_path = os.path.join(source_folder, image_name)
        destination_path = os.path.join(destination_folder, image_name)

        # 파일이 존재하면 이동
        if os.path.exists(source_path):
            shutil.move(source_path, destination_path)
            df.at[index, 'trans_yn'] = 'Y'
            print(f"Moved: {source_path} -> {destination_path}")
        else:
            print(f"Not found: {source_path}")

    # 변경된 데이터 저장
    df.to_csv(csv_filename, index=False)

# Boys.csv 작업
move_images("Boys.csv", "Boys")

# Toddler.csv 작업
move_images("Toddler.csv", "Toddler")
