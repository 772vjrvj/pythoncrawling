import pandas as pd
from openpyxl import load_workbook
import os


# 추가해 갈때 사용하기
# 기존 데이터 다음 row부터 추가할때
# 기존 데이터에 10개가 있고 현재
# 배열에 1부터 15까지 진행했다면
# 11부터 ~ 15까지 가져와서 업데이트 할때 사용
def save_to_excel_1(results, file_name, sheet_name='Sheet1'):
    try:
        # 결과 데이터가 비어있는지 확인
        if not results:
            print("결과 데이터가 비어 있습니다.")
            return False

        # 파일이 존재하는지 확인
        if os.path.exists(file_name):
            # 파일이 있으면 기존 데이터 읽어오기
            df_existing = pd.read_excel(file_name, sheet_name=sheet_name, engine='openpyxl')

            # 새로운 데이터를 DataFrame으로 변환
            df_new = pd.DataFrame(results)

            # 기존 데이터의 마지막 행 인덱스를 기준으로 새로운 데이터의 추가 범위 계산
            last_existing_index = df_existing.shape[0]  # 기존 데이터의 행 개수

            # 새로운 데이터에서 추가할 부분만 선택 (기존 데이터 이후의 데이터 부터 시작[10:] index 10부터)
            df_to_add = df_new.iloc[last_existing_index:]

            # 기존 데이터와 추가할 데이터 합치기
            # 전체적으로 0부터 다시 인덱스 부여 ignore_index=True
            df_combined = pd.concat([df_existing, df_to_add], ignore_index=True)

            # 엑셀 파일에 데이터 덧붙이기 (index는 제외)
            with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
                # 기존 파일을 열고, 특정 시트에 데이터를 덧붙임
                df_combined.to_excel(writer, sheet_name=sheet_name, index=False)
            return True  # 엑셀 파일에 성공적으로 덧붙였으면 True 리턴

        else:
            # 파일이 없으면 새로 생성
            df = pd.DataFrame(results)
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            return True  # 새로 생성한 파일에 데이터를 저장했으면 True 리턴

    except Exception as e:
        # 예기치 않은 오류 처리
        print(f'엑셀 에러 발생 발생: {e}')
        return False


def main():
    # 테스트용 데이터
    result = [{'Column1': 1, 'Column2': 'A'}, {'Column1': 2, 'Column2': 'B'}, {'Column1': 3, 'Column2': 'C'}, {'Column1': 4, 'Column2': 'D'},
              {'Column1': 5, 'Column2': 'A'}, {'Column1': 6, 'Column2': 'B'}, {'Column1': 7, 'Column2': 'C'}, {'Column1': 8, 'Column2': 'D'},
              {'Column1': 9, 'Column2': 'A'}, {'Column1': 10, 'Column2': 'B'}, {'Column1': 11, 'Column2': 'C'}, {'Column1': 12, 'Column2': 'D'}
              ]
    file_name = 'text_excel.xlsx'
    success = save_to_excel_1(result, file_name, sheet_name='Sheet1')
    print("엑셀 저장 성공:", success)

if __name__ == "__main__":
    main()
