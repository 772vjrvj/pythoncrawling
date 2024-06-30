import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import random
from ..common import get_current_time


# 쿠팡 전체 페이지 가져오기
def fetch_total_pages(driver, kwd, page, product_id):
    print("No Data")
    return


# 쿠팡 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, kwd, page, product_id):
    url = f"https://www.coupang.com/np/search?component=&q={kwd}&page={page}&listSize=36"
    print(f"ids 조회 url : {url}")
    try:
        driver.get(url)
        time.sleep(3)

        # XPath를 사용하여 클래스명이 'search-product-list'인 요소 찾기
        product_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'search-product-list')]"))
        )

        # 그 안에서 클래스명이 'search-product'인 <li> 태그 찾기
        products = product_list.find_elements(By.XPATH, ".//li[contains(@class, 'search-product')]")

        print(f"products len : {len(products)}")

        ids = set()
        for product in products:
            product_id = product.get_attribute("id")
            if product_id:
                ids.add(product_id)
        return list(ids)

    except Exception as e:
        print(f"An error occurred while fetching the product list: {e}")
        return []


# 쿠팡 제품 상세정보 가져오기
def fetch_product_detail(driver, kwd, page, product_id):
    url = f"https://www.coupang.com/vp/products/{product_id}"
    seller_info = {
        "아이디": product_id,
        "키워드": kwd,
        "상호명": "",
        "이메일": "",
        "플랫폼": "쿠팡",
        "URL": url,
        "페이지": page,
        "작업시간": ""
    }
    print(f"url : {url}")
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        shipping_info_tab = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'li[name="etc"]'))
        )
        shipping_info_tab.click()
        time.sleep(2)
        tables = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "prod-delivery-return-policy-table"))
        )
        found_all_info = False
        for table in tables:
            try:
                company_name_td = table.find_element(By.XPATH, ".//th/div[contains(text(), '상호/대표자')]/../following-sibling::td")
                seller_info["상호명"] = company_name_td.text if not seller_info["상호명"] else seller_info["상호명"]
                email_td = table.find_element(By.XPATH, ".//th/div[contains(text(), 'e-mail')]/../following-sibling::td")
                seller_info["이메일"] = email_td.text if not seller_info["이메일"] else seller_info["이메일"]
                if seller_info["상호명"] and seller_info["이메일"]:
                    found_all_info = True
                    break
            except (NoSuchElementException, ElementNotInteractableException) as e:
                continue
        if not found_all_info:
            print("Not all information could be found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return seller_info

    seller_info["작업시간"] = get_current_time()
    return seller_info
