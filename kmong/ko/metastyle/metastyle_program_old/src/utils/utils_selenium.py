import base64
import os
import ssl
import time

import psutil
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

ssl._create_default_https_context = ssl._create_unverified_context

class SeleniumDriverManager:
    def __init__(self, headless=True):
        self.driver = None
        self.session = requests.Session()
        self.headless = headless

    def set_chrome_driver(self):
        try:
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
            # webdriver_options.add_argument("--window-position=0,0")        # 브라우저를 좌측 상단에 위치
            # webdriver_options.add_argument("--window-size=960,1080")       # 전체 모니터의 절반 너비, 최대 높이
            self.driver = webdriver.Chrome(options=webdriver_options)
        except WebDriverException:
            self.driver = None


    def set_chrome_driver_user(self):
        try:
            self._close_chrome_processes()

            chrome_options = Options()
            user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
            profile = "Default"

            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"profile-directory={profile}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--start-maximized")
            # chrome_options.add_argument("--headless")  # Headless 모드 추가

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

            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            script = '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
            '''
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})
        except WebDriverException:
            self.driver = None


    def start_driver(self, url, timeout=120, user=None):
        if user:
            self.set_chrome_driver_user()
        else:
            self.set_chrome_driver()
        self.driver.set_page_load_timeout(timeout)
        self.driver.get(url)

        # Selenium의 쿠키를 requests 세션에 적용
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])

        return self.driver

    # 크롬 끄기
    def _close_chrome_processes(self):
        """모든 Chrome 프로세스를 종료합니다."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()  # Chrome 프로세스를 종료
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


    def _get_chrome_options_user(self):
        try:
            self._close_chrome_processes()

            chrome_options = Options()
            user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
            profile = "Default"

            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"profile-directory={profile}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--start-maximized")
            # chrome_options.add_argument("--headless")  # Headless 모드 추가

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

            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            script = '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
            '''
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})
        except WebDriverException:
            self.driver = None


    def selenium_scroll_keys_end(self, inter_time):

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # 페이지 끝까지 스크롤
            time.sleep(inter_time)  # 로딩 대기

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # 새로운 데이터가 없으면 종료
                break
            last_height = new_height


    def selenium_scroll_smooth(self, inter_time=0.5, step=100, delay=6):
        """
        전체 문서 높이에 비례하여 스크롤 step을 계산하여 부드럽게 스크롤합니다.
        :param inter_time: 스크롤 간 sleep 시간
        :param step_ratio: 전체 높이에 대한 스크롤 비율 (ex: 0.02 = 2%)
        :param delay: 마지막 지점에서 기다리는 시간
        """

        # window.scrollY	현재 스크롤 위치 (페이지 상단에서 얼마나 내렸는지)
        # window.innerHeight	현재 보이는 화면 높이 (뷰포트)
        # document.body.scrollHeight	전체 문서의 총 세로 길이
        # scrollY (4200) + innerHeight (800) = scrollHeight (5000)

        # 1. scrollTo(x, y) 절대적(Absolute) 위치로 이동합니다. 페이지 상단에서부터의 위치를 기준으로 이동합니다.
        # 2. scrollBy(x, y) 상대적(Relative) 위치로 이동합니다. 현재 스크롤 위치를 기준으로 추가로 이동합니다

        while True:
            initial_scroll_height = self.driver.execute_script("return document.body.scrollHeight")

            while True:
                current_scroll = self.driver.execute_script("return window.scrollY")
                window_height = self.driver.execute_script("return window.innerHeight")
                total_height = self.driver.execute_script("return document.body.scrollHeight")

                if current_scroll + window_height >= total_height - 2:
                    break

                self.driver.execute_script(f"window.scrollBy(0, {step});")
                time.sleep(inter_time)

            time.sleep(delay)

            updated_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            if updated_scroll_height == initial_scroll_height:
                break


    def download_image_content(self, obj):
        image_url = obj['image_url']
        try:
            # 👉 f_auto → f_jpg 강제 교체 (선택)
            if "f_auto" in image_url:
                image_url = image_url.replace("f_auto", "f_jpg")
                obj['image_url_modified'] = image_url  # 추적용

            self.driver.get(image_url)
            self.driver.implicitly_wait(5)

            # ✅ <img> 태그 찾기
            img = self.driver.find_element(By.TAG_NAME, "img")

            # ✅ canvas에 그림을 그리고 base64로 추출
            script = """
                var img = arguments[0];
                var canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                var ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/jpeg');
            """
            data_url = self.driver.execute_script(script, img)

            if not data_url.startswith("data:image"):
                obj['error'] = "이미지 추출 실패"
                obj['image_yn'] = 'N'
                return None

            # ✅ base64 디코딩
            header, encoded = data_url.split(",", 1)
            binary_data = base64.b64decode(encoded)

            return binary_data

        except Exception as e:
            obj['error'] = str(e)
            obj['image_yn'] = 'N'
            return None


    def get_session(self):
        return self.session


    def quit(self):
        if self.driver:
            self.driver.quit()
