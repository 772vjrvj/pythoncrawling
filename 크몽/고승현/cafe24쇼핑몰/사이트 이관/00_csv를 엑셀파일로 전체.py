import os
import pandas as pd

def convert_csv_to_xlsx_with_structure(folder_path, output_folder):
    # 폴더를 순회하면서 모든 파일과 폴더를 탐색
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith('.csv'):
                # CSV 파일 경로
                file_path = os.path.join(root, filename)

                # 출력 폴더 내 동일한 디렉토리 구조를 생성
                relative_path = os.path.relpath(root, folder_path)
                target_dir = os.path.join(output_folder, relative_path)
                os.makedirs(target_dir, exist_ok=True)

                # 변환할 XLSX 파일 경로 지정
                excel_filename = filename.replace('.csv', '.xlsx')
                output_path = os.path.join(target_dir, excel_filename)

                # CSV 파일을 읽고 XLSX 파일로 저장
                df = pd.read_csv(file_path)
                df.to_excel(output_path, index=False)
                print(f"{file_path} -> {output_path} 변환 완료")

# 예시 사용법
folder_path = '상세이미지정보추가_상품취합'  # 변환할 CSV 파일이 포함된 폴더
output_folder = '변환된_엑셀파일'  # XLSX 파일을 저장할 폴더

# 결과를 저장할 폴더가 없는 경우 생성
os.makedirs(output_folder, exist_ok=True)

# 변환 함수 실행
convert_csv_to_xlsx_with_structure(folder_path, output_folder)
