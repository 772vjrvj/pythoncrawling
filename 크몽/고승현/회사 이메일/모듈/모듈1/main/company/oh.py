import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
import random
from ..common import get_current_time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# G마켓 전체 페이지 가져오기
def fetch_total_pages(driver, kwd, page, product_id):
    print("No Data")
    return


# G마켓 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, kwd, page, product_id):
    url = f"https://ohou.se/productions/feed.json?v=7&type=store&query={kwd}&page={page}&per=20"
    headers = {
        'authority': 'ohou.se',
        'method': 'GET',
        'path': f'/productions/feed.json?v=7&type=store&query={kwd}&page={page}&per=20',
        'scheme': 'https',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'If-None-Match': 'W/"45a142fe1a5df378810859e6665519dc"',
        'Priority': 'u=0, i',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }

    # 세션 생성
    session = requests.Session()

    # Retry 설정
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # UTF-8로 인코딩된 헤더 설정
    headers = {k: str(v).encode('utf-8') for k, v in headers.items()}

    try:
        response = session.get(url, headers=headers, timeout=10)  # 타임아웃 설정
        response.raise_for_status()  # 요청이 성공하지 못하면 예외를 발생시킵니다

        ids = response.json()
        product_ids = parse_results(ids)
        return product_ids

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except requests.exceptions.ConnectionError as err:
        print(f"Error connecting: {err}")
    except requests.exceptions.Timeout as err:
        print(f"Timeout error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")


def parse_results(results):
    ids = []
    items = results.get('productions', [])
    for item in items:
        id_value = item.get('id')
        if id_value:
            ids.append(id_value)
    return ids



# 티몬 제품 상세정보 가져오기
def fetch_product_detail(driver, kwd, page, product_id):
    url = f"https://item.gmarket.co.kr/Item?goodscode={product_id}&buyboxtype=ad"
    seller_info = {
        "아이디": product_id,
        "키워드": kwd,
        "상호명": "",
        "이메일": "",
        "플랫폼": "G마켓",
        "URL": url,
        "페이지": page,
        "작업시간": ""
    }
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))

        li_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "uxetabs_menu"))
        )

        for li in li_elements:
            if "교환" in li.text or "반품" in li.text or "환불" in li.text or "취소" in li.text:
                li.click()
                break

        datas = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "list__exchange-data"))
        )

        found_all_info = False
        for data in datas:
            try:
                company_name = WebDriverWait(data, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//li[contains(text(), '상호명')]/span[contains(@class, 'text__deco')]"))
                )

                seller_info["상호명"] = company_name.text if not seller_info["상호명"] else seller_info["상호명"]

                email = WebDriverWait(data, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'E-mail')]/span[contains(@class, 'text__deco')]"))
                )

                seller_info["이메일"] = email.text if not seller_info["이메일"] else seller_info["이메일"]
                if seller_info["상호명"] and seller_info["이메일"]:
                    found_all_info = True
                    break
            except (NoSuchElementException, ElementNotInteractableException):
                continue
        if not found_all_info:
            print("Not all information could be found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return seller_info

    seller_info["작업시간"] = get_current_time()
    return seller_info
