import os
import os
import ssl
import time
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.core.global_state import GlobalState
from src.utils.str_utils import get_query_params
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker

# API
class ApiOnthespotSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://www.onthespot.co.kr/"
        self.sess = requests.Session()
        self.url_list = []
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "onthespot"
        self.site_name = "onthespot"
        self.excel_filename = ""
        self.brand_obj_list = []
        self.product_obj_list = []
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.current_page = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

    # 초기화
    def init(self):
        self.driver_set(True)
        self.driver.get(self.base_main_url)
        return True

    # 메인
    def main(self):
        try:
            self.set_cookies()

            self.log_signal.emit("크롤링 시작")

            self.url_list = [
                str(row[k]).strip()
                for row in self.excel_data_list
                for k in row.keys()
                if k.lower() == "url" and row.get(k) and str(row[k]).strip()
            ]

            # 브랜드 리스트 세팅 전체 갯수 조회
            self.brand_init()

            # 제품 목록 가져오기
            self.brand_obj_list_call_product_list()

            return True
        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False


    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)

        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)

    # 쿠키세팅
    def set_cookies(self):
        self.log_signal_func("📢 쿠키 세팅 시작")
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)
        self.log_signal_func("📢 쿠키 세팅 완료")
        time.sleep(2)

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
                prdt_no = get_query_params(product, "prdtNo")
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

    # 브랜드 api_data
    def product_api_data(self, prdt_no):
        product_detail_list = []
        url = f"https://www.onthespot.co.kr/product/info"
        payload = {
            "prdtNo": f"{prdt_no}"
        }
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.onthespot.co.kr",
            "referer": f"https://www.onthespot.co.kr/product?prdtNo={prdt_no}",
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
            json_data = self.api_client.get(url, headers=headers, params=payload)
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
                        "상품 링크": f"https://www.onthespot.co.kr/product?prdtNo={prdt_no}"
                    }
                    product_detail_list.append(extracted_data)
        except requests.exceptions.RequestException as e:
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            print(f"알 수 없는 에러 발생: {e}")
        return product_detail_list

    # 브랜드 리스트 초기화
    def brand_init(self):
        if self.url_list:
            self.excel_filename = self.file_driver.get_excel_filename(self.site_name)
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
            brand_no = get_query_params(url, 'brandNo')
            brand_obj = self.brand_api_data(brand_no, 1)
            time.sleep(0.5)
            brand_name_list = self.brand_api_name_list(brand_no)
            if brand_name_list:
                brand_obj['brand_name_ko'] = brand_name_list[1]
                brand_obj['brand_name_en'] = brand_name_list[0]
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
        url = "https://www.onthespot.co.kr/display/search-word/result/list"
        payload = {
            "searchPageType": "brand",
            "page": f"{page}",
            "brandNo": f"{brand_no}",
            "sort": "latest",
            "perPage": "40",
            # "_": "1736952631519"
        }
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.onthespot.co.kr",
            "referer": f"https://www.onthespot.co.kr/product/brand/page?brandNo={brand_no}",
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
            response = self.api_client.get(url, headers=headers, params=payload)
            soup = BeautifulSoup(response, 'html.parser')
            links = soup.find_all('a', class_='prod-link')
            product_list = []
            if links and len(links) > 0:
                product_list = [link.get('href') for link in links if link.get('href')]
            input_tag = soup.find('input', {'name': 'searchTotalCount'})
            if input_tag:
                value = input_tag.get('value')  # value 값 반환
                total_cnt = int(value)
                quotient, remainder = calculate_divmod(total_cnt, 40)
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
        return obj

    # 브랜드 api name
    def brand_api_name_list(self, brand_no):
        brand_name_list = ["", ""]
        url = "https://www.onthespot.co.kr/product/brand/page"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "www.onthespot.co.kr",
            "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": "Windows",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        payload = {
            "brandNo": brand_no
        }
        try:
            response = self.api_client.get(url, headers=headers, params=payload)
            soup = BeautifulSoup(response, 'html.parser')
            og_title = soup.find("meta", property="og:title")
            if og_title:
                content = og_title.get("content", "")
                if content:
                    brand_name_list = content.split(" | ")
        except requests.exceptions.RequestException as e:
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            print(f"알 수 없는 에러 발생: {e}")
        return brand_name_list


    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()



