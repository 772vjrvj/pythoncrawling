from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
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

def get_product_ids(driver, keyword, start_page=1, end_page=2):
    ids = []
    base_url = "https://www.gmarket.co.kr/n/search?keyword={keyword}&k=42&p={page_num}"

    for page_num in range(start_page, end_page + 1):
        url = base_url.format(keyword=keyword, page_num=page_num)
        driver.get(url)

        # Random sleep to avoid being detected as a bot
        time.sleep(random.uniform(2, 3))  # Wait for the page to load

        # class 'box__item-container' 요소가 나타날 때까지 대기
        item_containers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "box__item-container"))
        )

        products = []

        for container in item_containers:
            try:
                # 각 'box__item-container' 안에 'box__image' 요소가 나타날 때까지 대기
                image_element = WebDriverWait(container, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "box__image"))
                )
                # 'box__image' 안에 'link__item' 요소가 나타날 때까지 대기
                link_element = WebDriverWait(image_element, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "link__item"))
                )

                # data-montelena-goodscode 속성 값 가져오기
                product = link_element.get_attribute("data-montelena-goodscode")
                if product:
                    products.append(product)

            except Exception as e:
                print("An error occurred:", e)

        products = list(set(products))

        print(f"Page {page_num}: Found {len(products)} products.")

        ids.extend(products)

    return list(set(ids))

def click_shipping_info_tab(driver, product_id):
    product_url = f"https://item.gmarket.co.kr/Item?goodscode={product_id}&buyboxtype=ad"
    driver.get(product_url)

    try:
        # Wait until the "배송/교환/반품 안내" tab is clickable
        fourth_menu = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "uxetabs_menu"))
        )[3]
        fourth_menu.click()
        print(f"Clicked '배송/교환/반품 안내' tab for product {product_id}")
    except TimeoutException:
        print(f"Timed out waiting for the shipping info tab for product {product_id}")


def extract_seller_info(driver):

    try:
        # box__exchange-guide 요소 찾기
        box_exchange_guide = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "box__exchange-guide"))
        )

        # box__exchange-guide 안의 box__inner 요소들 찾기
        box_inners = box_exchange_guide.find_elements(By.CLASS_NAME, "box__inner")

        # 다섯 번째 box__inner 요소가 존재하는지 확인
        if len(box_inners) >= 5:
            box_inner_fifth = box_inners[4]

            # box_inner_fifth 안의 list__exchange-data 요소 찾기
            list_exchange_data = box_inner_fifth.find_element(By.CLASS_NAME, "list__exchange-data")

            # list_exchange_data 안의 list-item 요소들 찾기
            list_items = list_exchange_data.find_elements(By.CLASS_NAME, "list-item")

            if len(list_items) >= 1:
                first_text_deco = list_items[0].find_element(By.CLASS_NAME, "text__deco").text
            else:
                first_text_deco = None

            # 일곱 번째 list-item 안의 text__deco 텍스트 가져오기
            if len(list_items) >= 7:
                seventh_text_deco = list_items[6].find_element(By.CLASS_NAME, "text__deco").text
            else:
                seventh_text_deco = None

        else:
            first_text_deco = None
            seventh_text_deco = None

    except Exception as e:
        first_text_deco = None
        seventh_text_deco = None
        print("An error occurred:", e)

    seller_info = {'상호': first_text_deco, 'e-mail': seventh_text_deco}

    print("First item text:", first_text_deco)
    print("Seventh item text:", seventh_text_deco)

    return seller_info

def main():
    keyword = input("Enter keyword: ")
    driver = setup_driver()


    start_page = 1
    end_page = 2

    # product_ids = get_product_ids(driver, keyword, start_page, end_page)

    # print("Collected IDs:", product_ids)
    # print("Collected IDs:", len(product_ids))

    company = "Gmarket"

    product_ids = [
        '795085196', '3563597557', '3474952436']

    all_seller_info = []

    for product_id in product_ids:
        click_shipping_info_tab(driver, product_id)
        # Optional: Add a delay to avoid being detected as a bot
        time.sleep(random.uniform(1, 3))
        seller_info = extract_seller_info(driver, )
        if seller_info:
            seller_info["키워드"] = keyword
            seller_info["플랫폼"] = company
            all_seller_info.append(seller_info)

    # Define the columns
    columns = ['키워드', '상호', 'e-mail', '플랫폼']

    # Create a DataFrame
    df = pd.DataFrame(all_seller_info, columns=columns)

    # Save the DataFrame to an Excel file
    df.to_excel('seller_info.xlsx', index=False)

    print("Collected Seller Info:", all_seller_info)


if __name__ == "__main__":
    main()
