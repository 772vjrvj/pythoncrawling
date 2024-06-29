import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
import random
from ..common import get_current_time


# G마켓 전체 페이지 가져오기
def fetch_total_pages(driver, kwd, page, product_id):
    print("No Data")
    return


# G마켓 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, kwd, page, product_id):
    url = f"https://www.gmarket.co.kr/n/search?keyword={kwd}&k=42&p={page}"
    try:
        driver.get(url)
        time.sleep(2)
        item_containers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "box__item-container"))
        )
        ids = set()
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
                    ids.add(product)
            except Exception as e:
                print(f"Error retrieving data-deal-srl for an item: {e}")
                return []
        return list(ids)
    except Exception as e:
        print(f"An error occurred while fetching the product list: {e}")
        return []


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
