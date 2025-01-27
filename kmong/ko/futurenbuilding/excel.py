import pandas as pd

def add_number_column():
    # 엑셀 파일 읽기
    df = pd.read_excel('results_1.xlsx')

    # 새로운 컬럼 추가: 'Number' 컬럼을 생성
    df['Number'] = 0  # 초기값 설정

    # 번호를 부여할 변수
    number = 0

    # 'card' 값이 바뀔 때마다 새로운 번호 부여
    prev_card = None
    for idx, row in df.iterrows():
        current_card = row['CARD']
        if current_card != prev_card:
            # card 값이 달라지면 번호 증가
            number += 1
        df.at[idx, 'Number'] = number
        prev_card = current_card

    # 수정된 데이터를 새로운 엑셀 파일로 저장
    df.to_excel('results_1_with_numbers.xlsx', index=False)

def main():
    # add_number_column 함수 실행
    add_number_column()
    print("엑셀 파일에 번호가 추가되었습니다.")

if __name__ == "__main__":
    main()
