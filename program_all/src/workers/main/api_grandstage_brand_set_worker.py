import os
import ssl
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.core.global_state import GlobalState
from src.utils.str_utils import get_query_params
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


# API
class ApiGrandstageBrandSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://grandstage.a-rt.com/"
        self.url_list = []
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "grandstage_brand"
        self.site_name = "grandstage_brand"
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

            self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.excel_filename, self.columns)

            # 브랜드 리스트 세팅 전체 갯수 조회
            self.brand_init()

            # 제품 목록 가져오기
            self.brand_obj_list_call_product_list()

            # CSV -> 엑셀 변환
            self.excel_driver.convert_csv_to_excel_and_delete(self.excel_filename)

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


        self.driver = self.selenium_driver.start_driver(1200)

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
                now_per = divide_and_truncate_per(self.current_cnt, self.total_cnt)

                self.log_signal.emit("====================================================================================================")
                self.log_signal.emit(f"전체 브랜드({index}/{len(self.brand_obj_list)})[{now_per}%],  전체 페이지({self.current_page}/{self.total_pages}),  전체 상품({self.current_cnt}/{self.total_cnt})")
                self.log_signal.emit("----------------------------------------------------------------------------------------------------")
                self.log_signal.emit(f"현재 브랜드({brand_obj['brand_name_en']}),  현재 페이지({idx}/{brand_obj['total_page']}),  현재 상품({ix}/{brand_obj['total_cnt']})")
                self.log_signal.emit(f"현재 상품 상세 : {prdt_obj_list}")
                self.log_signal.emit("====================================================================================================")

                self.excel_driver.append_to_csv(self.excel_filename, prdt_obj_list, self.columns)

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                time.sleep(1)

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
            json_data = self.api_client.get(url, headers=headers, params=payload)
            sell_amt = json_data.get("displayProductPrice", "")
            if sell_amt:
                sell_amt = f"{sell_amt:,}"
            prdt_name = json_data.get("prdtName")
            brand_en_name = json_data.get("brand", {}).get("brandEnName", "")
            brand_name = json_data.get("brand", {}).get("brandName", "")
            style_info = ""
            if brand_en_name in ("NIKE", "JORDAN"):
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
        return product_detail_list

    # 브랜드 리스트 초기화
    def brand_init(self):
        if self.url_list:
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
            response = self.api_client.get(url, headers=headers, params=payload)
            soup = BeautifulSoup(response, 'html.parser')
            links = soup.find_all('a', class_='prod-link')
            product_list = []
            if links and len(links) > 0:
                product_list = [link.get('href') for link in links if link.get('href')]
            # input_tag = soup.find('input', id="GROUP_COUNT_CHNNL_NO_10001")
            # 수정 2024-02-24
            input_tag = soup.find('input', id="GROUP_COUNT_CHNNL_NO_10002") or soup.find('input', id="GROUP_COUNT_CHNNL_NO_10001")
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
            data = self.api_client.get(url, headers=headers, params=payload)
            brand_name_list = data.get("SELECT", {}).get("BRAND_LIST", [])
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






