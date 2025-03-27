import requests
import logging
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError,
    HTTPError, URLRequired, SSLError, RequestException
)
from bs4 import BeautifulSoup
import pandas as pd


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



def get_visit_data():

    url = 'https://tongclinic.com/adm/visit_domain.php'

    params = {
        'token': '445e998fa87d2cf72851ad4da236fff9',
        'fr_date': '2025-03-27',
        'to_date': '2025-03-27'
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'cookie': 'PHPSESSID=6m12a4lj859oltalncrcjkcvo7; 2a0d2363701f23f8a75028924a3af643=MjE4LjE0Ny4xMzIuMjM2; _wp_uid=1-f67b8bb75e7902906eaa59bb3de4ce1d-s1743076908.989433|windows_10|chrome-1g5xrb6; _gid=GA1.2.151252856.1743076911; _ga_NK0K96SNCZ=GS1.1.1743076910.1.1.1743078261.0.0.0; _ga=GA1.2.1319948639.1743076910; _ga_KHY053XY40=GS1.1.1743076910.1.1.1743078333.0.0.0',
        'host': 'tongclinic.com',
        'referer': 'https://tongclinic.com/adm/visit_domain.php?fr_date=2025-03-27&to_date=2025-03-27',
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

    response = request_api('get', url, headers, params)

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
    fr_date = '2025-03-01'
    to_date = '2025-03-27'

    data = get_visit_data(fr_date, to_date)
    for domain, count in data.items():
        print(f"{domain} : {count}")

    result = extract_keywords_from_pages(fr_date, to_date)

    print("\n[키워드별 방문자 수]")
    for keyword, count in result.items():
        print(f"{keyword} : {count}")

    # 👉 엑셀로 저장
    save_to_excel(data, result)