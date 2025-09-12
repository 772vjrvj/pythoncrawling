import os
import shutil
import ssl
import time
from urllib.parse import urlparse, parse_qs, unquote, quote, unquote_to_bytes

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.core.global_state import GlobalState

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from urllib.parse import quote, unquote



import re

# API
class ApiOkmallDetailSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://www.okmall.com"
        self.base_main_url_login = "https://www.okmall.com/members/login"
        self.url_list = []
        self.user = None
        self.driver = None
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "okmall"
        self.site_name = "okmall"
        self.csv_filename = ""
        self.product_obj_list = []
        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)
        self.headers = {
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


    # 초기화
    def init(self):
        self.driver_set(False)
        self.login()
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
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)
        
        # 드라이버 세팅
        self.driver = self.selenium_driver.start_driver(1200)


    # 쿠키세팅
    def set_cookies(self):
        self.log_signal_func("📢 쿠키 세팅 시작")
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)
        self.log_signal_func("📢 쿠키 세팅 완료")
        time.sleep(2)


    # 제품 상세정보
    def call_product_list(self):
        if self.url_list:
            self.total_cnt = len(self.url_list)
            for num, product in enumerate(self.url_list, start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_cnt += 1
                obj = self.product_api_data(product)
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

    # 브랜드 api_data
    def product_api_data(self, url):
        obj = {
            "상품링크": url,
            "브랜드": "",
            "상품명": "",
            "가격": "",
            "택 사이즈": [],
        }
        try:
            html = self.api_client.get(url, headers=self.headers)
            soup = BeautifulSoup(html, "html.parser")

            # 브랜드
            if brand := soup.select_one("span.brand_tit"):
                obj["브랜드"] = brand.get_text(strip=True)

            # 상품명
            if name_el := soup.select_one("h3#ProductNameArea .prd_name"):
                obj["상품명"] = name_el.get_text(strip=True)

            # 가격
            if price_el := soup.select_one(".real_price .price"):
                obj["가격"] = "".join(price_el.stripped_strings)

            # 사이즈
            size_list = []
            for row in soup.select('table.shoes_size tr[name="selectOption"]'):
                tds = row.select("td.t_center")
                if len(tds) >= 2:
                    size_list.append(tds[1].get_text(strip=True))
            obj["택 사이즈"] = size_list

        except requests.exceptions.RequestException as e:
            self.log_signal_func(f"HTTP 요청 에러: {e}")
        except Exception as e:
            self.log_signal_func(f"알 수 없는 에러 발생: {e}")

        return obj


    # 로그인 쿠키가져오기
    def login(self):
        self.driver.get(self.base_main_url_login)

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

        except Exception as e:
            log_signal_func(f"[❌ 로그인 자동 입력 오류] {e}")


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




