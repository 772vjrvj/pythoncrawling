import os

# 이미지 파일이 있는 디렉터리 경로
directory_path = "inven_image_list"

# 디렉터리 내의 파일 이름 변경
for filename in os.listdir(directory_path):
    # 파일 이름에 "초"가 있는 경우만 처리
    if "초" in filename:
        # 새 파일 이름 생성
        new_filename = filename.replace("초", "분")

        # 파일의 전체 경로
        old_file_path = os.path.join(directory_path, filename)
        new_file_path = os.path.join(directory_path, new_filename)

        # 파일 이름 변경
        os.rename(old_file_path, new_file_path)
        print(f"Renamed: {filename} -> {new_filename}")
