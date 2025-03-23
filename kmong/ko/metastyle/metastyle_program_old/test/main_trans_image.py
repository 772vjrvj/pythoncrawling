import os
import shutil
import pandas as pd

# CSV 파일 경로
csv_file = "Women_20250224230007.csv"

# 원본 이미지 폴더 및 대상 폴더 설정
source_folder = "Women"
target_folder = "Women_new"

# 대상 폴더가 없으면 생성
os.makedirs(target_folder, exist_ok=True)

# CSV 파일 읽기
df = pd.read_csv(csv_file)

# 이미지 이동 처리
for index, row in df.iterrows():
    image_name = row["image_name"]
    source_path = os.path.join(source_folder, f"{image_name}.jpg")
    target_path = os.path.join(target_folder, f"{image_name}.jpg")

    # 이미지 파일이 존재하면 이동
    if os.path.exists(source_path):
        try:
            shutil.move(source_path, target_path)  # 이미지 이동
            df.at[index, "image_yn"] = "Y"  # 성공 시 image_yn 업데이트
            print(f"✅ {image_name}.jpg 이동 완료")
        except Exception as e:
            print(f"❌ {image_name}.jpg 이동 오류: {e}")
    else:
        print(f"⚠️ {image_name}.jpg 없음")

# CSV 파일 업데이트
df.to_csv(csv_file, index=False)
print("✅ CSV 파일 업데이트 완료!")
