import os
import ssl
import time
from urllib.parse import urlparse, parse_qs
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.utils.time_utils import get_current_yyyymmddhhmmss
from urllib.parse import quote
import threading
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By

ssl._create_default_https_context = ssl._create_unverified_context

# API
class ApiOkmallSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    msg_signal = pyqtSignal(str, str, object)

    def __init__(self, url_list, user):
        super().__init__()
        self.baseUrl = "https://www.okmall.com"
        self.baseUrl_login = "https://www.okmall.com/members/login"
        self.sess = requests.Session()
        self.url_list = url_list
        self.user = user
        self.driver = None
        self.version = ""
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "okmall"
        self.excel_filename = ""
        self.brand_obj_list = []
        self.product_obj_list = []
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.current_page = 0
        self.before_pro_value = 0

    # 프로그램 실행
    def run(self):
        self.log_signal.emit("크롤링 시작")

        # 브랜드 리스트 세팅 전체 갯수 조회
        self.brand_init()

        # 제품 목록 가져오기
        self.brand_obj_list_call_product_list()

        # 마지막 세팅
        pro_value = 1000000
        self.progress_signal.emit(self.before_pro_value, pro_value)

        self.log_signal.emit(f"=============== 처리 데이터 수 : {self.total_cnt}")
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 브랜드에서 제품 목록 호출
    def brand_obj_list_call_product_list(self):
        if self.brand_obj_list:
            for index, brand_obj in enumerate(self.brand_obj_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break
                self.product_list_get(index, brand_obj)

    # 제품 목록 가져오기
    def product_list_get(self, index, brand_obj):
        if brand_obj:
            total_page = brand_obj['total_page']
            brand = brand_obj['brand']
            for idx, page in enumerate(range(1, total_page + 1), start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_page += 1
                brd_ob = self.brand_api_data(brand, page, False)
                product_list = brd_ob['product_list']
                self.product_detail(index, idx, product_list, brand_obj)
                time.sleep(0.5)

    # 제품 상세정보
    def product_detail(self, index, idx, product_list, brand_obj):
        if product_list:
            for ix, product in enumerate(product_list, start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_cnt += 1
                prdt_obj_list = self.product_api_data(product)
                self.product_obj_list.extend(prdt_obj_list)
                self.save_to_excel_one_by_one(prdt_obj_list, self.excel_filename)
                now_per = divide_and_truncate_per(self.current_cnt, self.total_cnt)

                self.log_signal.emit("\n")
                self.log_signal.emit("\n")
                self.log_signal.emit("\n")
                self.log_signal.emit("====================================================================================================")
                self.log_signal.emit(f"전체 브랜드({index}/{len(self.brand_obj_list)})[{now_per}%],  전체 페이지({self.current_page}/{self.total_pages}),  전체 상품({self.current_cnt}/{self.total_cnt})")
                self.log_signal.emit("----------------------------------------------------------------------------------------------------")
                self.log_signal.emit(f"현재 브랜드({brand_obj['brand']}),  현재 페이지({idx}/{brand_obj['total_page']}),  현재 상품({ix}/{brand_obj['total_cnt']})")
                self.log_signal.emit(f"현재 상품 상세 : {prdt_obj_list}")
                self.log_signal.emit("====================================================================================================")
                self.log_signal.emit("\n")
                self.log_signal.emit("\n")
                self.log_signal.emit("\n")

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                time.sleep(1)

    # 엑셀 저장
    def save_to_excel_one_by_one(self, results, file_name, sheet_name='Sheet1'):
        try:
            # 결과 데이터가 비어있는지 확인
            if not results:
                self.log_signal.emit("결과 데이터가 비어 있습니다.")
            else:
                # 파일이 존재하는지 확인
                if os.path.exists(file_name):
                    # 파일이 있으면 기존 데이터 읽어오기
                    df_existing = pd.read_excel(file_name, sheet_name=sheet_name, engine='openpyxl')

                    # 새로운 데이터를 DataFrame으로 변환
                    df_new = pd.DataFrame(results)

                    # 기존 데이터에 새로운 데이터 추가
                    for index, row in df_new.iterrows():
                        # 기존 DataFrame에 한 행씩 추가하는 부분
                        df_existing = pd.concat([df_existing, pd.DataFrame([row])], ignore_index=True)

                    # 엑셀 파일에 덧붙이기 (index는 제외)
                    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df_existing.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # 파일이 없으면 새로 생성
                    df = pd.DataFrame(results)
                    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

        except Exception as e:
            self.log_signal.emit(f'엑셀 에러 발생: {e}')

    # url param 가져오기
    def get_query_params(self, url, name):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get(name, [None])[0]

    # 브랜드 api_data
    def product_api_data(self, url):
        product_detail_list = []
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "host": "www.okmall.com",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
        try:
            response = self.sess.get(url, headers=headers)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
            soup = BeautifulSoup(response.text, 'html.parser')

            # 브랜드명
            brand_tag = soup.select_one("span.brand_tit")
            brand = brand_tag.get_text(strip=True) if brand_tag else ""

            # 상품명
            season = soup.select_one("h3#ProductNameArea .prd_name_season")
            name = soup.select_one("h3#ProductNameArea .prd_name")
            more = soup.select_one("h3#ProductNameArea .prd_name_more")
            product_name = " ".join(filter(None, [
                season.get_text(strip=True) if season else "",
                name.get_text(strip=True) if name else "",
                more.get_text(strip=True) if more else ""
            ]))

            # 가격 (div.last_price 내부 span.price만 타겟)
            price = ""
            price_tag = soup.select_one("div.last_price span.price")
            if price_tag:
                price_text = price_tag.get_text(strip=True).replace(",", "").replace("원", "")
                # 숫자만 필터링
                price_digits = ''.join(filter(str.isdigit, price_text))
                if price_digits:
                    price = int(price_digits)

            # 사이즈 정보 추출
            size_rows = soup.select('table.shoes_size tr[name="selectOption"]')
            for row in size_rows:
                tds = row.select("td.t_center")
                if len(tds) >= 2:
                    size = tds[1].get_text(strip=True)
                    obj = {
                        "브랜드명": brand,
                        "상품명": product_name,
                        "가격": price,
                        "택 사이즈": size,
                        "상품 링크": url
                    }
                    product_detail_list.append(obj)
        except requests.exceptions.RequestException as e:
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            print(f"알 수 없는 에러 발생: {e}")
        finally:
            return product_detail_list

    # 브랜드 리스트 초기화
    def brand_init(self):
        if self.url_list:
            self.log_signal.emit("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
            self.login()
            self.log_signal.emit("크롤링 사이트 인증에 성공하였습니다.")
            current_time = get_current_yyyymmddhhmmss()
            self.excel_filename = f"{self.company_name}_{current_time}.xlsx"
            self.log_signal.emit(f"전체 상품수 계산을 시작합니다. 잠시만 기다려주세요.")
            self.brand_obj_list = self.brand_obj_list_get()
            self.total_cnt = sum(int(obj['total_cnt']) for obj in self.brand_obj_list)
            self.total_pages = sum(int(obj['total_page']) for obj in self.brand_obj_list)
            self.log_signal.emit(f"전체 브랜드수 {len(self.brand_obj_list)}개")
            self.log_signal.emit(f"전체 상품수 {self.total_cnt} 개")
            self.log_signal.emit(f"전체 페이지수 {self.total_pages} 개")

    # 브랜드 리스트 가져오기
    def brand_obj_list_get(self):
        brand_obj_list = []
        for index, url in enumerate(self.url_list, start=1):
            brand = self.get_query_params(url, 'brand')
            brand_obj = self.brand_api_data(brand, 1, True)
            time.sleep(0.5)
            brand_obj_list.append(brand_obj)
            self.log_signal.emit(f"brand: {brand_obj}")
            time.sleep(0.5)
        return brand_obj_list

    # 브랜드 api data
    def brand_api_data(self, brand, page, count_flag):
        obj = {
            'brand': brand,
            'page': page,
            'total_cnt': 0,
            'total_page': 0,
            'product_list': []
        }
        url = "https://www.okmall.com/products/list"
        payload = {
            "key_type": "on",
            "brand": f"{brand}",
            "search_keyword": "",
            "detail_search_keyword": "",
            "page": page
        }
        encoded_brand = quote(brand)
        headers = {
            "accept": "text/html, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "host": "www.okmall.com",
            "referer": f"https://www.okmall.com/products/list?brand={encoded_brand}",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",           # CORS 상황이면 empty, 일반 페이지는 document
            "sec-fetch-mode": "cors",            # CORS 요청인 경우
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-csrf-token": "",                  # 쿠키에서 XSRF-TOKEN 추출해서 여기에 채워주세요
            "x-requested-with": "XMLHttpRequest"
        }

        xsrf = None
        for cookie in self.sess.cookies:
            if cookie.name == "XSRF-TOKEN" and cookie.domain == "" and cookie.path == "/":
                xsrf = cookie.value
                break

        if xsrf:
            headers["x-csrf-token"] = xsrf

        try:
            response = self.sess.get(url, headers=headers, params=payload)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
            soup = BeautifulSoup(response.text, 'html.parser')
            if count_flag:
                input_tag = soup.find('input', {'name': 'total_count'})
                if input_tag:
                    value = input_tag.get('value')  # value 값 반환
                    total_cnt = int(value)
                    quotient, remainder = calculate_divmod(total_cnt, 80)
                    total_page = quotient + 1
                    obj['page'] = page
                    obj['total_cnt'] = total_cnt
                    obj['total_page'] = total_page
            items = soup.find_all(class_="item_box")
            product_list = []
            for item in items:
                # 두 번째 <a> 태그 (상품 링크)
                p_tag = item.find("p", attrs={"name": "shortProductName"})
                if p_tag:
                    a_tags = p_tag.find_all("a")
                    if len(a_tags) >= 2:
                        href = a_tags[1].get("href", "")
                        url = href if href.startswith("http") else self.baseUrl + href
                        product_list.append(url)
            obj['product_list'] = product_list

        except requests.exceptions.RequestException as e:
            # 요청 관련 에러 처리
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            # 일반 에러 처리
            print(f"알 수 없는 에러 발생: {e}")
        finally:
            return obj


    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False

    # 로그인 쿠키가져오기
    def login(self):
        webdriver_options = webdriver.ChromeOptions()

        # 이 옵션은 Chrome이 자동화 도구(예: Selenium)에 의해 제어되고 있다는 것을 감지하지 않도록 만듭니다.
        # AutomationControlled 기능을 비활성화하여 webdriver가 브라우저를 자동으로 제어하는 것을 숨깁니다.
        # 이는 일부 웹사이트에서 자동화 도구가 감지되는 것을 방지하는 데 유용합니다.
        ###### 자동 제어 감지 방지 #####
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')

        # Chrome 브라우저를 실행할 때 자동으로 브라우저를 최대화 상태로 시작합니다.
        # 이 옵션은 사용자가 브라우저를 처음 실행할 때 크기가 자동으로 최대로 설정되도록 합니다.
        ##### 화면 최대 #####

        # 화면 크기 가져오기 (예: 너비 1920, 높이 1080 기준)
        screen_width, screen_height = shutil.get_terminal_size((1920, 1080))

        # 원하는 창 크기 계산
        window_width = screen_width // 3
        window_height = screen_height

        # 크롬 옵션 설정
        webdriver_options.add_argument(f"--window-size={window_width},{window_height}")
        webdriver_options.add_argument("--window-position=0,0")  # 왼쪽 상단에 붙이기


        # headless 모드로 Chrome을 실행합니다.
        # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
        # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
        ##### 화면이 안보이게 함 #####
        # webdriver_options.add_argument("--headless")

        #이 설정은 Chrome의 자동화 기능을 비활성화하는 데 사용됩니다.
        #기본적으로 Chrome은 자동화가 활성화된 경우 브라우저의 콘솔에 경고 메시지를 표시합니다.
        #이 옵션을 설정하면 이러한 경고 메시지가 나타나지 않도록 할 수 있습니다.
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
        self.driver = webdriver.Chrome(options=webdriver_options)
        self.driver.set_page_load_timeout(120)
        self.driver.get(self.baseUrl_login)
        self.version = self.driver.capabilities["browserVersion"]

        # 3초 대기
        time.sleep(2)

        try:
            # ID 입력
            id_input = self.driver.find_element(By.NAME, "txt_id")
            id_input.clear()
            id_input.send_keys(self.user.get("id", ""))

            # PW 입력
            pw_input = self.driver.find_element(By.NAME, "txt_pw")
            pw_input.clear()
            pw_input.send_keys(self.user.get("pw", ""))

            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login-default")
            login_button.click()

            time.sleep(3)

            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.sess.cookies.set(cookie['name'], cookie['value'])

        except Exception as e:
            print(f"[❌ 로그인 자동 입력 오류] {e}")


