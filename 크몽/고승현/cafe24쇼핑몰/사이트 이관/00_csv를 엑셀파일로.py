import pandas as pd
import os

# 폴더 경로 설정
folder_path = 'A'
output_folder = 'A_converted'  # 변환된 파일을 저장할 폴더

# 출력 폴더가 없으면 생성
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 폴더 내 모든 CSV 파일 순회
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)

        # CSV 파일 읽기
        df = pd.read_csv(file_path)

        # Excel 파일로 저장 (확장자를 .xlsx로 변경)
        excel_filename = filename.replace('.csv', '.xlsx')
        output_path = os.path.join(output_folder, excel_filename)

        # Excel 파일로 저장
        df.to_excel(output_path, index=False)
        print(f"{filename} -> {excel_filename} 변환 완료")

print(f"모든 CSV 파일이 {output_folder} 폴더에 Excel 형식으로 변환되었습니다.")
