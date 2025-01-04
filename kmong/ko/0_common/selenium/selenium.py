from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver


def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    ###### 자동 제어 감지 방지 #####
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    ##### 화면 최대 #####
    chrome_options.add_argument("--start-maximized")

    ##### 화면이 안보이게 함 #####
    chrome_options.add_argument("headless")

    ##### 자동 경고 제거 #####
    chrome_options.add_experimental_option('useAutomationExtension', False)

    ##### 로깅 비활성화 #####
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    ##### 자동화 탐지 방지 설정 #####
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    ##### 자동으로 최신 크롬 드라이버를 다운로드하여 설치하는 역할 #####

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    ##### CDP 명령으로 자동화 감지 방지 #####
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    # 브라우저 위치와 크기 설정
    # driver.set_window_position(0, 0)  # 왼쪽 위 (0, 0) 위치로 이동
    # driver.set_window_size(1200, 900)  # 크기를 500x800으로 설정
    return driver




if __name__ == '__main__':
    setup_driver()

