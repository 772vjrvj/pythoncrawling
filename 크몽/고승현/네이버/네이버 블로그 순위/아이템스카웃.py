import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from datetime import datetime
import os
import pandas as pd

def setup_driver(userID):
    try:
        chrome_options = Options()
        user_data_dir = f"C:\\Users\\{userID}\\AppData\\Local\\Google\\Chrome\\User Data"
        profile = "Default"

        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"profile-directory={profile}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--headless")  # Headless 모드 추가

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        download_dir = os.path.abspath("downloads")
        os.makedirs(download_dir, exist_ok=True)

        chrome_options.add_experimental_option('prefs', {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        script = '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
        '''
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        return driver
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None

def main(userID, keyword):
    driver = setup_driver(userID)
    if driver is None:
        return

    try:
        driver.get("https://itemscout.io/")

        # Wait for the input field to be present
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="상품을 검색해보세요."]'))
        )

        # Set the value of the input field to the keyword
        input_element.send_keys(keyword)

        # Find the search button next to the input field and click it
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "검색")]'))
        )
        search_button.click()

        # "검색 비율" div와 그 옆의 버튼 찾기
        stat_title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "KeywordCountStat_count-title__nq7aO") and text()="검색 비율"]'))
        )
        button = stat_title.find_element(By.XPATH, 'following-sibling::button')

        # 마우스 오버 수행
        actions = ActionChains(driver)
        actions.move_to_element(button).perform()
        time.sleep(1)  # 마우스 오버 후 텍스트 로딩 시간

        # 마우스 오버 후 나타난 div에서 텍스트 가져오기
        hover_text_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "KeywordCountStat_count-title__nq7aO") and text()="검색 비율"]/following-sibling::button/following-sibling::div'))
        )
        hover_text = hover_text_div.text
        print("Hover text:", hover_text)

        # 정규 표현식으로 "모바일 검색수"와 "PC 검색수" 값 추출
        search_counts = {}
        mobile_search = re.search(r"모바일 검색수\s*:\s*([\d,]+)회", hover_text)
        pc_search = re.search(r"PC 검색수\s*:\s*([\d,]+)회", hover_text)

        if mobile_search:
            search_counts["MO"] = int(mobile_search.group(1).replace(",", ""))
        if pc_search:
            search_counts["PC"] = int(pc_search.group(1).replace(",", ""))

        search_counts["SUM"] = search_counts["MO"] + search_counts["PC"]

        return search_counts

    except TimeoutException:
        print("요소를 찾을 수 없습니다.")
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        print("드라이버 종료")
        driver.quit()

# 실행 시간 체크 추가
if __name__ == "__main__":
    start_time = datetime.now()  # 시작 시간
    print(f"시작 시간: {start_time}")
    userID = '772vj'
    keyword = "강남포차"
    search_counts = main(userID, keyword)

    # 객체 출력
    print("검색 결과:", search_counts)

    end_time = datetime.now()  # 종료 시간
    print(f"종료 시간: {end_time}")

    elapsed_time = end_time - start_time  # 실행 시간 계산
    print(f"총 실행 시간: {elapsed_time}")
