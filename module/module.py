from datetime import datetime
import os
import pandas as pd





# 현재 시간
def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# 드라이버 세팅 크롬
def setup_driver():
    chrome_options = Options()  # 크롬 옵션 설정을 위한 Options 객체 생성

    # 헤드리스 모드로 실행
    # chrome_options.add_argument("--headless")  # 화면 없이 실행 (주석 처리됨)

    # GPU 비활성화 (헤드리스 모드에서는 필수)
    chrome_options.add_argument("--disable-gpu")

    # 샌드박스 모드 비활성화 (일부 리눅스 시스템에서 필요)
    chrome_options.add_argument("--no-sandbox")

    # /dev/shm 사용 비활성화 (메모리 부족 문제 방지)
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 시크릿 모드로 실행 (쿠키 및 세션 데이터 저장 안 함)
    chrome_options.add_argument("--incognito")

    # 브라우저 창 크기 설정 (가로 1080, 세로 750)
    chrome_options.add_argument("--window-size=1080,750")

    # 원격 디버깅 포트 설정 (디버깅을 위한 포트 번호 9222)
    chrome_options.add_argument("--remote-debugging-port=9222")

    # 사용자 에이전트 설정 (특정 브라우저와 운영체제로 인식되도록)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 소프트웨어로 인식되지 않도록 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # ChromeDriver 설치 및 드라이버 객체 생성
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 웹드라이버 감지 방지 스크립트를 페이지에 추가
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    return driver  # 설정이 완료된 드라이버 객체 반환


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