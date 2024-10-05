import requests
import pandas as pd
from bs4 import BeautifulSoup

# 1. POST 요청을 보내는 함수
def post_request(url, headers, payload):
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error: {response.status_code}")
        return None


# 2. HTML에서 우편번호를 추출하는 함수 (th를 가져올 때 에러 발생시 공백 처리)
def extract_zip_code(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='table_list')

    if table:
        tbody = table.find('tbody')
        if tbody:
            first_tr = tbody.find('tr')
            if first_tr:
                try:
                    # 첫 번째 th를 우편번호로 가정
                    zip_code_th = first_tr.find_all('th')[0]
                    return zip_code_th.get_text(strip=True)
                except (IndexError, AttributeError):
                    # 만약 th가 없거나 에러가 발생할 경우 공백으로 처리
                    return ''

    return ''

# 나머지 코드는 동일



# 3. 주소 리스트를 순회하면서 우편번호를 가져오는 함수
def get_zip_codes_for_addresses(address_list):
    url = 'https://www.epost.go.kr/search.RetrieveIntegrationNewZipCdList.comm'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'connection': 'keep-alive',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.epost.go.kr',
        'referer': 'https://www.epost.go.kr/search.RetrieveIntegrationNewZipCdList.comm',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }

    zip_codes = []

    for address in address_list:
        payload = {
            'targetRow': '',
            'srchZipCd': '',
            'srchSido': '',
            'srchSgg': '',
            'srchEmdNm': '',
            'srchRdNm': '',
            'srchRiNm': '',
            'srchEtcNm': '',
            'srchMaSn': '',
            'srchSbSn': '2',
            'srchPoBoxNm': '',
            'srchType': '',
            'keyword_type': '',
            'accessCnt': '1',
            'loginId': 'none',
            'keyword': address
        }

        html_content = post_request(url, headers, payload)
        if html_content:
            zip_code = extract_zip_code(html_content)
            if zip_code:
                zip_codes.append(zip_code)
                print(f'zip_code {zip_code}')
            else:
                zip_codes.append('우편번호 없음')
                print('우편번호 없음')
        else:
            zip_codes.append('요청 실패')

    return zip_codes

# 4. 엑셀 파일을 업데이트하는 함수
def update_excel_with_zip_codes(file_path, address_column, zip_code_column):
    # 엑셀 파일 읽어오기
    df = pd.read_excel(file_path)

    # 주소 리스트 추출
    address_list = df[address_column].tolist()

    # 주소에 해당하는 우편번호 가져오기
    zip_codes = get_zip_codes_for_addresses(address_list)

    # 우편번호 컬럼에 업데이트
    df[zip_code_column] = zip_codes

    # 엑셀 파일로 다시 저장
    df.to_excel(file_path, index=False)
    print(f"우편번호가 '{file_path}'에 업데이트되었습니다.")

# 5. 메인 함수
def main():
    file_path = '우편번호1.xlsx'
    address_column = '주소'  # 주소가 들어 있는 컬럼명
    zip_code_column = '우편번호'  # 업데이트할 우편번호 컬럼명

    # 엑셀 파일 업데이트
    update_excel_with_zip_codes(file_path, address_column, zip_code_column)

if __name__ == '__main__':
    main()
