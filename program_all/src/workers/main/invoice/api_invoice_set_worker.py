import os
import ssl
import time
import re
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup

from src.utils.BeautifulSoup_utils import bs_txt

from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.utils.selenium_utils import SeleniumUtils
from src.utils.str_utils import get_query_params, str_norm
from src.workers.api_base_worker import BaseApiWorker
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from urllib.parse import urlparse, parse_qs, urljoin

from src.workers.main.invoice.company.GFN import GfnInvoiceParser
from src.workers.main.invoice.company.Lignopure import LignopureInvoiceParser
from src.workers.main.invoice.company.Selco import SelcoInvoiceParser
from src.workers.main.invoice.company.bio_renuva import BioRenuvaInvoiceParser
from src.workers.main.invoice.company.contipro import ContiproInvoiceParser
from src.workers.main.invoice.company.evident_ingredients import EvidentInvoiceParser
from src.workers.main.invoice.company.hallstar_italy_us import HallstarInvoiceParser
from src.workers.main.invoice.company.protameen import ProtameenInvoiceParser


# API
class ApiInvoiceSetLoadWorker(BaseApiWorker):


    def __init__(self):
        super().__init__()
        self.excel_driver = None
        self.obj_list = []
        self.running = True  # 실행 상태 플래그 추가
        self.csv_filename = ""
        self.product_obj_list = []
        self.total_cnt = 0
        self.page = 0
        self.current_cnt = 0
        self.before_pro_value = 0


    # 초기화
    def init(self):

        self.driver_set(True)
        return True

    # 메인
    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            self.total_cnt = len(self.columns)

            for c in self.columns:

                self.current_cnt += 1

                if c == 'BioRenuva':
                    self.log_signal_func(f"BioRenuva: {c}")
                    BioRenuvaInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'CONTIPRO':
                    self.log_signal_func(f"CONTIPRO: {c}")
                    ContiproInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'Evident ingredients':
                    self.log_signal_func(f"Evident ingredients: {c}")
                    EvidentInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'GFN':
                    self.log_signal_func(f"GFN: {c}")
                    GfnInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'HALLSTAR ITALY & US':
                    self.log_signal_func(f"HALLSTAR ITALY & US: {c}")
                    HallstarInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'Lignopure':
                    self.log_signal_func(f"Lignopure: {c}")
                    LignopureInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'Protameen':
                    self.log_signal_func(f"Protameen: {c}")
                    ProtameenInvoiceParser(log_func=self.log_signal_func).run()


                elif  c == 'SELCO':
                    self.log_signal_func(f"SELCO: {c}")
                    SelcoInvoiceParser(log_func=self.log_signal_func).run()

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                time.sleep(1)


            return True
        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)


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



