from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# 1. 검색 키워드 리스트
keywords = [
    "506897", "502935", "599032", "1176452", "737453",
    "1566411", "1786966", "1785343", "1773163"
]

# 2. 크롬 드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

try:
    # 3. 사이트 접속
    driver.get("https://www.kipris.or.kr/khome/main.do")
    time.sleep(2)

    # 4. 검색창 요소 찾기 (최초 1회만)
    search_box = driver.find_element(By.ID, "inputQuery")

    for keyword in keywords:
        print(f"🔍 검색 중: {keyword}")

        # 검색어 입력 후 엔터
        search_box.clear()
        search_box.send_keys(keyword)
        time.sleep(0.3)
        search_box.send_keys(Keys.ENTER)

        # 결과 페이지 로딩 대기 (네트워크 상황 따라 조정)
        time.sleep(5)

        # 다시 메인 페이지로 이동
        driver.get("https://www.kipris.or.kr/khome/main.do")
        time.sleep(3)

        # 다시 검색창 재지정 (새로고침 후에는 다시 요소를 잡아야 함)
        search_box = driver.find_element(By.ID, "inputQuery")

    input("✅ 전체 검색 완료. 브라우저 닫으려면 Enter를 누르세요.")

finally:
    driver.quit()
