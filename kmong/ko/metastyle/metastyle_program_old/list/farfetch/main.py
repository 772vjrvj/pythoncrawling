from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# 웹 드라이버 설정
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # 브라우저 숨김 모드
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

base_url = "https://www.farfetch.com/kr/sets/new-in-this-week-eu-women.aspx?page="
page = 1
all_products = []

while True:
    url = base_url + str(page)
    driver.get(url)
    time.sleep(3)  # 페이지 로딩 대기

    print(f"📢 현재 페이지: {page}")

    # 스크롤을 끝까지 내리기
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(7)  # 스크롤 후 대기 시간 추가
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            time.sleep(3)  # 마지막 스크롤 후 추가 대기
            break
        last_height = new_height

    # 모든 상품 li 태그 찾기 (최대 10초 대기)
    try:
        product_list = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='productCard']"))
        )
    except TimeoutException:
        print("🔴 상품을 찾을 수 없습니다. 종료합니다.")
        break  # 상품이 없으면 종료

    for product in product_list:
        try:
            # **a 태그 찾기 (li 태그 내부의 첫 번째 a 태그)**
            a_tag = WebDriverWait(product, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            href = a_tag.get_attribute("href")

            # URL 앞에 "https://www.farfetch.com"이 없으면 붙이기
            if not href.startswith("https://www.farfetch.com"):
                href = "https://www.farfetch.com" + href

            # 정규식을 사용하여 product_id 추출 (숫자만 찾기)
            product_id_match = re.search(r"item-(\d+)", href)
            product_id = product_id_match.group(1) if product_id_match else "Unknown"

            all_products.append({
                "href": href,
                "product_id": product_id
            })

        except (NoSuchElementException, TimeoutException):
            print("⚠️ a 태그를 찾을 수 없습니다. 다음 상품으로 넘어갑니다.")

    print(f"✅ 페이지 {page} 크롤링 완료. 총 상품 개수: {len(all_products)}")

    page += 1  # 다음 페이지로 이동
    time.sleep(3)

# 최종 결과 출력
print(all_products)

# 드라이버 종료
driver.quit()
