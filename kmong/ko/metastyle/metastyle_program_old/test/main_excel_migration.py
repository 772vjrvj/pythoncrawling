import os
import pandas as pd

# 엑셀 파일이 위치한 경로
input_directory = r"D:\GitHub\pythoncrawling\kmong\ko\metastyle\metastyle_program\dist\metastyle_program"
# 통합된 엑셀 파일 저장 경로
output_file = os.path.join(input_directory, "combined_excel.xlsx")

# 엑셀 파일 읽기 및 통합
def combine_excel_files(input_dir, output_file):
    all_data = []
    # 디렉토리 내 모든 파일 검색
    for file in os.listdir(input_dir):
        if file.endswith(".xlsx") or file.endswith(".xls"):
            file_path = os.path.join(input_dir, file)
            # 엑셀 파일 읽기
            try:
                df = pd.read_excel(file_path)
                df['Source_File'] = file  # 원본 파일명 기록 (옵션)
                all_data.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")

    # 데이터프레임 합치기
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # 통합된 엑셀 저장
        combined_df.to_excel(output_file, index=False)
        print(f"All files combined into {output_file}")
    else:
        print("No Excel files found in the directory.")

# 함수 실행
combine_excel_files(input_directory, output_file)
