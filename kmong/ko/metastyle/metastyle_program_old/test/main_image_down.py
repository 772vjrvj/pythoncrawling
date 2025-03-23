import os
import pandas as pd
import requests

# CSV 파일 경로와 대상 디렉토리
csv_path = r"D:\GitHub\pythoncrawling\kmong\ko\metastyle\metastyle_program_old\images 2\Men.csv"
dst_dir = r"D:\GitHub\pythoncrawling\kmong\ko\metastyle\metastyle_program_old\images 2\Men"

# CSV 파일 읽기
df = pd.read_csv(csv_path)

# 대상 디렉토리가 없으면 생성
if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

# image_yn 이 'N'인 행들에 대해 image_url 다운로드 수행
for idx, row in df.iterrows():
    if row.get('image_yn', 'N') == 'N':
        image_url = row.get('image_url')
        image_name = row.get('image_name')
        dest_path = os.path.join(dst_dir, image_name)

        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            print(f"다운로드 성공: {image_url} -> {dest_path}")
            # 성공 시 image_yn 값을 "Y"로 업데이트
            df.at[idx, 'image_yn'] = "Y"
        except Exception as e:
            print(f"다운로드 실패: {image_url} - {e}")
            df.at[idx, 'image_yn'] = "N"

# 변경된 내용을 CSV 파일에 덮어쓰기 저장
df.to_csv(csv_path, index=False)
print("CSV 파일 업데이트 완료!")
