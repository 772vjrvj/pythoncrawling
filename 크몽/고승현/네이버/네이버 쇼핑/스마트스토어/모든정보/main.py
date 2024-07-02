import os
import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--window-size=1080,750")
    chrome_options.add_argument("--remote-debugging-port=9222")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

def create_filename(base_name, keyword, extension, directory="."):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    while True:
        filename = f"{base_name}_{keyword}_{current_time}.{extension}"
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return filepath

def fetch_excel(all_seller_info, kwd):
    columns = ['상품명', '상품가격', '대표이미지', '상호명', '대표자', '배송', '배송옵션', '배송가격', '상품번호', '상품상태', '제조사', '브랜드', '모델명', '원산지']
    df = pd.DataFrame(all_seller_info, columns=columns)
    filename = create_filename("products_info", kwd, "xlsx")
    df.to_excel(filename, index=False)

def extract_product_info(driver, product_id):
    url = f"https://smartstore.naver.com/from_eat/products/{product_id}"
    driver.get(url)
    time.sleep(3)

    product_info = {}
    try:
        product_info['상품명'] = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_22kNQuEXmb._copyable"))).text
    except Exception as e:
        product_info['상품명'] = ""
        print(f"Error extracting 상품명 for {product_id}: {e}")

    try:
        product_info['상품가격'] = driver.find_element(By.CLASS_NAME, "_1LY7DqCnwR").text
    except Exception as e:
        product_info['상품가격'] = ""
        print(f"Error extracting 상품가격 for {product_id}: {e}")

    try:
        product_info['대표이미지'] = driver.find_element(By.CLASS_NAME, "bd_1uFKu.bd_2PG3r").find_element(By.TAG_NAME, "img").get_attribute("src")
    except Exception as e:
        product_info['대표이미지'] = ""
        print(f"Error extracting 대표이미지 for {product_id}: {e}")

    try:
        tables = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "IA34ue2o2i")))
        for table in tables:
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                try:
                    th_elements = row.find_elements(By.TAG_NAME, "th")
                    td_elements = row.find_elements(By.TAG_NAME, "td")
                    for th, td in zip(th_elements, td_elements):
                        th_text = th.text
                        td_text = td.text
                        if th_text == "상호명":
                            product_info['상호명'] = td_text
                        elif th_text == "대표자":
                            product_info['대표자'] = td_text
                except Exception as e:
                    print(f"Error extracting table row data for {product_id}: {e}")
                    continue
    except Exception as e:
        product_info.update({'상호명': "", '대표자': ""})
        print(f"Error extracting table for {product_id}: {e}")



    try:
        tables = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "_1_UiXWHt__")))
        for table in tables:
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                try:
                    th_elements = row.find_elements(By.TAG_NAME, "th")
                    td_elements = row.find_elements(By.TAG_NAME, "td")
                    for th, td in zip(th_elements, td_elements):
                        th_text = th.text
                        td_text = td.text
                        if th_text == "상품번호":
                            product_info['상품번호'] = td_text
                        elif th_text == "상품상태":
                            product_info['상품상태'] = td_text
                        elif th_text == "제조사":
                            product_info['제조사'] = td_text
                        elif th_text == "브랜드":
                            product_info['브랜드'] = td_text
                        elif th_text == "모델명":
                            product_info['모델명'] = td_text
                        elif th_text == "원산지":
                            product_info['원산지'] = td_text
                except Exception as e:
                    print(f"Error extracting table row data for {product_id}: {e}")
                    continue
    except Exception as e:
        print(f"Error extracting table for {product_id}: {e}")




    try:
        product_info['배송'] = driver.find_element(By.CLASS_NAME, "bd_ChMMo").text
    except Exception as e:
        product_info['배송'] = ""
        print(f"Error extracting 배송 for {product_id}: {e}")

    try:
        product_info['배송옵션'] = driver.find_element(By.CLASS_NAME, "bd_1g_zz").text
    except Exception as e:
        product_info['배송옵션'] = ""
        print(f"Error extracting 배송옵션 for {product_id}: {e}")

    try:
        product_info['배송가격'] = driver.find_element(By.CLASS_NAME, "bd_3uare").text
    except Exception as e:
        product_info['배송가격'] = ""
        print(f"Error extracting 배송가격 for {product_id}: {e}")

    return product_info




def main():
    ids = ['5233032940', '7617395160']
    all_product_info = []
    driver = setup_driver()

    for product_id in ids:
        product_info = extract_product_info(driver, product_id)
        all_product_info.append(product_info)

    driver.quit()

    fetch_excel(all_product_info, "product")

if __name__ == "__main__":
    main()
