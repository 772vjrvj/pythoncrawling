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


def fetch_total_pages(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    driver.get(url)

    try:
        time.sleep(2)
        # Find the element with class "c-page__total" and get its text
        total_pages_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'c-page__total'))
        )
        total_pages_text = total_pages_element.text
        print(f"Total pages text: {total_pages_text}")
        return total_pages_text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def fetch_deal_srl_values(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    driver.get(url)

    try:
        # Find the deallist_wrap element and get all li elements inside the ul with class 'list'
        deallist_wrap = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'deallist_wrap'))
        )
        ul_element = deallist_wrap.find_element(By.CLASS_NAME, 'list')
        li_elements = ul_element.find_elements(By.CLASS_NAME, 'item')

        # Extract data-deal-srl values from a tags inside each li element
        deal_srl_values = []
        for li in li_elements:
            try:
                a_tag = WebDriverWait(li, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'a'))
                )
                deal_srl = a_tag.get_attribute('data-deal-srl')
                if deal_srl:
                    deal_srl_values.append(deal_srl)
            except Exception as e:
                print(f"Error retrieving data-deal-srl for an item: {e}")

        return deal_srl_values

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def fetch_product_details(driver, product_id):
    url = f"https://www.tmon.co.kr/deal/{product_id}"
    driver.get(url)

    print(f"product_id : {product_id}")
    print(f"url : {url}")

    seller_info = {"상호": "", "e-mail": ""}

    time.sleep(2)

    try:
        # Find the tab-inner _fixedUIItem element
        tab_inner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab-inner._fixedUIItem'))
        )

        # Find the ul element with class tab-navigation and click the 4th li element
        tab_navigation = tab_inner.find_element(By.CLASS_NAME, 'tab-navigation')
        li_elements = tab_navigation.find_elements(By.TAG_NAME, 'li')
        if len(li_elements) >= 4:
            li_elements[3].click()
        else:
            print("li 태그가 4개 이상 존재하지 않습니다.")
            return

        time.sleep(3)  # 네비게이션 후 페이지 로딩 시간 추가

        # Wait for and click the 2nd element with class toggle.tit_align_top
        toggle_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'toggle.tit_align_top'))
        )

        print(f"len {len(toggle_elements)}")

        toggle_elements_len = len(toggle_elements)

        if toggle_elements_len == 7:
            toggle_elements[4].click()
        elif toggle_elements_len == 4:
            toggle_elements[1].click()
        else:
            print("toggle.tit_align_top 요소가 4개 이상 존재하지 않습니다.")
            return


        time.sleep(3)  # 토글 클릭 후 페이지 로딩 시간 추가

        # Wait for the 2nd element with class ct.slide-ct
        slide_ct_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ct.slide-ct'))
        )

        print(f"len slide_ct_elements : {len(slide_ct_elements)}")


        if len(slide_ct_elements) >= 7:
            slide_ct = slide_ct_elements[4]
        elif len(slide_ct_elements) >= 4:
            slide_ct = slide_ct_elements[1]
        else:
            print("ct.slide-ct 요소가 2개 이상 존재하지 않습니다.")
            return

        # Find the table with class tbl_info and extract "상호명" and "이메일"
        table = WebDriverWait(slide_ct, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tbl_info'))
        )
        th_elements = table.find_elements(By.TAG_NAME, 'th')
        for th in th_elements:
            if '상호명' in th.text:
                td = th.find_element(By.XPATH, './following-sibling::td')
                seller_info['상호'] = td.text
            elif '이메일' in th.text:
                td = th.find_element(By.XPATH, './following-sibling::td')
                seller_info['e-mail'] = td.text

    except Exception as e:
        print(f"An error occurred: {e}")

    return seller_info



if __name__ == "__main__":
    kwd = "냉면"  # Replace with your keyword
    initial_page = 1  # Replace with your page number
    company = "티몬"

    # Set up the Selenium WebDriver
    driver = setup_driver()

    # Fetch the total pages text
    total_pages_text = fetch_total_pages(driver, kwd, initial_page)

    total_page = int(total_pages_text)
    total_page = 1

    all_deal_srl_values = set()

    # 모든 페이지에 대해 for 문을 돌면서 id 값을 수집합니다.
    for page in range(1, total_page + 1):
        deal_srl_values = fetch_deal_srl_values(driver, kwd, page)
        all_deal_srl_values.update(deal_srl_values)  # set을 사용하여 중복을 자동으로 제거합니다.


    print(f"deal_srl_values len : {len(all_deal_srl_values)}")


    all_seller_info = []

    all_deal_srl_values = ['14506661950', '26475116670','4045470354']

    for product_id in all_deal_srl_values:

        seller_info = fetch_product_details(driver, product_id)
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


