import os
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

ssl._create_default_https_context = ssl._create_unverified_context

# API
class ApiGrandstageSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    def __init__(self, url_list):
        super().__init__()
        self.baseUrl = "https://grandstage.a-rt.com/"
        self.sess = requests.Session()
        self.url_list = url_list
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "grandstage"
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
            brand_no = brand_obj['brand_no']
            for idx, page in enumerate(range(1, total_page + 1), start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_page += 1
                brd_ob = self.brand_api_data(brand_no, page)
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
                prdt_no = self.get_query_params(product, "prdtNo")
                prdt_obj_list = self.product_api_data(prdt_no)
                self.product_obj_list.extend(prdt_obj_list)
                self.save_to_excel_one_by_one(prdt_obj_list, self.excel_filename)
                now_per = divide_and_truncate_per(self.current_cnt, self.total_cnt)
                self.log_signal.emit("====================================================================================================")
                self.log_signal.emit(f"전체 브랜드({index}/{len(self.brand_obj_list)})[{now_per}%],  전체 페이지({self.current_page}/{self.total_pages}),  전체 상품({self.current_cnt}/{self.total_cnt})")
                self.log_signal.emit("----------------------------------------------------------------------------------------------------")
                self.log_signal.emit(f"현재 브랜드({brand_obj['brand_name_en']}),  현재 페이지({idx}/{brand_obj['total_page']}),  현재 상품({ix}/{brand_obj['total_cnt']})")
                self.log_signal.emit(f"현재 상품 상세 : {prdt_obj_list}")
                self.log_signal.emit("====================================================================================================")

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
    def product_api_data(self, prdt_no):
        product_detail_list = []
        url = f"https://grandstage.a-rt.com/product/info"
        payload = {
            "prdtNo": f"{prdt_no}"
        }
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "grandstage.a-rt.com",
            "referer": f"https://grandstage.a-rt.com/product/new?prdtNo={prdt_no}",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }
        try:
            response = self.sess.get(url, headers=headers, params=payload)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
            json_data = response.json()
            sell_amt = json_data.get("displayProductPrice", "")
            if sell_amt:
                sell_amt = f"{sell_amt:,}"
            prdt_name = json_data.get("prdtName")
            brand_en_name = json_data.get("brand", {}).get("brandEnName", "")
            brand_name = json_data.get("brand", {}).get("brandName", "")
            style_info = ""
            if "NIKE" == brand_en_name:
                style_info = f"{json_data.get('styleInfo')}-{json_data.get('prdtColorInfo')}"
            else:
                style_info = json_data.get("styleInfo")

            for option in json_data.get("productOption", []):
                optnName = option.get("optnName")
                total_stock_qty = option.get("totalStockQty", 0)
                if total_stock_qty != 0:
                    extracted_data = {
                        "브랜드명": brand_name,
                        "스타일코드": style_info,
                        "사이즈": optnName,
                        "가격": sell_amt,
                        "상품 링크": f"https://grandstage.a-rt.com/product/new?prdtNo={prdt_no}"
                    }
                    product_detail_list.append(extracted_data)
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
            brand_no = self.get_query_params(url, 'brandNo')
            brand_obj = self.brand_api_data(brand_no, 1)
            time.sleep(0.5)
            brand_name_list = self.brand_api_name_list(brand_no)
            if brand_name_list:
                brand_entry = brand_name_list[0]  # 첫 번째 항목
                brand_name = brand_entry.split(",")  # 쉼표로 분리하여 첫 번째 값 추출
                brand_obj['brand_name_ko'] = brand_name[2]
                brand_obj['brand_name_en'] = brand_name[0]
            brand_obj_list.append(brand_obj)
            self.log_signal.emit(f"brand: {brand_obj}")
            time.sleep(0.5)
        return brand_obj_list

    # 브랜드 api data
    def brand_api_data(self, brand_no, page):
        obj = {
            'brand_no': brand_no,
            'page': page,
            'total_cnt': 0,
            'total_page': 0,
            'brand_name_ko': '',
            'brand_name_en': '',
            'product_list': []
        }
        url = "https://grandstage.a-rt.com/display/search-word/result/list"
        payload = {
            "searchPageType": "brand",
            "channel": "10002",
            "page": f"{page}",
            "pageColumn": "4",
            "deviceCode": "10000",
            "firstSearchYn": "Y",
            "tabGubun": "total",
            "searchPageGubun": "brsearch",
            "searchRcmdYn": "Y",
            "brandNo": f"{brand_no}",
            "searchBrandNo": f"{brand_no}",
            "brandPrdtArtDispYn": "Y",
            "sort": "latest",
            "perPage": "30",
            "rdoProdGridModule": "col3",
            # "_": "1736952631519"
        }
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "grandstage.a-rt.com",
            "referer": f"https://grandstage.a-rt.com/product/brand/page/main?brandNo={brand_no}&page={page}",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }
        try:
            response = self.sess.get(url, headers=headers, params=payload)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', class_='prod-link')
            product_list = []
            if links and len(links) > 0:
                product_list = [link.get('href') for link in links if link.get('href')]
            input_tag = soup.find('input', id="GROUP_COUNT_CHNNL_NO_10001")
            if input_tag:
                value = input_tag.get('value')  # value 값 반환
                total_cnt = int(value)
                quotient, remainder = calculate_divmod(total_cnt, 30)
                total_page = quotient + 1
                obj['page'] = page
                obj['total_cnt'] = total_cnt
                obj['total_page'] = total_page
                obj['product_list'] = product_list
        except requests.exceptions.RequestException as e:
            # 요청 관련 에러 처리
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            # 일반 에러 처리
            print(f"알 수 없는 에러 발생: {e}")
        finally:
            return obj

    # 브랜드 api name
    def brand_api_name_list(self, brand_no):
        brand_name_list = []
        url = "https://grandstage.a-rt.com/display/search-word/smart-option/list"
        payload = {
            "searchPageType": "brand",
            "channel": "10002",
            "page": "1",
            "pageColumn": "4",
            "deviceCode": "10000",
            "firstSearchYn": "Y",
            "tabGubun": "total",
            "searchPageGubun": "brsearch",
            "searchRcmdYn": "Y",
            "brandNo": f"{brand_no}",
            "searchBrandNo": f"{brand_no}",
            # "_": "1736952631519"
        }
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "grandstage.a-rt.com",
            "referer": f"https://grandstage.a-rt.com/product/brand/page/main?brandNo=={brand_no}",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }
        try:
            response = self.sess.get(url, headers=headers, params=payload)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
            data = response.json()
            brand_name_list = data.get("SELECT", {}).get("BRAND_LIST", [])
        except requests.exceptions.RequestException as e:
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            print(f"알 수 없는 에러 발생: {e}")
        finally:
            return brand_name_list

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
        webdriver_options.add_argument("--start-maximized")

        # headless 모드로 Chrome을 실행합니다.
        # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
        # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
        ##### 화면이 안보이게 함 #####
        webdriver_options.add_argument("--headless")

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
        self.driver.get(self.baseUrl)
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])
        self.version = self.driver.capabilities["browserVersion"]
        self.headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.version}"
        }
        self.driver.quit()






