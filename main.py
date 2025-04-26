from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# 크롬 드라이버 설정
options = Options()
options.add_argument("--headless")  # 브라우저 안 띄우고 실행하려면 주석 해제
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service()  # 자동 경로 설정 (chromedriver가 PATH에 등록되어 있는 경우)
driver = webdriver.Chrome(service=service, options=options)

try:
    # 페이지 열기
    url = "https://pkgtour.naver.com/products/airteltour/754501-20250501/schedule?adultCnt=1&childCnt=0&infantCnt=0"
    driver.get(url)

    # 페이지 로딩 대기
    time.sleep(3)  # 필요한 경우 WebDriverWait으로 대체 가능

    # class="Collapse"인 모든 요소 찾기
    collapse_elements = driver.find_elements(By.CLASS_NAME, "Collapse")

    for idx, element in enumerate(collapse_elements, start=1):
        # 각각 텍스트 가져와서 줄바꿈 제거하고 연결
        text = element.text.replace('\n', ' ').strip()
        print(f"[Collapse {idx}] {text}")

finally:
    driver.quit()
