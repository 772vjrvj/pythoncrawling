import os
import shutil

def create_destination_folder(destination_folder):
    """대상 폴더가 없으면 생성하는 함수"""
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f'폴더를 생성했습니다: {destination_folder}')

def copy_csv_files(source_folder, destination_folder):
    """모든 CSV 파일을 지정된 폴더로 복사하는 함수"""
    for first_level_folder in os.listdir(source_folder):
        first_level_path = os.path.join(source_folder, first_level_folder)

        if os.path.isdir(first_level_path):  # 1차 폴더 확인
            # 1차 폴더에 CSV 파일이 있는지 확인
            csv_files_in_first_level = [file for file in os.listdir(first_level_path) if file.endswith('.csv')]
            if csv_files_in_first_level:
                # 1차 폴더에서 CSV 파일 복사
                for file in csv_files_in_first_level:
                    source_file_path = os.path.join(first_level_path, file)
                    new_file_name = f'{first_level_folder}.csv'  # 새로운 파일 이름
                    destination_file_path = os.path.join(destination_folder, new_file_name)
                    shutil.copy(source_file_path, destination_file_path)
                    print(f'파일을 복사했습니다: {source_file_path} -> {destination_file_path}')
            else:
                # 1차 폴더에 CSV 파일이 없고 2차 폴더가 있는 경우
                for second_level_folder in os.listdir(first_level_path):
                    second_level_path = os.path.join(first_level_path, second_level_folder)

                    if os.path.isdir(second_level_path):  # 2차 폴더 확인
                        for file in os.listdir(second_level_path):
                            if file.endswith('.csv'):
                                source_file_path = os.path.join(second_level_path, file)
                                new_file_name = f'{first_level_folder}_{second_level_folder}.csv'  # 1차 폴더 이름을 접두사로 추가
                                destination_file_path = os.path.join(destination_folder, new_file_name)
                                shutil.copy(source_file_path, destination_file_path)
                                print(f'파일을 복사했습니다: {source_file_path} -> {destination_file_path}')

def main():
    source_folder = '카페24_상품자료'  # 1차 폴더의 경로
    destination_folder = '모든_csv파일'  # 모든 CSV 파일을 옮길 폴더

    create_destination_folder(destination_folder)  # 대상 폴더 생성
    copy_csv_files(source_folder, destination_folder)  # CSV 파일 복사

    print("모든 CSV 파일을 성공적으로 이동했습니다.")

if __name__ == "__main__":
    main()
