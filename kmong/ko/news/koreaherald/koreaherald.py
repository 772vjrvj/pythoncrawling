import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from datetime import datetime
import pandas as pd


def koreaherald_url_request(keyword, page):
    url = f"https://www.koreaherald.com/search/index.php?q={keyword}&sort=1&mode=list&np={page}"

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'connection': 'keep-alive',
        'cookie': '_fwb=218n6hHTmvvgZITA57vJx0B.1734454346369; ACEFCID=UID-6761AC4ADF6512949BE766BD; _ynx153=1734454346; _gid=GA1.2.348498055.1734454347; _sas_id.04.5078=fa337660ca201927.1734454347.; kh_f=null; kh_lh=null; _ss_pp_id=595c54b54406e83779a1725507417205; _lr_geo_location=KR; _lr_env_src_ats=false; __qca=P0-140865564-1734454439350; _sas_ses.04.5078=1; __gads=ID=4df40ac2bd0cb893:T=1734454436:RT=1734539433:S=ALNI_Mb6dSFydb9h2mtN9t-NNCW75ygFog; __gpi=UID=00000fa94bb7f9e1:T=1734454436:RT=1734539433:S=ALNI_MYi4Q5SMiLZia-VWKTLKzkbIhlM6A; __eoi=ID=9e51efb77ceca2dc:T=1734454436:RT=1734539433:S=AA-AfjbGpQXDfcvChcMJ8Ggsnfdj; _lr_retry_request=true; _gat_gtag_UA_127230343_1=1; _td=31dac392-9799-40f3-a235-0c54664fa0fa; wcs_bt=c7749f754cfc38:1734539499; _ga=GA1.2.314102202.1734454347; cto_bundle=NWlYKV9oYmRtUnRRc0hXVSUyRjhqUno5MkJLYjZobjVOZ2hFYlJ5djJ0cUV1YU4xSUJOaSUyQlZaJTJGWE9JQTFLOW1OVUFRTzExczJ1aWxCTlB4OTdEY1h1TmxFWDAxUUJKUUtGWmJYaU4lMkJiJTJGRnU3anExVTBWWHZPcU90SFdLa2RYRUVxb0lHbEZMSlR4MHRFN2ZYd0FBTFFNaVJsNDlKczZkJTJGJTJGUklXZGRHUkxsRGE1c1JnN1BvRlVvUjlSaE5yZ2x5JTJGazNNa2Jnb2dDWkJUeGdCUW1rZmR1JTJCMWUxVjBBJTNEJTNE; cto_bidid=ZVv6EF9kc2dBNUZaMFN4aXluZ0xjRWxTMzdZZU9jWEJIb3lOSlRTTTlKMDlVUjZjdm5zeXBaOGdVS21DbU9kQzNRbmRQYXd0QTZzcU1USG9kTjFIR0FjV044SVBqY1B3JTJCOXVZbjJUZ3NzdHVpdXZRJTNE; _ga_H1P87EFV70=GS1.1.1734539321.2.1.1734539503.0.0.0; _ga_K4JZJD1VS2=GS1.1.1734539321.2.1.1734539503.0.0.0; _ga_S0CBW8XMP5=GS1.1.1734539321.2.1.1734539504.36.0.0',
        'host': 'www.koreaherald.com',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    # GET 요청
    try:
        # HTTP GET 요청
        response = requests.get(url, headers=headers)

        # 요청이 성공적인 경우
        response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 중 오류 발생: {e}")
        return None



def get_koreaherald_url(html, main_url, keyword):
    url_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('ul', class_='sub_content_list') if soup else None

        if not board_list:
            logging.error("Board list not found")
            return []

        for index, li in enumerate(board_list.find_all('li', recursive=False)):
            obj = {
                'NEWS': 'The Korea Herald',
                '키워드': keyword,
                'URL': '',
                'DATE': '',
                'TITLE': '',
                'CONTENT': ''
            }
            news_link = li.find('a', class_='news_link')
            if news_link:
                news_link_href = news_link['href'] if 'href' in news_link.attrs else None
                if news_link_href:
                    obj['URL'] = f'{main_url}{news_link_href}'

                    match = re.search(r'ud=(\d{8})', news_link_href)
                    if match:
                        date_str = match.group(1)  # 추출된 날짜 (yyyymmdd)
                        obj['DATE'] = date_str  # 날짜 값 저장

            print(f'obj : {obj}')
            url_list.append(obj)

    except Exception as e:
        logging.error(f"Error during scraping: {e}")

    return url_list


def koreaherald_detail_request(url):

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'connection': 'keep-alive',
        'host': 'www.koreaherald.com',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    # GET 요청
    try:
        # HTTP GET 요청
        response = requests.get(url, headers=headers)

        # 요청이 성공적인 경우
        response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 중 오류 발생: {e}")
        return None

def get_koreaherald_detail(html, data):

    try:
        soup = BeautifulSoup(html, 'html.parser')
        news_content = soup.find('div', class_='news_content') if soup else None

        if not news_content:
            logging.error("news_content not found")
            return data

        news_title_area = news_content.find('div', class_='news_title_area')
        if news_title_area:
            news_title = news_title_area.find('h1', class_='news_title')
            data['TITLE'] = news_title.get_text(strip=True) if news_title else ''

        news_text_area = news_content.find('div', class_='news_text_area')
        data['CONTENT'] = news_text_area.get_text(strip=True) if news_text_area else ''

    except Exception as e:
        logging.error(f"Error during scraping: {e}")

    return data


def save_to_excel(results):

    # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    # 파일 이름 설정
    file_name = f"신문_{current_time}.xlsx"

    try:
        # 파일이 없으면 새로 생성
        df = pd.DataFrame(results)

        # 엑셀 파일 저장
        df.to_excel(file_name, index=False)

    except Exception as e:
        # 예기치 않은 오류 처리
        logging.error(f"엑셀 저장 실패: {e}")


def main():

    all_data_list = []

    keyword = 'South Korea’s President'
    main_url = 'https://www.koreaherald.com'
    for page in range(1, 2):
        html = koreaherald_url_request(keyword, page)
        time.sleep(random.uniform(1, 2))
        if html:
            url_list = get_koreaherald_url(html, main_url, keyword)
            print(f'page : {page}, data_list {len(url_list)}')

            all_data_list.extend(url_list)

    all_result_list = []
    for idx, data in enumerate(all_data_list, start=1):
        if idx > 2:
            break
        html = koreaherald_detail_request(data['URL'])
        time.sleep(random.uniform(1, 2))
        result = get_koreaherald_detail(html, data)
        print(f'result : {result}')
        all_result_list.append(result)

    save_to_excel(all_result_list)


if __name__ == '__main__':
    main()