import os
import random
import re
import ssl
import pandas as pd
import psutil
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta



ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiKreamSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    finally_finished_signal = pyqtSignal(str)
    msg_signal = pyqtSignal(str, str)

    # 초기화
    def __init__(self, user_list):
        super().__init__()
        self.baseUrl = "https://kream.co.kr"
        self.result_list = []
        self.before_pro_value = 0
        self.user_list = user_list  # URL을 클래스 속성으로 저장
        self.end_cnt = 0
        self.cookies = None
        self.access_token = None
        self.running = True  # 실행 상태 플래그 추가
        self.request_key = None
        self.driver = None
        self.all_end = 'N'

        if len(self.user_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')
        else:
            self.driver = self._setup_driver()

    # 실행
    def run(self):
        if len(self.user_list) > 0:
            for idx, user in enumerate(self.user_list, start=1):
                self.end_cnt = idx
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                login = self._login(user)

                # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
                current_time = datetime.now().strftime("%Y%m%d%H%M%S")

                self.file_name = f"{user['ID']}_{current_time}.csv"

                if login:
                    self.log_signal.emit("크롤링 시작")
                    cursor = 1
                    all_extracted_ids = []

                    while True:
                        extracted_ids = self._get_sold_out_list(cursor)
                        if not extracted_ids:  # 빈 배열이 반환되면 종료
                            self.log_signal.emit(f"❌ 404 에러 또는 더 이상 데이터가 없습니다. (cursor={cursor})")
                            break
                        all_extracted_ids.extend(extracted_ids)  # 결과 합치기
                        self.log_signal.emit(f'목록 {cursor} : {extracted_ids}')
                        cursor += 1  # cursor 증가
                        time.sleep(random.uniform(0.5, 1))

                    for idx, product_id in enumerate(all_extracted_ids, start=1):
                        if not self.running:  # 실행 상태 확인
                            self.log_signal.emit("크롤링이 중지되었습니다.")
                            break

                        # 100개의 항목마다 임시로 엑셀 저장
                        if (idx - 1) % 10 == 0 and self.result_list:
                            self._save_to_csv_append(self.result_list)  # 임시 엑셀 저장 호출
                            self.log_signal.emit(f"엑셀 {idx - 1}개 까지 임시저장")
                            self.result_list = []  # 저장 후 초기화

                        self.log_signal.emit(f'번호 : {idx}, 시작')
                        product_data = self.fetch_product_data(product_id)
                        product_data['USER_ID'] = user['ID']
                        self.log_signal.emit(f'번호 : {idx}, 데이터 : {product_data}')

                        pro_value = (idx / len(all_extracted_ids)) * 1000000
                        self.progress_signal.emit(self.before_pro_value, pro_value)
                        self.before_pro_value = pro_value

                        self.result_list.append(product_data)
                        time.sleep(random.uniform(1, 2))

                    self._logout(user)
                    self._remain_data_set()
                    self.result_list = []
                else:
                    self.log_signal.emit("로그인 실패.")
        else:
            self.log_signal.emit("USER를 입력하세요.")

        self.log_signal.emit(f'크롤링 종료')


    def _logout(self, user):
        # 로그아웃 버튼 클릭 (text 기반)
        logout_buttons = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'top_link'))
        )

        for button in logout_buttons:
            if button.text.strip() == "로그아웃":
                button.click()
                self.log_signal.emit(f"{user['ID']} 로그아웃 성공!")
                time.sleep(2)
                break


    def _login(self, user):
        try:
            login_url = f'{self.baseUrl}/login'
            self.driver.get(login_url)
            time.sleep(2.5)

            # 이메일 입력
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
            )
            email_input.send_keys(user['ID'])

            # 비밀번호 입력
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
            )
            password_input.send_keys(user['PASSWORD'])

            # 로그인 버튼 클릭
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            login_button.click()

            time.sleep(2)

            # 로그인 완료 대기 (쿠키 확보)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.cookies = self._get_cookies_from_browser()

            if self.cookies:
                self.get_access_token()
                self.log_signal.emit(f"로그인 성공!")
            return True

        except Exception as e:
            error_message = f"로그인 중 에러 발생: {str(e)}"
            self.log_signal.emit(error_message)

            # 드라이버 종료
            if self.driver:
                self.driver.quit()

            return False


    def _get_cookies_from_browser(self):
        cookies = self.driver.get_cookies()

        if not cookies:  # 쿠키가 없는 경우
            return None

        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return cookie_dict


    def get_access_token(self):
        try:
            # JavaScript 실행하여 localStorage 값 가져오기
            token_value = self.driver.execute_script("return localStorage.getItem('_token.local.p-2');")

            if token_value:
                self.access_token = f"Bearer {token_value}"
                self.log_signal.emit("토큰 성공")
            else:
                raise Exception("🔴 '_token.local.p-2' key not found in localStorage")

        except Exception as e:
            self.log_signal.emit(f"❌ 오류 발생: {e}")
            self.access_token = None  # 실패 시 None으로 설정


    def _get_sold_out_list(self, cursor):

        tab="finished"
        status="canceled"
        request_key=""
        url = f"https://api.kream.co.kr/api/o/asks/?cursor={cursor}&tab={tab}&status={status}&request_key={request_key}"

        url_pattern = re.compile(r"https://kream\.co\.kr/my/selling/(\d+)")

        headers = {
            "authority": "api.kream.co.kr",
            "method": "GET",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": "https://kream.co.kr",
            "referer": "https://kream.co.kr/my/selling?tab=finished",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "authorization": self.access_token,
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "x-kream-api-version": "41",
            "x-kream-device-id": "web;fcb9350d-91d8-4a78-945d-e941984c6386",
            "x-kream-web-build-version": "6.7.4",
            "x-kream-web-request-secret": "kream-djscjsghdkd"
        }

        extracted_ids = []

        try:
            response = requests.get(url, headers=headers, cookies=self.cookies)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

            # 응답 JSON 파싱 및 출력
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    for item in data["items"]:
                        if item.get("actions", []):
                            for action in item.get("actions", []):
                                if "value" in action and "https://kream.co.kr/my/selling/" in action["value"]:
                                    match = url_pattern.search(action["value"])
                                    if match:
                                        extracted_ids.append(match.group(1))  # 숫자 부분만 저장
            return extracted_ids
        except requests.exceptions.RequestException as e:
            return []


    def _setup_driver(self):

        chrome_options = Options()  # 크롬 옵션 설정

        # 헤드리스 모드로 실행
        chrome_options.add_argument("--headless")

        # GPU 비활성화
        chrome_options.add_argument("--disable-gpu")

        # 샌드박스 보안 모드를 비활성화합니다.
        chrome_options.add_argument("--no-sandbox")

        # /dev/shm 사용 비활성화
        chrome_options.add_argument("--disable-dev-shm-usage")

        # 시크릿 모드로 실행
        chrome_options.add_argument("--incognito")

        # 사용자 에이전트를 설정하여 브라우저의 기본값 대신 특정 값을 사용하게 합니다.
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')

        # 웹 드라이버를 사용한 자동화임을 나타내는 Chrome의 플래그를 비활성화하여 자동화 도구의 사용을 숨깁니다.
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # 자동화 확장 기능의 사용을 비활성화합니다.
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 사용하여 호환되는 크롬 드라이버를 자동으로 다운로드하고 설치합니다.
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # 크롬 개발자 프로토콜 명령을 실행하여 브라우저의 navigator.webdriver 속성을 수정함으로써, 자동화 도구 사용을 감지하고 차단하는 스크립트를 우회합니다.
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            '''
        })

        return driver


    # [공통] 브라우저 닫기
    def _close_chrome_processes(self):
        """모든 Chrome 프로세스를 종료합니다."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()  # Chrome 프로세스를 종료
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


    def _setup_driver_main(self):
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


    def get_progress_status_text(self, progress):
        # progress의 title이 '진행 상황'인지 확인합니다.
        if progress and progress.get("title") == "진행 상황":
            for item in progress.get("items", []):
                description = item.get("description")
                if description and isinstance(description, dict):
                    text = description.get("text", "")
                    if text:  # text 값이 존재하면 즉시 반환
                        return text
        return ""  # 해당 조건을 만족하는 text가 없으면 빈 문자열 반환


    def get_transaction_time(self, items):
        for section in items:
            for item in section.get("items", []):
                title_obj = item.get("title")  # title 객체 가져오기

                if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                    title_text = title_obj.get("text", "")

                    if title_text == "거래 일시":
                        description_obj = item.get("description", {})

                        if isinstance(description_obj, dict):  # description이 dict인지 확인
                            return self.format_date_kst(description_obj.get("text", ""))

        return ""  # "거래 일시"가 없으면 None 반환


    def get_penalty_info(self, items):
        for section in items:
            for item in section.get("items", []):
                title_obj = item.get("title")  # title 객체 가져오기

                if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                    title_text = title_obj.get("text", "")

                    if title_text == "페널티":
                        description_obj = item.get("description", {})

                        if isinstance(description_obj, dict):  # description이 dict인지 확인
                            return description_obj.get("text", "")


        return ""  # "페널티"가 없으면 None 반환


    def format_date_kst(self, date_str):
        try:
            # UTC 기준 시간 변환
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

            # 한국 시간(KST)으로 변환 (UTC+9)
            dt_kst = dt + timedelta(hours=9)

            return dt_kst.strftime("%Y-%m-%d %I:%M:%S %p")
        except Exception as e:
            self.log_signal.emit(f'에러 {e}')
            return ""


    def get_penalty_payment_date(self, items):
        for section in items:
            for item in section.get("items", []):
                title_obj = item.get("title")  # title 객체 가져오기

                if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                    title_text = title_obj.get("text", "")

                    if title_text == "페널티 결제일":
                        description_obj = item.get("description", {})

                        if isinstance(description_obj, dict):  # description이 dict인지 확인
                            return self.format_date_kst((description_obj.get("text", "")))

        return ""  # "페널티 결제일"이 없으면 None 반환


    def get_instant_sale_price(self, items):
        for section in items:
            for item in section.get("items", []):
                title_obj = item.get("title")  # title 객체 가져오기

                if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                    title_text = title_obj.get("text", "")

                    if title_text == "즉시 판매가":
                        description_obj = item.get("description", {})

                        if isinstance(description_obj, dict):  # description이 dict인지 확인
                            lookups = description_obj.get("lookups", [])
                            if lookups and isinstance(lookups, list) and len(lookups) > 0:
                                return lookups[0].get("text", "")  # 첫 번째 lookup의 text 반환

        return ""  # "즉시 판매가"가 없으면 None 반환


    def get_tracking_info(self, data):
        tracking_obj = data.get("tracking", {})  # tracking 객체 가져오기

        if isinstance(tracking_obj, dict):  # dict인지 확인
            return tracking_obj.get("tracking_code")  # 존재하면 반환

        return ""  # tracking_code가 없으면 None 반환


    def extract_fail_and_success_reason(self, data):
        fail_reason = ""
        success_reason = ""

        # 최상위 items 배열을 순회합니다.
        for section in data.get("items", []):
            section_title = section.get("title")

            # 불합격/페널티 사유 섹션인 경우
            if section_title == "불합격/페널티 사유":
                items = section.get("items", [])
                if items:
                    title_obj = items[0].get("title", {})
                    fail_reason = title_obj.get("text", "")

            # 95점 합격 사유 섹션인 경우
            elif section_title == "95점 합격 사유":
                items = section.get("items", [])
                if items:
                    title_obj = items[0].get("title", {})
                    success_reason = title_obj.get("text", "")

        return fail_reason, success_reason

    # API 요청 및 데이터 파싱 함수
    def fetch_product_data(self, product_id):
        url = f"https://api.kream.co.kr/api/m/asks/{product_id}"
        headers = {
            "authority": "api.kream.co.kr",
            "method": "GET",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": self.access_token,
            "origin": "https://kream.co.kr",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "x-kream-api-version": "41",
            "x-kream-device-id": "web;fcb9350d-91d8-4a78-945d-e941984c6386",
            "x-kream-web-build-version": "6.7.4",
            "x-kream-web-request-secret": "kream-djscjsghdkd"
        }

        response = requests.get(url, headers=headers, cookies=self.cookies)

        if response.status_code == 200:
            data = response.json()

            progress_data = data.get("progress", {})

            progress_text = self.get_progress_status_text(progress_data)

            transaction_time = self.get_transaction_time(data.get("items", []))

            penalty_info = self.get_penalty_info(data.get("items", []))

            penalty_payment_date = self.get_penalty_payment_date(data.get("items", []))

            instant_sale_price = self.get_instant_sale_price(data.get("items", []))

            tracking_info = self.get_tracking_info(data)

            fail_reason, success_reason = self.extract_fail_and_success_reason(data)

            return {
                "주문번호": data.get("oid"),
                "사이즈": data.get("option"),
                "영문명": data.get("product", {}).get("release", {}).get("name"),
                "한글명": data.get("product", {}).get("release", {}).get("translated_name"),
                "모델번호": data.get("product", {}).get("release", {}).get("style_code"),
                "진행 상황": progress_text,
                "즉시 판매가": instant_sale_price,
                "거래 일시": transaction_time,
                "페널티": penalty_info,
                "페널티 결제일": penalty_payment_date,
                "페널티 결제 정보": data.get("payment", {}).get("pg_display_title", {}),
                "발송 정보": tracking_info,
                "불합격/페널티 사유": fail_reason,
                "95점 합격 사유": success_reason
            }
        else:
            print(f"Failed to fetch data for product {product_id}, status code: {response.status_code}")
            return {}

    # [공통] csv 남은 데이터 처리
    def _remain_data_set(self):
        # 남은 데이터 저장
        if self.result_list:
            self._save_to_csv_append(self.result_list)

        # CSV 파일을 엑셀 파일로 변환
        try:
            excel_file_name = self.file_name.replace('.csv', '.xlsx')  # 엑셀 파일 이름으로 변경
            self.log_signal.emit(f"CSV 파일을 엑셀 파일로 변환 시작: {self.file_name} → {excel_file_name}")
            df = pd.read_csv(self.file_name)  # CSV 파일 읽기
            df.to_excel(excel_file_name, index=False)  # 엑셀 파일로 저장

            # 마지막 세팅
            pro_value = 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)

            self.log_signal.emit(f"엑셀 파일 변환 완료: {excel_file_name}")

            self.log_signal.emit(f'종료 수 : {self.end_cnt}')

            if self.end_cnt == len(self.user_list):
                self.progress_end_signal.emit()
            else:
                self.log_signal.emit(f'다음 작업 준비중입니다. 잠시만 기다려주세요...')

        except Exception as e:
            self.log_signal.emit(f"엑셀 파일 변환 실패: {e}")

    # [공통] csv 데이터 추가
    def _save_to_csv_append(self, results):
        self.log_signal.emit("CSV 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(self.file_name):
                # 파일이 없으면 새로 생성 및 저장
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, index=False, encoding='utf-8-sig')

                self.log_signal.emit(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                # 파일이 있으면 append 모드로 데이터 추가
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
                self.log_signal.emit(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.emit(f"CSV 저장 실패: {e}")

    # [공통] 프로그램 중단
    def stop(self):
        self.log_signal.emit(f'종료 수 : {self.end_cnt}')
        if self.end_cnt == len(self.user_list):
            if self.driver:
                self.driver.quit()
            self.running = False
