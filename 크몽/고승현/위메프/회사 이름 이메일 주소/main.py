import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


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


def fetch_last_page(driver, kwd, page):
    url = f"https://search.wemakeprice.com/search?searchType=DEFAULT&search_cate=top&keyword={kwd}&isRec=1&_service=5&_type=3&page={page}"
    driver.get(url)

    try:
        # Find the paging_comm element
        paging_comm = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'paging_comm'))
        )

        # Find all a tags within paging_comm
        a_tags = paging_comm.find_elements(By.TAG_NAME, 'a')

        if a_tags:
            # Get the data-page attribute of the last a tag
            last_a_tag = a_tags[-1]
            last_page = last_a_tag.get_attribute('data-page')
            return last_page
        else:
            print("a 태그를 찾을 수 없습니다.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def fetch_deal_ids(driver, kwd, page):
    url = f"https://search.wemakeprice.com/search?searchType=DEFAULT&search_cate=top&keyword={kwd}&isRec=1&_service=5&_type=3&page={page}"
    driver.get(url)

    try:
        time.sleep(2)
        # Find the search_box_listdeal element
        search_box_listdeal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'search_box_listdeal'))
        )

        # Find all list_conts_wrap elements within search_box_listdeal
        list_conts_wraps = search_box_listdeal.find_elements(By.CLASS_NAME, 'list_conts_wrap')

        # Extract data-gtm-link-value values from a tags inside each list_conts_wrap
        deal_ids = []
        for wrap in list_conts_wraps:
            a_tag = wrap.find_element(By.TAG_NAME, 'a')
            deal_id = a_tag.get_attribute('data-gtm-link-value')
            if deal_id:
                deal_ids.append(deal_id)

        return deal_ids

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def fetch_seller_info(driver, product_id):
    url = f"https://front.wemakeprice.com/product/{product_id}"
    driver.get(url)

    print(f"product_id : {product_id}")
    print(f"url : {url}")

    seller_info = {"상호": "", "e-mail": ""}

    time.sleep(2)

    try:
        # ul 태그 class detailTab 찾기
        detail_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab_info'))
        )

        # li 태그 data-wscrollspy-tab="cancelRefund" 찾기
        cancel_refund_tab = detail_tab.find_element(By.CSS_SELECTOR, 'li[data-wscrollspy-tab="cancelRefund"]')
        cancel_refund_tab.click()

        # id="cancelrefund" 찾기
        cancel_refund_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'cancelrefund'))
        )

        # class가 deal_shipinfo box인 것 중에 텍스트가 "판매자 정보"인 요소 찾기
        ship_info_boxes = cancel_refund_section.find_elements(By.CLASS_NAME, 'deal_shipinfo.box')
        seller_info_box = None
        for box in ship_info_boxes:
            if "판매자 정보" in box.text:
                seller_info_box = box
                break

        if not seller_info_box:
            print("판매자 정보를 찾을 수 없습니다.")
            return

        # deal_shipinfo box의 바로 다음 class가 table_box인 요소 찾기
        table_box = seller_info_box.find_element(By.XPATH, 'following-sibling::*[contains(@class, "table_box")]')

        # table_box 내부에 th 중 텍스트가 "상호 / 대표자"인 것의 td 텍스트 출력
        th_elements = table_box.find_elements(By.TAG_NAME, 'th')
        for th in th_elements:
            if '상호 / 대표자' in th.text:
                td = th.find_element(By.XPATH, './following-sibling::td')
                print(f"상호 / 대표자: {td.text}")
                seller_info['상호'] = td.text

            elif 'e-mail' in th.text:
                td = th.find_element(By.XPATH, './following-sibling::td')
                print(f"e-mail: {td.text}")
                seller_info['e-mail'] = td.text

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return seller_info

if __name__ == "__main__":

    kwd = '냉면'
    company = '오늘의집'
    initial_page = 1

    # Set up the Selenium WebDriver
    driver = setup_driver()

    # Fetch the last page number
    last_page = fetch_last_page(driver, kwd, initial_page)

    print(f"last_page : {last_page}")

    total_page = int(last_page)
    total_page = 1

    all_values = set()

    # 모든 페이지에 대해 for 문을 돌면서 id 값을 수집합니다.
    for page in range(1, total_page + 1):
        deal_srl_values = fetch_deal_ids(driver, kwd, page)
        all_values.update(deal_srl_values)  # set을 사용하여 중복을 자동으로 제거합니다.

    print(f"Deal IDs: {all_values}")
    print(f"Deal IDs: {len(all_values)}")

    all_values = ['604860045','630363768','2881368589','631025574','2881366817','2859040936','2612772036','2218046813','630683467','629325499']

    all_seller_info = []

    for product_id in all_values:

        seller_info = fetch_seller_info(driver, product_id)

        if seller_info:
            seller_info["키워드"] = kwd
            seller_info["플랫폼"] = company
            print(f"seller_info : {seller_info}")
            all_seller_info.append(seller_info)


    # Define the columns
    columns = ['키워드', '상호', 'e-mail', '플랫폼']

    # Create a DataFrame
    df = pd.DataFrame(all_seller_info, columns=columns)

    # Save the DataFrame to an Excel file
    df.to_excel('seller_info.xlsx', index=False)


