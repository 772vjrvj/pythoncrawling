import re
import time
import random
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from src.utils.number_utils import extract_number

# API
class ApiWorker(QThread):
    api_data_received = pyqtSignal(object)  # API 호출 결과를 전달하는 시그널
    api_worker_log = pyqtSignal(object)  # API 호출 결과를 전달하는 시그널


    # 초기화
    def __init__(self, url_list, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.login_url = 'https://login.coupang.com/login/login.pang'
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.driver = None


    # 실행
    def run(self):
        data_list = []
        result = False
        try:
            result = self.set_login()
            if result:
                self.parent.add_log(f'url_list : {self.url_list} ')
                for url in self.url_list:
                    # 외부 API 호출
                    data = self.fetch_product_info_sele(url)
                    data_list.append(data)  # 결과를 리스트에 추가
                    self.parent.add_log(f'url 요청성공 : {url} ')
                    self.parent.add_log(f'url 요청 Data : {data} ')
                    time.sleep(random.uniform(1, 2))

        except Exception as e:
            self.parent.add_log(f'크롤링 중 발생{e}')

        finally:
            if result:
                # 데이터를 시그널로 전달
                self.api_data_received.emit(data_list)
            self.driver.quit()


    # 크롬 세팅
    def setup_chrome_options(self):
        """크롬 드라이버 옵션 설정"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Headless 모드 옵션 (필요에 따라 활성화)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1080,750")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 크롬 드라이버 설정 및 반환
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            '''
        })
        return driver


    # 로그인
    def set_login(self):
        try:
            self.driver = self.setup_chrome_options()
            # 로그인 페이지 열기
            self.driver.get(self.login_url)
            time.sleep(3)

            # 이메일 입력 필드 찾기
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "login-email-input"))
            )
            email_input.clear()  # 기존 텍스트를 지우고
            email_input.send_keys(self.parent.user_id)  # 사용자 ID 입력

            # 비밀번호 입력 필드 찾기
            password_input = self.driver.find_element(By.ID, "login-password-input")
            password_input.clear()  # 기존 텍스트를 지우고
            password_input.send_keys(self.parent.user_pw)  # 사용자 비밀번호 입력

            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.CLASS_NAME, "login__button--submit")
            login_button.click()

            time.sleep(3)
            # 로그인 후, 페이지가 로드될 때까지 대기 (예시: 로그인 후 나타나는 특정 요소)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "logout"))  # 'logout' 버튼이 나타날 때까지 대기
            )
            self.api_worker_log.emit("쿠팡 로그인 시도 성공")
            return True
        except NoSuchElementException as e:
            self.api_worker_log.emit(f"로그인 요소를 찾을 수 없습니다: {str(e)}")
            return False
        except TimeoutException as e:
            self.api_worker_log.emit(f"로그인 페이지 로드 시간이 초과되었습니다: {str(e)}")
            return False
        except Exception as e:
            self.api_worker_log.emit(f"로그인 실패: {str(e)}")
            return False

    
    # 데이터 크롤링
    def fetch_product_info_sele(self, url):
        try:
            # URL 로드
            self.driver.get(url)

            # 상품명 추출
            product_name = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "prod-buy-header__title"))
            ).text

            # 배송비 추출
            try:
                delivery_fee = self.driver.find_element(By.CLASS_NAME, "delivery-fee-info").text
            except NoSuchElementException as e:
                delivery_fee = ""

            # 판매가 추출
            try:
                total_price = self.driver.find_element(By.CLASS_NAME, "total-price").text
            except NoSuchElementException as e:
                total_price = ""

            # 배송비와 판매가에서 숫자만 추출하고 더하기
            delivery_fee_number = extract_number(delivery_fee)
            total_price_number = extract_number(total_price)
            total = delivery_fee_number + total_price_number
            total_formatted = f"{total:,}원" if total > 0 else ""

            # 최근 실행 시간
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 결과 객체
            obj = {
                "status": "success",
                "message": "성공",
                "data": {
                    "URL": url,
                    "상품명": product_name,
                    "배송비": delivery_fee,
                    "판매가": total_price,
                    "합계": total_formatted,
                    "최근실행시간": current_time,
                },
            }
            return obj

        except TimeoutException as e:
            return {"status": "error", "message": f"요소 로딩 실패: {str(e)}", "data": ""}
        except NoSuchElementException as e:
            return {"status": "error", "message": f"요소 탐색 실패: {str(e)}", "data": ""}
        except Exception as e:
            return {"status": "error", "message": f"알 수 없는 에러: {str(e)}", "data": ""}

