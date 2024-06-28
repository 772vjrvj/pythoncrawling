import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException

# 티몬 전체 페이지 가져오기
def fetch_total_pages(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    try:
        driver.get(url)
        time.sleep(5)
        total_pages_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'c-page__total'))
        )
        total_pages_text = total_pages_element.text.strip()
        if total_pages_text.isdigit():
            total_pages = int(total_pages_text)
            print(f"Total pages text: {total_pages}")
            return total_pages
        else:
            print("No valid total pages number found.")
            return 0
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Element not found or timed out: {e}")
        return 0
    except ValueError:
        print("Conversion error: Text is not a number.")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0

# 티몬 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    try:
        driver.get(url)
        time.sleep(2)
        deallist_wrap = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'deallist_wrap'))
        )
        ul_element = deallist_wrap.find_element(By.CLASS_NAME, 'list')
        li_elements = ul_element.find_elements(By.CLASS_NAME, 'item')
        ids = []
        for li in li_elements:
            try:
                a_tag = li.find_element(By.TAG_NAME, 'a')
                deal_srl = a_tag.get_attribute('data-deal-srl')
                if deal_srl:
                    ids.append(deal_srl)
            except Exception as e:
                print(f"Error retrieving data-deal-srl for an item: {e}")
        return ids
    except Exception as e:
        print(f"An error occurred while fetching the product list: {e}")
        return []

# 티몬 제품 상세정보 가져오기
def fetch_product_detail(driver, product_id):
    url = f"https://www.tmon.co.kr/deal/{product_id}"
    driver.get(url)
    seller_info = {"상호명": "", "이메일": ""}
    try:
        time.sleep(3)
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
        return {}
    return seller_info
