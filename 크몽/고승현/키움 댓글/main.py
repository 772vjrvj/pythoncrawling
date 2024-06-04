from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # 추가
import openpyxl
import requests

# 셀레니움 설정 및 웹 드라이버 준비
def init_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")  # 브라우저를 화면에 표시하지 않음

    options.add_argument("--start-maximized") # 화면이 제일 크게 열림

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# 웹 페이지 크롤링
def crawl_data(url):
    driver = init_driver()
    driver.get(url)

    # 페이지 로딩을 위한 대기
    driver.implicitly_wait(5)  # 최대 5초까지 대기

    try:
        # iframe 요소가 로드될 때까지 최대 30초 대기
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "ifrm"))
        )

        # iframe으로 전환
        driver.switch_to.frame(iframe)

        # iframe 내부의 a.notice-title 요소가 로드될 때까지 대기
        notice_link = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.kwGridHead.tb-kw-grid tbody td.al-l a.notice-title"))
        )

        print(notice_link.text)

    except TimeoutException:
        print("Timeout while waiting for element to be present")

if __name__ == '__main__':
    url = "https://www1.kiwoom.com/h/common/bbs/VBbsBoardBCOSZView?dummyVal=0"
    print(url)
    print()

    data = crawl_data(url)