from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
products = []

for product in product_list:
    try:
        product_id = product.get_attribute("data-productid")  # 상품 ID 가져오기
        img_tag = product.find_element(By.XPATH, ".//img[contains(@class, 'media-image__image')]")
        img_src = img_tag.get_attribute("src")  # 이미지 URL 가져오기

        products.append({
            "data-productid": product_id,
            "src": img_src
        })
    except Exception as e:
        print(f"상품 정보 수집 오류: {e}")

# 결과 출력
print(len(products))
print(products)

# 드라이버 종료
driver.quit()
