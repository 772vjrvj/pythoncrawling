from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.common.exceptions import TimeoutException, WebDriverException

LOGGER.setLevel(logging.WARNING)

# 검색할 place와 category 쌍 배열
search_terms = [
    ("광주", "변호사태림")
    # 필요한 만큼 추가
]

# Selenium 설정
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 브라우저 창을 열지 않음
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')  # GPU 가속 비활성화
options.add_argument('--disable-software-rasterizer')  # SwiftShader 비활성화
options.add_argument('--remote-debugging-port=9222')  # 디버깅 포트 설정
options.add_argument('--single-process')
options.add_argument('--disable-extensions')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-background-networking')
options.add_argument('--disable-client-side-phishing-detection')
options.add_argument('--disable-default-apps')
options.add_argument('--disable-hang-monitor')
options.add_argument('--disable-popup-blocking')
options.add_argument('--disable-prompt-on-repost')
options.add_argument('--disable-sync')
options.add_argument('--disable-translate')
options.add_argument('--metrics-recording-only')
options.add_argument('--safebrowsing-disable-auto-update')
options.add_argument('--enable-automation')
options.add_argument('--password-store=basic')
options.add_argument('--use-mock-keychain')
options.add_argument('--disable-notifications')
options.add_argument('--disable-desktop-notifications')
options.add_argument('--disable-webgl')
options.add_argument('--disable-2d-canvas-clip-aa')
options.add_argument('--disable-2d-canvas-image-chromium')
options.add_argument('--log-level=3')  # 로깅 레벨 설정

# 드라이버 초기화
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 검색 및 place ID 추출 함수
def get_place_id(place, category):
    search_url = f"https://map.naver.com/v5/search/{place}%20{category}"
    try:
        driver.get(search_url)
        
        all_ids = []

        # iframe이 나타날 때까지 대기
        time.sleep(2)
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[id^="salt-search-marker-"]')))
        elements = driver.find_elements(By.CSS_SELECTOR, '[id^="salt-search-marker-"]')
        all_ids.extend([re.search(r'salt-search-marker-(\d+)', element.get_attribute('id')).group(1) for element in elements])
        print(f"첫 페이지에서 가져온 ID len: {len(all_ids)}")
    except TimeoutException as te:
        print(f"TimeoutException occurred: {te}")
    except WebDriverException as we:
        print(f"WebDriverException occurred: {we}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# 모든 검색어 쌍에 대해 place ID 추출
for place, category in search_terms:
    get_place_id(place, category)

# 드라이버 종료
driver.quit()