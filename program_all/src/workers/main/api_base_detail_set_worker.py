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
from src.utils.type_utils import _as_dict, _as_list, _s, ensure_list_attr
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


class ApiBaseDetailSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()

        self.csv_filename = None
        self.current_cnt = 0
        self.total_cnt = 0

        self.columns = None
        self.setting_detail = None

        self.site_name = "logo"
        self.site_url = "https://457deep.com/"

        self.before_pro_value = 0.0

        self.result_data_list = []

        self.excel_driver = None
        self.file_driver = None
        self.api_client = None

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://m.land.naver.com/",
        }


    def init(self):
        return True

    def main(self):
        self.log_signal_func("시작합니다.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)

        df = pd.DataFrame(columns=self.columns or [])
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

        return True

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(1)
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False


    def driver_set(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)
