import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 엑셀 파일에서 사업자번호와 홈페이지 데이터를 읽어오는 함수
def read_excel(file_path):
    df = pd.read_excel(file_path)
    return df[['사업자번호', '홈페이지']].dropna()

# 이메일 추출을 위한 정규식 패턴 설정
email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

# 홈페이지에서 HTML을 가져와 이메일을 찾는 함수
def find_email_from_website(website_url):
    try:
        # 타임아웃을 10초로 설정
        response = requests.get(website_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        # 정규식으로 이메일 추출
        emails = email_pattern.findall(text)
        print(f"emails found: {emails}")
        return emails[0] if emails else ""
    except requests.exceptions.Timeout:
        print(f"Timeout error while accessing {website_url}")
        return "Timeout"
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {website_url}: {e}")
        return "Request Failed"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Error"

# 이메일 정보를 포함한 사업자 정보를 처리하는 함수
def process_business_info(df):
    business_info_list = []

    for index, row in df.iterrows():
        print(f'Processing index: {index}, 사업자번호: {row["사업자번호"]}')
        business_number = row['사업자번호']
        website = row['홈페이지']
        email = find_email_from_website(website)

        business_info = {
            '사업자번호': business_number,
            '홈페이지': website,
            '이메일': email if email else "이메일 없음"
        }
        business_info_list.append(business_info)

    return pd.DataFrame(business_info_list)

# 결과를 엑셀 파일로 저장하는 함수
def save_to_excel(dataframe, output_file_path):
    dataframe.to_excel(output_file_path, index=False, engine='openpyxl')

# 메인 함수
def main(input_excel, output_excel):
    # 엑셀 데이터 읽기
    df = read_excel(input_excel)
    # 사업자 정보 처리 (이메일 추출)
    result_df = process_business_info(df)
    # 결과를 엑셀로 저장
    save_to_excel(result_df, output_excel)
    print(f"결과가 {output_excel} 파일로 저장되었습니다.")

# 실행
if __name__ == "__main__":
    input_excel = '사업자정보.xlsx'  # 입력 파일 경로
    output_excel = '결과_사업자_이메일.xlsx'  # 출력 파일 경로
    main(input_excel, output_excel)
