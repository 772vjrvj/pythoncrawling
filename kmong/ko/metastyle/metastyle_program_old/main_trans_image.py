import os
import pandas as pd
import shutil

# CSV 파일 경로
csv_path = r"D:\GitHub\pythoncrawling\kmong\ko\metastyle\metastyle_program_old\images 2\Men.csv"

# 소스 및 대상 디렉토리 경로
src_dir = r"D:\GitHub\pythoncrawling\kmong\ko\metastyle\metastyle_program_old\images 2\Men_1"
dst_dir = r"D:\GitHub\pythoncrawling\kmong\ko\metastyle\metastyle_program_old\images 2\Men"

# CSV 파일 읽기
df = pd.read_csv(csv_path)

# 'image_yn' 컬럼을 초기화 (빈 문자열로 초기화)
df['image_yn'] = ""

# 대상 디렉토리가 존재하지 않으면 생성
if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

# 각 이미지 파일 처리
for idx, row in df.iterrows():
    image_name = row['image_name']
    src_path = os.path.join(src_dir, image_name)
    dst_path = os.path.join(dst_dir, image_name)

    try:
        # 소스 파일이 존재하면 이동 처리
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)
            df.at[idx, 'image_yn'] = "Y"
            print(f"Moved: {src_path} -> {dst_path}")
        else:
            df.at[idx, 'image_yn'] = "N"
            print(f"File not found: {src_path}")
    except Exception as e:
        # 예외 발생 시 실패로 처리
        df.at[idx, 'image_yn'] = "N"
        print(f"Error moving {src_path}: {e}")

# 변경된 내용을 CSV 파일에 저장 (덮어쓰기)
df.to_csv(csv_path, index=False)
print("CSV 파일 업데이트 완료!")
