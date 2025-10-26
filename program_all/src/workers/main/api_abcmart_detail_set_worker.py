import os
import os
import ssl
import time
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.utils.str_utils import get_query_params
from src.workers.api_base_worker import BaseApiWorker
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from urllib.parse import urlparse, parse_qs

# API
class ApiAbcmartDetailSetLoadWorker(BaseApiWorker):


    def __init__(self):
        super().__init__()
        self.file_driver = None
        self.excel_driver = None
        self.url_list = []
        self.user = None
        self.driver = None
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "abcmart_detail"
        self.site_name = "abcmart_detail"
        self.csv_filename = ""
        self.product_obj_list = []
        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }


    # 초기화
    def init(self):
        self.driver_set()
        return True

    # 메인
    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            self.url_list = [
                str(row[k]).strip()
                for row in self.excel_data_list
                for k in row.keys()
                if k.lower() == "url" and row.get(k) and str(row[k]).strip()
            ]

            # csv파일 만들기
            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.csv_filename, self.columns)

            # 제품 목록 가져오기
            self.call_product_list()

            # CSV -> 엑셀 변환
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)

            return True
        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False


    # 드라이버 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)


    # 제품 상세정보
    def call_product_list(self):
        if self.url_list:
            self.total_cnt = len(self.url_list)
            for num, url in enumerate(self.url_list, start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_cnt += 1
                prdtNo = self.extract_prdtNo(url)

                if not prdtNo:
                    self.log_signal_func(f"[스킵] prdtNo 추출 실패: {url}")
                    continue

                if "abcmart" in url:
                    request_url = f"https://abcmart.a-rt.com/product/info?prdtNo={prdtNo}"
                    retailer = "ABC-MART"
                elif "grandstage" in url:
                    request_url = f"https://grandstage.a-rt.com/product/info?prdtNo={prdtNo}"
                    retailer = "GRAND STAGE"
                elif "onthespot" in url:
                    request_url = f"https://www.onthespot.co.kr/product/info?prdtNo={prdtNo}"
                    retailer = "On the spot"
                else:
                    self.log_signal_func(f"Unsupported URL: {url}", level="ERROR")
                    continue

                obj = self.product_api_data(request_url, retailer)
                self.product_obj_list.append(obj)
                self.log_signal.emit(f"({num}/{self.total_cnt}) : {obj}")

                if num % 5 == 0:
                    self.excel_driver.append_to_csv(self.csv_filename, self.product_obj_list, self.columns)

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                time.sleep(1)

            if self.product_obj_list:
                self.excel_driver.append_to_csv(self.csv_filename, self.product_obj_list, self.columns)


    def extract_prdtNo(self, url):
        """URL에서 prdtNo 값을 안전하게 추출"""
        try:
            qs = parse_qs(urlparse(url).query)
            return (qs.get("prdtNo") or [None])[0]
        except Exception:
            # 마지막 fallback (old style)
            if "prdtNo=" in url:
                return url.split("prdtNo=", 1)[-1].split("&", 1)[0]
            return None

    # 브랜드 api_data
    def product_api_data(self, request_url, retailer):

        obj = {
            "상품명": "",
            "상품 상태": "판매 종료",
            "브랜드": "",
            "상품상세url": request_url,
            "구매 가능한 옵션": "",
            "품절된 옵션": "",
            "스타일코드": "",
            "판매가": "",
            "색상코드": "",
            "판매처": retailer
        }
        try:
            json_data = self.api_client.get(request_url, headers=self.headers)

            # 품절된 옵션과 구매 가능한 옵션을 분리
            options = json_data.get("productOption") or []
            available_options = [o.get("optnName") for o in options if (o.get("totalStockQty") or 0) > 0] # 0 제외
            sold_out_options  = [o.get("optnName") for o in options if (o.get("totalStockQty") or 0) == 0]
            total_stock_qty   = sum((o.get("totalStockQty") or 0) for o in options)

            # 상품상태 결정
            product_status = "품절" if total_stock_qty == 0 else "정상"

            # 판매가 포맷 설정
            # sellAmt = json_data.get("productPrice", {}).get("sellAmt")
            # if sellAmt is not None:
            #     sellAmt = f"{sellAmt:,}"

            sellAmt = json_data.get("displayProductPrice")
            if sellAmt is not None:
                sellAmt = f"{sellAmt:,}"

            # 빈 배열일 경우 공백으로 설정
            available_options = ", ".join(available_options) if available_options else ""
            sold_out_options  = ", ".join(sold_out_options)  if sold_out_options  else ""

            # 원하는 값을 추출하여 객체로 구성
            obj = {
                "상품명": json_data.get("prdtName", ""),
                "상품 상태": product_status,
                "브랜드": (json_data.get("brand") or {}).get("brandName", ""),
                "상품상세url": request_url,
                "판매가": sellAmt or "",
                "구매 가능한 옵션": available_options,
                "품절된 옵션": sold_out_options,
                "스타일코드": json_data.get("styleInfo", ""),
                "색상코드": json_data.get("prdtColorInfo", ""),
                "판매처": retailer
            }
        except Exception as e:
            self.log_signal_func(f"에러 : {e}")
        return obj


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




