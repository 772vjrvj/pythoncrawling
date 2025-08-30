import os
import ssl
import time
import traceback
import psutil
from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException, TimeoutException, \
    ElementClickInterceptedException, ElementNotInteractableException, InvalidSelectorException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc


ssl._create_default_https_context = ssl._create_unverified_context

class SeleniumUtils:
    def __init__(self, headless=False):
        self.driver = None
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
            # webdriver_options.add_argument("--start-maximized")

            # headless 모드로 Chrome을 실행합니다.
            # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
            # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
            ##### 화면이 안보이게 함 #####
            if self.headless:
                webdriver_options.add_argument("--headless")

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
            webdriver_options.add_argument("--window-size=500,600")       # 전체 모니터의 절반 너비, 최대 높이
            self.driver = webdriver.Chrome(options=webdriver_options)

        except WebDriverException:
            self.driver = None


    def set_chrome_driver_user(self):
        try:
            self._close_chrome_processes()
            time.sleep(2)

            chrome_options = Options()

            # 사용자 프로필 디렉토리 (충돌 방지를 위해 새 임시 프로필 경로 사용 권장)
            temp_profile_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data\\SeleniumTemp"
            chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # 안정성 향상 옵션
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")

            # User-Agent 설정
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')

            # 봇 감지 우회 설정
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 다운로드 설정
            download_dir = os.path.abspath("downloads")
            os.makedirs(download_dir, exist_ok=True)
            chrome_options.add_experimental_option('prefs', {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })

            # WebDriver 실행
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            # 봇 탐지 우회용 JS 삽입
            script = '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                });
            '''
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        except WebDriverException as e:
            print(f"❌ WebDriverException 발생: {e}")
            traceback.print_exc()
            self.driver = None

    # 크롬 끄기
    def _close_chrome_processes(self):
        """Chrome 및 ChromeDriver 관련 프로세스를 안전하게 종료합니다."""
        target_names = ['chrome.exe', 'chromedriver.exe']

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name']
                if proc_name and proc_name.lower() in target_names:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue


    def start_driver(self, timeout=30, user=None,  mode="default"):
        if mode == "undetected":
            self.set_undetected_chrome_driver()
        elif user:
            self.set_chrome_driver_user()
        else:
            self.set_chrome_driver()
        self.driver.set_page_load_timeout(timeout)

        return self.driver


    def handle_selenium_exception(self, context, exception):
        if isinstance(exception, NoSuchElementException):
            return f"❌ {context} - 요소 없음"
        elif isinstance(exception, StaleElementReferenceException):
            return f"❌ {context} - Stale 요소"
        elif isinstance(exception, TimeoutException):
            return f"⏱️ {context} - 로딩 시간 초과"
        elif isinstance(exception, ElementClickInterceptedException):
            return f"🚫 {context} - 클릭 방해 요소 존재"
        elif isinstance(exception, ElementNotInteractableException):
            return f"🚫 {context} - 요소가 비활성 상태"
        elif isinstance(exception, InvalidSelectorException):
            return f"🚫 {context} - 선택자 오류"
        elif isinstance(exception, WebDriverException):
            return f"⚠️ {context} - WebDriver 오류"
        else:
            return f"❗ {context} - 알 수 없는 오류"

    # SeleniumUtils 내부
    def wait_element(self, driver, by, selector, timeout=10):
        try:
            wait = WebDriverWait(driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception as e:
            self.handle_selenium_exception(f"wait_element: [{selector}] 요소를 {timeout}초 안에 찾지 못했습니다.", e)
            return None

    # 크롬 끄기
    def close_chrome_processes(self):
        """모든 Chrome 프로세스를 종료합니다."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()  # Chrome 프로세스를 종료
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def quit(self):
        if self.driver:
            self.driver.quit()


    def set_undetected_chrome_driver(self):
        try:
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # ✅ Headless 최적화 (new 방식)
            if self.headless:
                options.add_argument("--headless=new")

            # ✅ 이미지·폰트 로딩 차단 -- 속도 최적화
            prefs = {
                # "profile.managed_default_content_settings.images": 2,
                # "profile.managed_default_content_settings.fonts": 2,
                "download.default_directory": os.path.abspath("downloads"),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            os.makedirs(prefs["download.default_directory"], exist_ok=True)
            options.add_experimental_option("prefs", prefs)

            self.driver = uc.Chrome(options=options)

        except Exception as e:
            print(f"❌ undetected-chromedriver 로드 실패: {e}")
            traceback.print_exc()
            self.driver = None