import json
import re
import time
import random
import pandas as pd

from bs4 import BeautifulSoup

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils


from src.workers.api_base_worker import BaseApiWorker

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


class ApiBaseDetailSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()
        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0.0
        self.site_name = "base"
        self.site_list_url = "https://baselist.com"
        self.site_detail_url = "https://basedetail.com"
        self.headers_list = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://m.land.naver.com/",
        }
        self.headers_detail = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://m.land.naver.com/",
        }
        self.result_data_list = []
        self.csv_filename = None
        self.selenium_driver = None
        self.excel_driver = None
        self.file_driver = None
        self.driver = None
        self.api_client = None


    def init(self):
        return True


    def stop(self):
        self.running = False


    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(1)
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()


    def driver_set(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless=False)
        self.driver = self.selenium_driver.start_driver(1200)


    def main(self):
        self.log_signal_func("시작합니다.")

        # 파일경로, 파일명 생성
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)

        # 파일 생성
        self.excel_driver.init_csv(self.csv_filename, self.columns)


        pro_value = (self.current_cnt / float(self.total_cnt)) * 1000000
        self.progress_signal.emit(self.before_pro_value, pro_value)
        self.before_pro_value = pro_value

        return True

