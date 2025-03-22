from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import time

# 웹 드라이버 설정
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # 브라우저 숨김 모드
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Zara 페이지 접속
url = "https://www.zara.com/us/en/woman-new-in-l1180.html?v1=2546081"
driver.get(url)
time.sleep(4)

try:
    # 버튼이 로딩될 때까지 최대 10초 대기 후 클릭
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    accept_button.click()
    time.sleep(2)
    print("쿠키 수락 버튼 클릭 완료")
except Exception as e:
    print("버튼 클릭 중 오류 발생:", e)



try:
    # data-qa-action 속성으로 버튼 찾기
    stay_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qa-action='stay-in-store']"))
    )
    stay_button.click()
    time.sleep(2)
    print("국가 유지 버튼 클릭 완료")
except Exception as e:
    print("버튼 클릭 중 오류 발생:", e)


# "3" 버튼 클릭
try:
    button = driver.find_element(By.XPATH, "//span[contains(@class, 'view-option-selector-button__option') and text()='3']")
    ActionChains(driver).move_to_element(button).click().perform()
    time.sleep(3)
except Exception as e:
    print(f"3 버튼 클릭 실패: {e}")

# 스크롤 내리기 (데이터가 늘어날 때까지)
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # 페이지 끝까지 스크롤
    time.sleep(2)  # 로딩 대기

    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:  # 새로운 데이터가 없으면 종료
        break
    last_height = new_height

# 모든 상품 li 태그 가져오기
product_list = driver.find_elements(By.XPATH, "//li[contains(@class, 'product-grid-product')]")

# 결과 저장 리스트
product_links = []

for product in product_list:
    try:
        # 1. 데이터 없는 경우: info-wrapper가 없으면 건너뛰기
        try:
            info_wrapper = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__data > div.product-grid-product__info-wrapper")
        except NoSuchElementException:
            continue  # info-wrapper 없으면 넘어감

        # 2. 텍스트가 "LOOK"이면 건너뛰기
        try:
            name_tag = info_wrapper.find_element(By.CSS_SELECTOR, "a.product-grid-product-info__name")
            product_name = name_tag.text.strip()
            if product_name == "LOOK":
                continue
        except NoSuchElementException:
            continue  # name_tag 없으면 넘어감

        # 3. 링크 수집
        try:
            link_tag = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__figure a.product-grid-product__link")
            href = link_tag.get_attribute("href")
            if href:
                product_links.append(href)
        except NoSuchElementException:
            continue  # 링크 못 찾으면 넘어감

    except Exception as e:
        print(f"상품 처리 중 오류 발생: {e}")

# 결과 출력
print(len(product_links))
print(product_links)



# 상세 정보 저장 리스트
product_details = []

for url in product_links:
    try:
        driver.get(url)
        time.sleep(1)  # 페이지 로딩 대기

        # 1. 지역 선택 버튼 클릭 (있다면)
        try:
            stay_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa-action='stay-in-store']"))
            )
            stay_btn.click()
            print("지역 선택 버튼 클릭")
            time.sleep(1)
        except TimeoutException:
            pass  # 버튼 없으면 무시하고 진행

        # 2. product-detail-view__main-content 영역
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-detail-view__main-content"))
        )

        # 이미지 src 추출
        try:
            img_tag = driver.find_element(By.CSS_SELECTOR,
                                          "div.product-detail-view__main-content button.product-detail-image img")
            img_src = img_tag.get_attribute("src")
        except NoSuchElementException:
            img_src = None

        # 제품명
        try:
            name = driver.find_element(By.CSS_SELECTOR,
                                       "div.product-detail-view__main-info .product-detail-info__header-name").text.strip()
        except NoSuchElementException:
            name = ""

        # 가격
        try:
            price = driver.find_element(By.CSS_SELECTOR,
                                        "div.product-detail-view__main-info .money-amount__main").text.strip()
        except NoSuchElementException:
            price = ""

        # 설명
        try:
            content = driver.find_element(By.CSS_SELECTOR,
                                          "div.product-detail-view__main-info .expandable-text__inner-content").text.strip()
        except NoSuchElementException:
            content = ""

        # 객체로 저장
        product_details.append({
            "url": url,
            "src": img_src,
            "name": name,
            "price": price,
            "content": content
        })
        print(f"[완료] {name}")

    except Exception as e:
        print(f"[오류] {url} 처리 중 문제 발생: {e}")




# 드라이버 종료
driver.quit()
