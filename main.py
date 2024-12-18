import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from datetime import datetime
import pandas as pd


def nytimes_url_request(keyword, page):
    url = f"https://www.koreaherald.com/search/index.php?q={keyword}&sort=1&mode=list&np={page}"

    headers = {
        'authority': 'www.nytimes.com',
        'method': 'GET',
        'path': f'/search?query={keyword}',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'cookie': 'nyt-a=dqz9RORDq3obmFljSqnVWn; _rdt_uuid=1734454507068.795758ed-3957-4fe6-9ca1-0a98b951c53b; _cb=wMVj1BcCOFZDD8hlX; _scid=3De-WLApQzkyPmvzrwKw9dlMetOS4g6_; _scid_r=3De-WLApQzkyPmvzrwKw9dlMetOS4g6_; _gcl_aw=GCL.1734454508.CjwKCAiA34S7BhAtEiwACZzv4RcexVALwhySZe_Pp-Q1TkydoLU_Boz5PckuGNAbSjE2w21P0mJmyRoC2SwQAvD_BwE; _gcl_dc=GCL.1734454508.CjwKCAiA34S7BhAtEiwACZzv4RcexVALwhySZe_Pp-Q1TkydoLU_Boz5PckuGNAbSjE2w21P0mJmyRoC2SwQAvD_BwE; _gcl_gs=2.1.k1$i1734454504$u136575535; _gcl_au=1.1.1522965089.1734454508; nyt-tos-viewed=true; iter_id=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhaWQiOiI2NzYxYWNlYzEyYjFhZWRhOWM5ZDZhODIiLCJjb21wYW55X2lkIjoiNWMwOThiM2QxNjU0YzEwMDAxMmM2OGY5IiwiaWF0IjoxNzM0NDU0NTA4fQ.nHq_23Mq0FxP5xaoXUq2aivQe0XqfeOt8Tw6fNaCQDs; _sctr=1%7C1734447600000; purr-pref-agent=<G_<C_<T0<Tp1_<Tp2_<Tp3_<Tp4_<Tp7_<a12; purr-cache=<G_<C_<T0<Tp1_<Tp2_<Tp3_<Tp4_<Tp7_<a0_<K0<S0<r<ua; nyt-purr=cfhhcfhhhukfhufhhgah2f; NYT-Edition=edition|INTERNATIONAL; _v__chartbeat3=BiUqTnqzIHADSB0Y3; nyt-gdpr=0; nyt-traceid=(null); __gads=ID=c130c981128e3bda:T=1734454525:RT=1734545426:S=ALNI_MYAflfaIG96yhwa8MlcMXvwgukWTQ; __gpi=UID=00000fa94d5e90f9:T=1734454525:RT=1734545426:S=ALNI_MZizmb5mbB_elVQ26iCZGb9UbO-eQ; __eoi=ID=db9171052c67e12e:T=1734454525:RT=1734545426:S=AA-AfjaKu1WtJR3ksF9Ll9vhSSOT; _cb_svref=https%3A%2F%2Fwww.google.com%2F; nyt-jkidd=uid=0&lastRequest=1734545606900&activeDays=%5B0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C1%2C1%5D&adv=2&a7dv=2&a14dv=2&a21dv=2&lastKnownType=anon&newsStartDate=&entitlements=; _chartbeat2=.1734454507093.1734545610427.11.CQSMnnCxVdV8CEhO-4IgivkDuzki4.2; datadome=LSROKNAun9tK~jxHsyg0KssWWIPuChXvC2_hpXtFL8Rc6JVOmegUkpseEQIkTZq~d9g9QTT8nTfcilJZa5G0R9_jXn47fkArhyxMokgPaHecGXwFuF7NYMbLyYx4YI4j; _dd_s=rum=0&expire=1734546530973',
        'if-modified-since': 'Wed, 18 Dec 2024 18:13:25 GMT',
        'priority': 'u=0, i',
        'referer': 'https://www.nytimes.com/',
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



def nytimes_url_request_html():
    # 파일 경로 설정 (프로그램 실행 경로에서 'ny_President.html' 파일을 읽음)
    file_path = 'ny_President.html'

    try:
        # 파일을 읽어서 내용을 반환
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"파일 '{file_path}'을(를) 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        return None


def get_nytimes_url(html, main_url, keyword):
    url_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('ol', {'data-testid': 'search-results'}) if soup else None

        if not board_list:
            logging.error("Board list not found")
            return []

        for index, li in enumerate(board_list.find_all('li', recursive=False)):
            obj = {
                'NEWS': 'The New York Times',
                '키워드': keyword,
                'URL': '',
                'DATE': '',
                'TITLE': '',
                'CONTENT': ''
            }
            news_link = li.find('a')
            if news_link:
                news_link_href = news_link['href'] if 'href' in news_link.attrs else None
                if news_link_href:
                    obj['URL'] = f'{main_url}{news_link_href}'

                    # 정규 표현식 패턴: URL에서 'YYYYMMDD' 형식의 날짜를 추출
                    pattern = r'(\d{4})/(\d{2})/(\d{2})'

                    # 정규 표현식에 맞는 날짜 부분을 찾습니다.
                    match = re.search(pattern, news_link_href)

                    if match:
                        # 날짜를 'YYYYMMDD' 형식으로 추출
                        extracted_date = match.group(1) + match.group(2) + match.group(3)
                        obj['DATE'] = extracted_date
                        print(f'obj : {obj}')
                        url_list.append(obj)
                    else:
                        print("날짜를 찾을 수 없습니다.")

    except Exception as e:
        logging.error(f"Error during scraping: {e}")

    return url_list


def nytimes_detail_request(url):

    headers = {
        'authority': 'www.nytimes.com',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'cookie': 'nyt-a=dqz9RORDq3obmFljSqnVWn; _cb=wMVj1BcCOFZDD8hlX; _scid=3De-WLApQzkyPmvzrwKw9dlMetOS4g6_; _gcl_aw=GCL.1734454508.CjwKCAiA34S7BhAtEiwACZzv4RcexVALwhySZe_Pp-Q1TkydoLU_Boz5PckuGNAbSjE2w21P0mJmyRoC2SwQAvD_BwE; _gcl_dc=GCL.1734454508.CjwKCAiA34S7BhAtEiwACZzv4RcexVALwhySZe_Pp-Q1TkydoLU_Boz5PckuGNAbSjE2w21P0mJmyRoC2SwQAvD_BwE; _gcl_gs=2.1.k1$i1734454504$u136575535; _gcl_au=1.1.1522965089.1734454508; nyt-tos-viewed=true; _sctr=1%7C1734447600000; purr-pref-agent=<G_<C_<T0<Tp1_<Tp2_<Tp3_<Tp4_<Tp7_<a12; nyt-purr=cfhhcfhhhukfhufhhgah2f; NYT-Edition=edition|INTERNATIONAL; _v__chartbeat3=BiUqTnqzIHADSB0Y3; nyt-gdpr=0; nyt-traceid=(null); nyt-geo=KR; nyt-us=0; purr-cache=<G_<C_<T0<Tp1_<Tp2_<Tp3_<Tp4_<Tp7_<a0_<K0<S0<r<ur; NYT-MPS=0000000c4d24e06130396476d219bb5646f99281f7ac3f1dd71040a544c499dd18a04ef9a206aa9c70cb4fa2fcdf6d680e35718f660a42d849e42f0097cbc0; nyt-auth-method=sso; _rdt_uuid=1734454507068.795758ed-3957-4fe6-9ca1-0a98b951c53b; _scid_r=5be-WLApQzkyPmvzrwKw9dlMetOS4g6_avrNNA; _fbp=fb.1.1734548013142.61723261818017971; RT="z=1&dm=nytimes.com&si=857507fa-df42-448f-9c64-a28c77944dcf&ss=m4u93atl&sl=2&tt=4ul&bcn=%2F%2F684d0d4a.akstat.io%2F&ld=ac5&ul=fc5&hd=fca"; regi_cookie=; iter_id=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhaWQiOiI2NzYxYWNlYzEyYjFhZWRhOWM5ZDZhODIiLCJhaWRfZXh0Ijp0cnVlLCJjb21wYW55X2lkIjoiNWMwOThiM2QxNjU0YzEwMDAxMmM2OGY5IiwiaWF0IjoxNzM0NTQ4MDIyfQ.4ais0i9gzLbdq-MaZxnXv4pfpIiQ7uIDPQhh8WhHhAk; _cb_svref=external; __gads=ID=c130c981128e3bda:T=1734454525:RT=1734548692:S=ALNI_MYAflfaIG96yhwa8MlcMXvwgukWTQ; __gpi=UID=00000fa94d5e90f9:T=1734454525:RT=1734548692:S=ALNI_MZizmb5mbB_elVQ26iCZGb9UbO-eQ; __eoi=ID=db9171052c67e12e:T=1734454525:RT=1734548692:S=AA-AfjaKu1WtJR3ksF9Ll9vhSSOT; SIDNY=CBoSLgimtIy7BhC4u4y7BhoSMS2P3bZOxndksdqyYxDp9GkKIMe6uIABOKW0jLsGQgAaQLHK3ilw1hC215APyV-bq7mYLTX4UEXouJmVayEiNc-oO1AQqHjmOr3VWCei_Yv5_f5bnqlbmD-Cl0SAU9i7iww=; NYT-S=0^CBoSLgimtIy7BhC4u4y7BhoSMS2P3bZOxndksdqyYxDp9GkKIMe6uIABOKW0jLsGQgAaQLHK3ilw1hC215APyV-bq7mYLTX4UEXouJmVayEiNc-oO1AQqHjmOr3VWCei_Yv5_f5bnqlbmD-Cl0SAU9i7iww=; nyt.et.dd=iv=3C5B0F4E0E8B47D4812925E67EDB6ACF&val=jdZlUCUTvaY+yTqkEwlmhqpM3swomVOFJoD0mo5zwZqxwIsT03OUC9FLxMer9UJtTqlwKUqLzldN9xY7GGF7022z3JAMQgvdRilxEsUJX5jx/5/185GY7f9psiWAsAm61f8BySoW6lvBs7cyNE3S+R4duuF4RklDtYoJr6CDfNfj+ad+Xpz/OycScsTjMOk+9q9hejNdv4NX08nTDjXcCsvpztfIzNuFI1SRAR7ZVYA=; nyt-jkidd=uid=269360455&lastRequest=1734548807930&activeDays=%5B0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C1%2C1%5D&adv=2&a7dv=2&a14dv=2&a21dv=2&lastKnownType=regi&newsStartDate=&entitlements=; datadome=hE9kih6CAHFE2LUS10AXWUtdzsT0usfmGdAh1gk7IMay8hxwY4Cakf7evIMIw0qsbCEbyT_wDAqwTLsgyDn6bVsiUW43INBIWwfQGbW1CuNDSMZF3Li79D4bXt9PjtSa; _chartbeat2=.1734454507093.1734548814126.11.wG_zvBcuBVVPHVd7CIAGLFCJ7T8C.4; _chartbeat5=; _dd_s=rum=0&expire=1734549708899',
        'if-modified-since': 'Wed, 18 Dec 2024 18:53:37 GMT',
        'priority': 'u=0, i',
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


def get_nytimes_detail(html, data):

    try:
        soup = BeautifulSoup(html, 'html.parser')
        news_content = soup.find('section', {'name': 'articleBody'}) if soup else None

        if not news_content:
            logging.error("news_content not found")
            return data

        data['CONTENT'] = news_content.get_text(strip=True)

        news_title = soup.find('h1', {'data-testid': 'headline'}) if soup else None
        data['TITLE'] = news_title.get_text(strip=True) if news_title else ''

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
    main_url = 'https://www.nytimes.com'
    html = nytimes_url_request_html()
    if html:
        url_list = get_nytimes_url(html, main_url, keyword)

        all_data_list.extend(url_list)
    print(f'all_data_list : {all_data_list}')

    all_result_list = []
    for idx, data in enumerate(all_data_list, start=1):
        html = nytimes_detail_request(data['URL'])
        time.sleep(random.uniform(1, 2))
        result = get_nytimes_detail(html, data)
        print(f'result : {result}')
        all_result_list.append(result)

    save_to_excel(all_result_list)


if __name__ == '__main__':
    main()