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

def fetch_search_results(kwd, page):
    url = f"https://ohou.se/productions/feed.json?v=7&type=store&query={kwd}&page={page}&per=20"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def parse_results(results):
    ids = []
    items = results.get('items', [])
    for item in items:
        id_value = item.get('id')
        if id_value:
            ids.append(id_value)
    return ids

def click_fourth_tab(driver, product_id):
    time.sleep(2)  # 각 요청 사이에 잠시 대기
    url = f"https://www.11st.co.kr/products/{product_id}"
    driver.get(url)

    seller_info = {"상호": "", "e-mail": ""}

    try:
        # Wait until the product detail wrap is present
        product_detail_wrap = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'l_product_detail_wrap'))
        )

        # Find the tab list inside the product detail wrap
        product_tab_list = WebDriverWait(product_detail_wrap, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'c_product_tab_list'))
        )

        # Find the tab menu items
        tab_menus = product_tab_list.find_elements(By.CLASS_NAME, 'tab_menu')
        if len(tab_menus) >= 4:
            fourth_tab_button = tab_menus[3].find_element(By.TAG_NAME, 'button')

            # Scroll the element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", fourth_tab_button)
            time.sleep(1)  # Allow some time for any potential animations or scrolling to complete

            # Use JavaScript to click the element
            driver.execute_script("arguments[0].click();", fourth_tab_button)
            print(f"Clicked the 4th tab for product ID: {product_id}")

            # Wait for the details tables to load
            time.sleep(1)
            details_tables = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'prdc_detail_table'))
            )

            if len(details_tables) >= 4:
                details_table = details_tables[3]  # Get the 4th table

                # Find all rows in the 4th details table
                rows = details_table.find_elements(By.TAG_NAME, 'tr')

                for row in rows:
                    th_elements = row.find_elements(By.TAG_NAME, 'th')
                    td_elements = row.find_elements(By.TAG_NAME, 'td')

                    for th, td in zip(th_elements, td_elements):
                        th_text = th.text.strip()
                        td_text = td.text.strip()
                        if "상호명/대표자" in th_text:
                            seller_info['상호'] = td_text
                        elif "E-Mail" in th_text:
                            seller_info['e-mail'] = td_text
            else:
                print(f"Less than 4 details tables found for product ID: {product_id}")

    except Exception as e:
        print(f"An error occurred for product ID: {product_id}: {e}")

    return seller_info

if __name__ == "__main__":
    # 예제 검색어와 첫 페이지 번호
    kwd = '냉면'
    company = '오늘의집'
    initial_page = 1

    # 첫 페이지에서 totalPage 값을 가져옵니다.
    totalPageJson = fetch_search_results(kwd, initial_page)
    totalPage = int(totalPageJson['totalPage'])

    all_ids = set()

    # 모든 페이지에 대해 for 문을 돌면서 id 값을 수집합니다.
    for page in range(1, 1 + 1):
        results = fetch_search_results(kwd, page)
        ids = parse_results(results)
        all_ids.update(ids)  # set을 사용하여 중복을 자동으로 제거합니다.

    # Selenium WebDriver 설정
    driver = setup_driver()


    # all_ids = ['5928602581', '4424564709', '7149332910']

    all_seller_info = []

    for product_id in all_ids:
        seller_info = click_fourth_tab(driver, product_id)
        seller_info["키워드"] = kwd
        seller_info["플랫폼"] = company
        all_seller_info.append(seller_info)

        # Define the columns
    columns = ['키워드', '상호', 'e-mail', '플랫폼']

    # Create a DataFrame
    df = pd.DataFrame(all_seller_info, columns=columns)

    # Save the DataFrame to an Excel file
    df.to_excel('seller_info.xlsx', index=False)


