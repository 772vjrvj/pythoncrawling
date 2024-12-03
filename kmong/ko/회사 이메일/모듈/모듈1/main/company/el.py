import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
import requests
import random
from ..common import get_current_time


# 11번가 전체 페이지 가져오기
def fetch_total_pages(driver, kwd, page, product_id):
    url = f"https://apis.11st.co.kr/search/api/tab/total-search/more/common?kwd={kwd}&tabId=TOTAL_SEARCH&pageNo={page}&prdMoreStartShowCnt=60"
    response = requests.get(url)

    if response.status_code == 200:
        totalPageJson = response.json()
        total_pages = int(totalPageJson['totalPage'])
        print(f"티몬 전체 페이지 : {total_pages}")
        return total_pages
    else:
        response.raise_for_status()


# 11번가 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, kwd, page, product_id):
    url = f"https://apis.11st.co.kr/search/api/tab/total-search/more/common?kwd={kwd}&tabId=TOTAL_SEARCH&pageNo={page}&prdMoreStartShowCnt=60"
    response = requests.get(url)

    if response.status_code == 200:
        results = response.json()
        ids = parse_results(results)
        return ids
    else:
        response.raise_for_status()
        return []


# 11번가  제품 상세정보 가져오기
def fetch_product_detail(driver, kwd, page, product_id):
    url = f"https://www.11st.co.kr/products/{product_id}"
    seller_info = {
        "아이디": product_id,
        "키워드": kwd,
        "상호명": "",
        "이메일": "",
        "플랫폼": "11번가",
        "URL": url,
        "페이지": page,
        "작업시간": ""
    }
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '판매자정보')]"))
        )
        driver.execute_script("arguments[0].click();", button)

        time.sleep(2)
        tables = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'prdc_detail_table'))
        )
        found_all_info = False
        for table in tables:
            try:
                company_name_td = table.find_element(By.XPATH, ".//th[contains(text(), '상호명/대표자')]/following-sibling::td")
                seller_info["상호명"] = company_name_td.text if not seller_info["상호명"] else seller_info["상호명"]
                email_td = table.find_element(By.XPATH, ".//th[contains(text(), 'E-Mail')]/following-sibling::td")
                seller_info["이메일"] = email_td.text if not seller_info["이메일"] else seller_info["이메일"]
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


def parse_results(results):
    ids = set()
    items = results.get('items', [])
    for item in items:
        id_value = item.get('id')
        if id_value:
            ids.add(id_value)  # update 대신 add를 사용
    return list(ids)
