import os
import shutil

# 이미지 파일들이 들어있는 상위 폴더 (page_1, page_2 폴더가 있는 곳)
root_dir = "metastyle"
# 이미지 파일을 이동할 목적지 폴더
destination_dir = os.path.join(root_dir)

# page_1, page_2 같은 폴더를 순회
for folder in os.listdir(root_dir):
    folder_path = os.path.join(root_dir, folder)

    if os.path.isdir(folder_path):  # page 폴더라면
        for subfolder in os.listdir(folder_path):
            subfolder_path = os.path.join(folder_path, subfolder)

            if os.path.isdir(subfolder_path):  # ID 폴더라면
                for file in os.listdir(subfolder_path):
                    file_path = os.path.join(subfolder_path, file)

                    # 파일을 목적지 폴더로 이동할 때 이미 존재하는지 확인
                    destination_file_path = os.path.join(destination_dir, file)
                    if not os.path.exists(destination_file_path):  # 파일이 존재하지 않으면 이동
                        shutil.move(file_path, destination_dir)
                        print(f"Moved {file} to {destination_dir}")
                    else:
                        print(f"Skipped {file}, already exists in {destination_dir}")
