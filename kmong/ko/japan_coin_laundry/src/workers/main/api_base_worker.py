import time
from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_file import FilePathBuilder
from src.utils.utils_selenium import SeleniumDriverManager
from src.utils.utils_time import get_current_formatted_datetime


# PyQt5 QThread와 ABCMeta의 메타클래스 병합
class QThreadABCMeta(type(QThread), ABCMeta):
    pass

# 병합된 메타클래스를 사용하는 추상 클래스 정의
class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()

    def __init__(self, name: str, item_list: list):
        super().__init__()
        self.name = name
        self.item_list = item_list
        self.running = True
        self.driver = None
        self.base_url = ""
        self.product_list = []
        self.before_pro_value = 0
        self.csv_appender = None
        self.google_uploader = None
        self.driver_manager = None
        self.sess = None
        self.seen_keys = set()

    def run(self):
        if self.item_list:
            self.log_func("크롤링 시작")
            self.driver_manager = SeleniumDriverManager(headless=True)
            config = SITE_CONFIGS.get(self.name)
            self.base_url = config.get("base_url")
            self.driver = self.driver_manager.start_driver(self.base_url, 1200, True)
            self.sess = self.driver_manager.get_session()

            for index, item in enumerate(self.item_list, start=1):
                if not self.running:
                    self.log_func("크롤링이 중지되었습니다.")
                    break

                csv_path = FilePathBuilder.build_csv_path_main("DB", self.name)
                self.csv_appender = CsvAppender(csv_path, self.log_func)

                self.selenium_get_product_list(index, item)
                self.selenium_get_product_detail_list()

            self.progress_signal.emit(self.before_pro_value, 1000000)
            self.log_func("=============== 크롤링 종료중...")
            time.sleep(5)
            self.log_func("=============== 크롤링 종료")
            self.progress_end_signal.emit()
        else:
            self.log_func("선택된 항목이 없습니다.")

    def log_func(self, msg):
        self.log_signal.emit(msg)

    def stop(self):
        self.running = False


    @abstractmethod
    def selenium_get_product_list(self, index: int, item: str):
        pass

    @abstractmethod
    def selenium_get_product_detail_list(self):
        """각 사이트별 상품 상세 정보 추출"""
        pass

