from datetime import datetime
import os
import pandas as pd

from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# 현재 시간
def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


# 드라이버 세팅 크롬
def setup_driver():
    chrome_options = Options()  # 크롬 옵션 설정

    # 헤드리스 모드로 실행
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--window-size=1080,750")  # 화면 크기 설정
    chrome_options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            '''
        })
        return driver
    except Exception as e:
        print(f"Error initializing Chrome WebDriver: {e}")
        return None


# 파일명 생성 함수
def create_filename(base_name, keyword, extension, directory="."):
    # 현재 시간
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

    while True:
        filename = f"{base_name}_{keyword}_{current_time}.{extension}"
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return filepath


# 엑셀 얻기
def fetch_excel(all_seller_info, kwd):
    columns = ['아이디', '키워드', '상호명', '이메일', '플랫폼', 'URL', '페이지', '작업시간']
    df = pd.DataFrame(all_seller_info, columns=columns)

    filename = create_filename("email_info", kwd, "xlsx")

    # 엑셀 파일 저장
    df.to_excel(filename, index=False)