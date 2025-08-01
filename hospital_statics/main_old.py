import requests
import logging
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError,
    HTTPError, URLRequired, SSLError, RequestException
)
from bs4 import BeautifulSoup
import urllib.parse
import urllib3
import pandas as pd
from collections import defaultdict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
cookie = "_wp_uid=1-8ec896e8f0d14c2d2035b1c67a05bf60-s1749051817.518393|windows_10|chrome-1q8ze2x; _gid=GA1.2.1191383243.1749051819; 2a0d2363701f23f8a75028924a3af643=MjE4LjE0Ny4xMzIuMjM2; PHPSESSID=gjv28q1oshgfobk1e0rtlggs71; _gat_gtag_UA_260367900_1=1; _ga_NK0K96SNCZ=GS2.1.s1749129175$o6$g1$t1749130231$j55$l0$h0; _ga=GA1.2.234932638.1749051815; _ga_KHY053XY40=GS2.1.s1749129173$o6$g1$t1749130232$j54$l0$h0"

def request_api(
        method: str,
        url: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        timeout: int = 30,
        verify: bool = True
):
    """
    HTTP 요청을 수행하고 상태 코드, 응답 타입을 자동 처리하여 결과만 반환하는 함수

    :return:
        - JSON 응답일 경우: dict
        - HTML 응답일 경우: str (html)
        - 기타 텍스트 응답일 경우: str
        - 실패 시: None
    """
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json,
            timeout=timeout,
            verify=verify
        )

        response.encoding = 'utf-8'
        response.raise_for_status()  # 4xx, 5xx 응답 시 예외 발생

        # 상태 코드 체크
        if response.status_code != 200:
            logging.error(f"Unexpected status code: {response.status_code}")
            return None

        # Content-Type 판별
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            return response.json()
        elif 'text/html' in content_type or 'application/xhtml+xml' in content_type:
            return response.text
        else:
            return response.text  # 기타 텍스트 형식

    # 예외 처리
    except Timeout:
        logging.error("Request timed out")
    except TooManyRedirects:
        logging.error("Too many redirects")
    except ConnectionError:
        logging.error("Network connection error")
    except HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
    except URLRequired:
        logging.error("A valid URL is required")
    except SSLError:
        logging.error("SSL certificate verification failed")
    except RequestException as e:
        logging.error(f"Request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected exception: {e}")

    return None


# 도메인별 접속자집계
def get_visit_data(fr_date, to_date):
    global cookie

    url = 'https://tongclinic.com/adm/visit_domain.php'

    params = {
        'token': '75bbdca009f82ed3b11d090b913ba113',
        'fr_date': fr_date,
        'to_date': to_date
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": '''_wp_uid=1-8ec896e8f0d14c2d2035b1c67a05bf60-s1749051817.518393|windows_10|chrome-1q8ze2x; _gid=GA1.2.1191383243.1749051819; 2a0d2363701f23f8a75028924a3af643=MjE4LjE0Ny4xMzIuMjM2; PHPSESSID=gjv28q1oshgfobk1e0rtlggs71; _gat_gtag_UA_260367900_1=1; _ga_KHY053XY40=GS2.1.s1749129173$o6$g1$t1749130055$j50$l0$h0; _ga_NK0K96SNCZ=GS2.1.s1749129175$o6$g1$t1749130055$j53$l0$h0; _ga=GA1.2.234932638.1749051815''',
        "Host": "tongclinic.com",
        "If-Modified-Since": "Thu, 05 Jun 2025 13:13:58 GMT",
        "Sec-CH-UA": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    response = request_api('get', url, headers, params, verify=False)

    soup = BeautifulSoup(response, 'html.parser', )

    result = {}
    table_wrap = soup.find("div", class_="tbl_head01 tbl_wrap")
    if table_wrap:
        rows = table_wrap.find("tbody").find_all("tr")
        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 4:
                domain = columns[1].get_text(strip=True)
                count = columns[3].get_text(strip=True)
                if domain and count.isdigit():
                    result[domain] = int(count)

    return result



# 키워드
def extract_keywords_from_pages(fr_date: str, to_date: str):
    global cookie
    base_url = "https://tongclinic.com/adm/visit_list.php"
    keyword_counter = defaultdict(int)
    page = 1

    while True:
        params = {
            'fr_date': fr_date,
            'to_date': to_date,
            'page': page
        }

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'connection': 'keep-alive',
            'cookie': f'{cookie}',
            'host': 'tongclinic.com',
            'referer': f'https://tongclinic.com/adm/visit_list.php?fr_date={fr_date}&to_date={to_date}&page={page}',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }

        html = request_api("GET", base_url, headers=headers, params=params, verify=False)
        if not html:
            print(f"페이지 {page} 요청 실패 또는 응답 없음, 종료")
            break

        soup = BeautifulSoup(html, "html.parser")

        # 종료 조건 체크
        empty_tag = soup.find("td", class_="empty_table")
        if empty_tag and "자료가 없거나" in empty_tag.text:
            print(f"페이지 {page} → 데이터 없음 메시지 확인됨. 종료")
            break

        table_wrap = soup.find("div", class_="tbl_head01 tbl_wrap")
        if not table_wrap:
            print(f"페이지 {page} → 테이블 구조 없음. 종료")
            break

        rows = table_wrap.find("tbody").find_all("tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            a_tag = tds[1].find("a")
            if a_tag:
                text_url = a_tag.get_text(strip=True)
                parsed_url = urllib.parse.urlparse(text_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                for key in ['query', 'q']:
                    if key in query_params:
                        for kw in query_params[key]:
                            keyword = kw.strip()
                            if keyword:
                                keyword_counter[keyword] += 1

        print(f"페이지 {page} 처리 완료")
        page += 1

    return keyword_counter


def save_to_excel(source_data: dict, keyword_data: dict, filename: str = "visit_data.xlsx"):
    # 시트1: 유입 소스/매체
    df1 = pd.DataFrame([
        {"유입 소스/매체": k, "사용자": v}
        for k, v in sorted(source_data.items(), key=lambda x: x[1], reverse=True)
    ])

    # 시트2: 키워드
    df2 = pd.DataFrame([
        {"키워드": k, "사용자": v}
        for k, v in sorted(keyword_data.items(), key=lambda x: x[1], reverse=True)
    ])

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name="유입소스", index=False)
        df2.to_excel(writer, sheet_name="키워드", index=False)

    print(f"\n✅ 엑셀 저장 완료: {filename}")



if __name__ == '__main__':
    fr_date = '2025-04-01'
    to_date = '2025-04-30'

    result = extract_keywords_from_pages(fr_date, to_date)

    data = get_visit_data(fr_date, to_date)
    for domain, count in data.items():
        print(f"{domain} : {count}")



    print("\n[키워드별 방문자 수]")
    for keyword, count in result.items():
        print(f"{keyword} : {count}")

    # 👉 엑셀로 저장
    save_to_excel(data, result)