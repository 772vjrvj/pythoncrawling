import pandas as pd

def split_excel_file(input_file, rows_per_file=1000):
    # 입력 파일을 로드합니다.
    df = pd.read_excel(input_file)

    # 총 row 개수를 계산하고 필요한 파일 개수를 계산합니다.
    total_rows = len(df)
    total_files = (total_rows + rows_per_file - 1) // rows_per_file

    for i in range(total_files):
        # 시작과 끝 row 인덱스를 계산합니다.
        start_row = i * rows_per_file
        end_row = start_row + rows_per_file

        # 청크 데이터를 추출하여 새로운 엑셀 파일로 저장합니다.
        chunk_df = df.iloc[start_row:end_row]
        output_file = f'제품정보_part_{i+1}.xlsx'
        chunk_df.to_excel(output_file, index=False)

        print(f"{output_file} 파일이 생성되었습니다.")

# 사용 예시
split_excel_file("제품정보_241029.xlsx", rows_per_file=1000)
