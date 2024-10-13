import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException
import random
from ..common import get_current_time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# 오늘의집 전체 페이지 가져오기
def fetch_total_pages(driver, kwd, page, product_id):
    print("No Data")
    return


# 오늘의집 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, kwd, page, product_id):
    url = f"https://ohou.se/productions/feed.json?v=7&type=store&query={kwd}&page={page}&per=20"
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
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


# 페이지를 끝까지 스크롤하는 함수
def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 페이지가 로드될 시간을 줌
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height



# 티몬 제품 상세정보 가져오기
def fetch_product_detail(driver, kwd, page, product_id):
    url = f"https://ohou.se/productions/{product_id}/selling"
    print(f"url {url}")
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

        nav_list = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'production-selling-navigation__list'))
        )

        li_elements = nav_list.find_elements(By.TAG_NAME, 'li')
        print(f"li_elements : {len(li_elements)}")

        for li in li_elements:
            if "배송" in li.text or "환불" in li.text or "반품" in li.text or "취소" in li.text or "배송/환불" in li.text:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", li)
                    time.sleep(2)
                    li.click()
                    break
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", li)
                    break

        # 페이지 끝까지 스크롤
        # scroll_to_bottom(driver)

        time.sleep(3)

        # 모든 테이블 찾기
        tables = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'production-selling-table'))
        )
        print(f"tables {len(tables)}")
        found_all_info = False
        for table in tables:
            try:
                company_name_td = table.find_element(By.XPATH, ".//th[contains(text(), '상호')]/following-sibling::td")
                seller_info["상호명"] = company_name_td.text if not seller_info["상호명"] else seller_info["상호명"]
                email_td = table.find_element(By.XPATH, ".//th[contains(text(), 'E-mail')]/following-sibling::td")
                seller_info["이메일"] = email_td.text if not seller_info["이메일"] else seller_info["이메일"]
                if seller_info["상호명"] and seller_info["이메일"]:
                    found_all_info = True
                    break
            except NoSuchElementException as e:
                continue
            except ElementNotInteractableException as e:
                continue
        if not found_all_info:
            print("Not all information could be found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return seller_info

    seller_info["작업시간"] = get_current_time()
    return seller_info
