import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from datetime import datetime
import random


# 현재 시간
def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def setup_driver():
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")  # Use incognito mode

    # Set user-agent to mimic a regular browser
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Bypass the detection of automated software
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    return driver


def parse_results(results):
    ids = set()
    items = results.get('items', [])
    for item in items:
        id_value = item.get('id')
        if id_value:
            ids.update(id_value)
    return list(ids)


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
        "플랫폼": "티몬",
        "URL": url,
        "페이지": page,
        "작업시간": ""
    }
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        tab_inner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab-inner._fixedUIItem'))
        )
        tab_navigation = tab_inner.find_element(By.CLASS_NAME, 'tab-navigation')
        li_elements = tab_navigation.find_elements(By.TAG_NAME, 'li')
        for li in li_elements:
            if "환불" in li.text or "교환" in li.text or "취소" in li.text:
                li.click()
                break
        time.sleep(2)
        seller_info_button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//button[h4[text()='판매자 정보']]"))
        )
        seller_info_button.click()
        time.sleep(2)
        tables = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'tbl_info'))
        )
        found_all_info = False
        for table in tables:
            try:
                company_name_td = table.find_element(By.XPATH, ".//th[contains(text(), '상호명')]/following-sibling::td")
                seller_info["상호명"] = company_name_td.text if not seller_info["상호명"] else seller_info["상호명"]
                email_td = table.find_element(By.XPATH, ".//th[contains(text(), '이메일')]/following-sibling::td")
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

if __name__ == "__main__":
    kwd = input("Enter keyword: ")
    # 예제 검색어와 첫 페이지 번호
    company = '11번가'
    initial_page = 1

    # Selenium WebDriver 설정
    driver = setup_driver()

    # 첫 페이지에서 totalPage 값을 가져옵니다.
    totalPage = fetch_total_pages(driver, kwd, initial_page, '')


    all_ids = set()
    print("11번가...")
    print("페이지 수집...")

    # 모든 페이지에 대해 for 문을 돌면서 id 값을 수집합니다.
    for page in range(1, 1 + 1):
        pr_ids = fetch_product_ids(driver, kwd, page, '')
        all_ids.update(pr_ids)  # set을 사용하여 중복을 자동으로 제거합니다.


    print("크롤링 시작...")

    all_ids = ['5928602581', '4424564709', '7149332910']

    all_seller_info = []

    for product_id in all_ids:
        seller_info = fetch_product_detail(driver, kwd, page, product_id)
        print(f"seller_info : {seller_info}")
        all_seller_info.append(seller_info)

        # Define the columns
    columns = ['키워드', '상호', 'e-mail', '플랫폼']

    # Create a DataFrame
    df = pd.DataFrame(all_seller_info, columns=columns)

    # Save the DataFrame to an Excel file
    df.to_excel('seller_info.xlsx', index=False)


