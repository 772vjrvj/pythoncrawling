import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import random
from ..common import get_current_time


# 위메프 전체 페이지 가져오기
def fetch_total_pages(driver, kwd, page, product_id):
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
            return int(last_page)
        else:
            print("a 태그를 찾을 수 없습니다.")
            return 0

    except Exception as e:
        print(f"An error occurred: {e}")
        return 0


# 위메프 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, kwd, page, product_id):
    url = f"https://search.wemakeprice.com/search?searchType=DEFAULT&search_cate=top&keyword={kwd}&isRec=1&_service=5&_type=3&page={page}"
    try:
        driver.get(url)
        time.sleep(3)
        search_box_listdeal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'search_box_listdeal'))
        )

        list_conts_wraps = search_box_listdeal.find_elements(By.CLASS_NAME, 'list_conts_wrap')

        ids = set()
        for wrap in list_conts_wraps:
            a_tag = wrap.find_element(By.TAG_NAME, 'a')
            deal_id = a_tag.get_attribute('data-gtm-link-value')
            if deal_id:
                ids.add(deal_id)

        return list(ids)
    except Exception as e:
        print(f"An error occurred while fetching the product list: {e}")
        return []


# 위메프 제품 상세정보 가져오기
def fetch_product_detail(driver, kwd, page, product_id):
    url = f"https://front.wemakeprice.com/product/{product_id}"
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

        detail_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab_info'))
        )

        li_elements = detail_tab.find_elements(By.TAG_NAME, 'li')

        for li in li_elements:
            if "배송" in li.text or "교환" in li.text or "반품" in li.text:
                li.click()
                break

        time.sleep(2)

        tables = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'table_info'))
        )

        found_all_info = False
        for table in tables:
            try:
                company_name_td = table.find_element(By.XPATH, ".//th[contains(text(), '업체명')]/following-sibling::td")
                seller_info["상호명"] = company_name_td.text if not seller_info["상호명"] else seller_info["상호명"]
                email_td = table.find_element(By.XPATH, ".//th[contains(text(), 'e-mail')]/following-sibling::td")
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
