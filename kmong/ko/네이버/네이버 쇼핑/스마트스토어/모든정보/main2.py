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
from selenium.webdriver.common.action_chains import ActionChains

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
    columns = ['평점', '아이디', '날짜', '내용']
    df = pd.DataFrame(all_seller_info, columns=columns)
    filename = create_filename("products_info", kwd, "xlsx")
    df.to_excel(filename, index=False)

class Review:
    def __init__(self, rating, user_id, date, content):
        self.rating = rating
        self.user_id = user_id
        self.date = date
        self.content = content

    def to_dict(self):
        return {
            "평점": self.rating,
            "아이디": self.user_id,
            "날짜": self.date,
            "내용": self.content
        }

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 스크롤 후 로딩 시간 대기
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_product_info(driver, product_id):
    url = f"https://smartstore.naver.com/from_eat/products/{product_id}"
    driver.get(url)
    time.sleep(3)

    # 페이지의 맨 아래로 스크롤
    scroll_to_bottom(driver)
    time.sleep(2)  # 스크롤 후 로딩 시간 대기

    elements = driver.find_elements(By.CLASS_NAME, "_1k5R-niA93")
    print(len(elements))
    for element in elements:
        if "리뷰" in element.text:
            ActionChains(driver).move_to_element(element).perform()
            element.click()
            time.sleep(2)  # 클릭 후 로딩 시간 대기
            break

    # 리뷰 목록을 포함하는 ul 요소 찾기
    ul_element = driver.find_element(By.CLASS_NAME, "_2ms2i3dD92")
    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

    reviews = []

    # 각 리뷰 요소를 순회하며 정보 추출
    for li in li_elements:
        try:
            rating = li.find_element(By.CLASS_NAME, "_15NU42F3kT").text
            user_id = li.find_elements(By.CLASS_NAME, "_2L3vDiadT9")[0].text
            date = li.find_elements(By.CLASS_NAME, "_2L3vDiadT9")[1].text
            content = li.find_elements(By.CLASS_NAME, "_2L3vDiadT9")[2].text
            review = Review(rating, user_id, date, content)
            reviews.append(review)
        except Exception as e:
            print(f"Error extracting review: {e}")

    reviews_dict_list = [review.to_dict() for review in reviews]

    return reviews_dict_list

def main():
    ids = ['5233032940']
    all_product_info = []
    driver = setup_driver()

    for product_id in ids:
        product_info = extract_product_info(driver, product_id)
        all_product_info.extend(product_info)

    driver.quit()

    fetch_excel(all_product_info, "product")

if __name__ == "__main__":
    main()
