import os
import shutil
import time

def create_destination_folder(destination_folder):
    """대상 폴더가 없으면 생성하는 함수"""
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f'폴더를 생성했습니다: {destination_folder}')

def move_image_files(source_folder, destination_folder):
    """모든 이미지 파일을 지정된 폴더로 이동하는 함수"""
    # 이미지 확장자 리스트
    # image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.heic']
    # image_extensions = ['.png', '.jpg']
    # image_extensions = ['.webp', '.gif']
    image_extensions = ['.jpeg']

    # os.walk()를 사용하여 소스 폴더 내의 모든 하위 폴더와 파일을 탐색합니다.
    # 이미지 파일 확장자 목록에 따라 파일이 이미지인지 확인합니다.
    # 확인된 이미지 파일을 대상 폴더로 이동합니다.

    for root, dirs, files in os.walk(source_folder):
        for file in files:
            # 파일의 확장자가 이미지 확장자 리스트에 있는지 확인
            if any(file.lower().endswith(ext) for ext in image_extensions):
                source_file_path = os.path.join(root, file)
                destination_file_path = os.path.join(destination_folder, file)

                # 파일 이동
                shutil.move(source_file_path, destination_file_path)
                print(f'파일을 이동했습니다: {source_file_path} -> {destination_file_path}')

def main():
    source_folder = r'D:\cafe24\product'  # 소스 폴더의 경로
    destination_folder = r'D:\cafe24\move_product'  # 모든 이미지 파일을 옮길 폴더

    create_destination_folder(destination_folder)  # 대상 폴더 생성

    start_time = time.time()  # 시작 시간 기록
    print(f'start : {start_time}')
    move_image_files(source_folder, destination_folder)  # 이미지 파일 이동
    end_time = time.time()  # 종료 시간 기록
    print(f'end : {end_time}')

    duration = end_time - start_time
    print(f"모든 이미지 파일을 성공적으로 이동했습니다. 소요 시간: {duration:.2f} 초")

if __name__ == "__main__":
    main()


# 이미지 한 폴더로 이동