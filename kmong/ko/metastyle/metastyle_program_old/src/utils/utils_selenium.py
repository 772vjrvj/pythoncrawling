from selenium import webdriver
import requests
import ssl
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

ssl._create_default_https_context = ssl._create_unverified_context

class SeleniumDriverManager:
    def __init__(self, headless=True):
        self.driver = None
        self.session = requests.Session()
        self.headless = headless

    def _get_chrome_options(self):
        webdriver_options = webdriver.ChromeOptions()

        # 이 옵션은 Chrome이 자동화 도구(예: Selenium)에 의해 제어되고 있다는 것을 감지하지 않도록 만듭니다.
        # AutomationControlled 기능을 비활성화하여 webdriver가 브라우저를 자동으로 제어하는 것을 숨깁니다.
        # 이는 일부 웹사이트에서 자동화 도구가 감지되는 것을 방지하는 데 유용합니다.
        ###### 자동 제어 감지 방지 #####
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')

        # Chrome 브라우저를 실행할 때 자동으로 브라우저를 최대화 상태로 시작합니다.
        # 이 옵션은 사용자가 브라우저를 처음 실행할 때 크기가 자동으로 최대로 설정되도록 합니다.
        ##### 화면 최대 #####
        webdriver_options.add_argument("--start-maximized")

        # headless 모드로 Chrome을 실행합니다.
        # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
        # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
        ##### 화면이 안보이게 함 #####
        # webdriver_options.add_argument("--headless")

        # 이 설정은 Chrome의 자동화 기능을 비활성화하는 데 사용됩니다.
        # 기본적으로 Chrome은 자동화가 활성화된 경우 브라우저의 콘솔에 경고 메시지를 표시합니다.
        # 이 옵션을 설정하면 이러한 경고 메시지가 나타나지 않도록 할 수 있습니다.
        ##### 자동 경고 제거 #####
        webdriver_options.add_experimental_option('useAutomationExtension', False)

        # 이 옵션은 브라우저의 로깅을 비활성화합니다.
        # enable-logging을 제외시키면, Chrome의 로깅 기능이 활성화되지 않아 불필요한 로그 메시지가 출력되지 않도록 할 수 있습니다.
        ##### 로깅 비활성화 #####
        webdriver_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 이 옵션은 enable-automation 스위치를 제외시킵니다.
        # enable-automation 스위치가 활성화되면,
        # 자동화 도구를 사용 중임을 알리는 메시지가 브라우저에 표시됩니다.
        # 이를 제외하면 자동화 도구의 사용이 감지되지 않습니다.
        ##### 자동화 도구 사용 감지 제거 #####
        webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        ##### 브라우저 위치 및 크기 설정 #####
        # 예: 해상도 1920x1080 기준으로 왼쪽 끝에 위치, 너비는 960, 높이는 1080
        webdriver_options.add_argument("--window-position=0,0")        # 브라우저를 좌측 상단에 위치
        webdriver_options.add_argument("--window-size=960,1080")       # 전체 모니터의 절반 너비, 최대 높이


        return webdriver_options

    def start_driver(self, url, timeout=120):
        self.driver = webdriver.Chrome(options=self._get_chrome_options())
        self.driver.set_page_load_timeout(timeout)
        self.driver.get(url)

        # Selenium의 쿠키를 requests 세션에 적용
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])

        return self.driver

    def selenium_scroll_keys_end(self, inter_time):

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # 페이지 끝까지 스크롤
            time.sleep(inter_time)  # 로딩 대기

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # 새로운 데이터가 없으면 종료
                break
            last_height = new_height


    def get_session(self):
        return self.session

    def quit(self):
        if self.driver:
            self.driver.quit()
