import time
from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal

from src.utils.api_server import ApiServer
from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_file import FilePathBuilder
from src.utils.utils_google_cloud_upload import GoogleUploader
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

    def __init__(self, name: str, checked_list: list):
        super().__init__()
        self.name = name
        self.checked_list = checked_list
        self.sess = None
        self.running = True
        self.driver = None
        self.base_url = ""
        self.brand_type = ""
        self.country = ""
        self.product_list = []
        self.detail_product_list = []
        self.blob_product_ids = []
        self.before_pro_value = 0
        self.csv_appender = None
        self.google_uploader = None
        self.driver_manager = None
        self.seen_keys = set()
        self.server_api = None



    def run(self):
        if self.checked_list:
            self.log_func("서버와 데이터 동기화를 시작합니다...")
            latest_date = self.csv_appender.get_latest_reg_date()
            if not latest_date:
                latest_date = "1900.01.01 00:00:00"
            self.detail_product_list = self.server_api.get_products_after_reg_date(latest_date)
            self.csv_appender.append_rows_to_metastyle_all(self.detail_product_list)
            self.log_func("서버와 데이터 동기화를 완료하였습니다!!!")
            self.log_func("크롤링 시작")
            self.log_func(f"checked_list : {self.checked_list}")
            self.driver_manager = SeleniumDriverManager(headless=True)
            config = SITE_CONFIGS.get(self.name)
            self.base_url = config.get("base_url")
            self.brand_type = config.get("brand_type")
            self.country = config.get("country")
            self.driver = self.driver_manager.start_driver(self.base_url, 1200, True)
            self.sess = self.driver_manager.get_session()
            self.google_uploader = GoogleUploader(self.log_func, self.sess)
            self.server_api = ApiServer(log_func=self.log_func)
            self.csv_appender = CsvAppender("DB", self.log_func)
            self.init_set()

            for index, check_obj in enumerate(self.checked_list, start=1):
                if not self.running:
                    self.log_func("크롤링이 중지되었습니다.")
                    break

                name = check_obj['name']
                obj = {
                    "website": self.name,
                    "categoryFull": name
                }
                # self.google_uploader.delete(obj)
                self.blob_product_ids = self.google_uploader.verify_upload(obj)
                # self.google_uploader.download_all_in_folder(obj)
                site_url = config.get('check_list', {}).get(name, "")
                main_url = f"{self.base_url}{site_url}"
                self.selenium_get_product_list(main_url)
                self.selenium_get_product_detail_list(name)
                self.csv_appender.append_rows_to_metastyle_all(self.detail_product_list)
                self.detail_product_list = []

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

    def selenium_get_product_detail_list(self, name):
        for no, product in enumerate(self.product_list, start=1):
            if not self.running:
                self.log_func("크롤링이 중지되었습니다.")
                break

            product_id = product["product_id"]
            url = product["url"]

            obj = self.extract_product_detail(product_id, url, name, no)
            if not obj:
                continue
            obj["regDate"] = get_current_formatted_datetime()
            obj["productKey"] = f'{obj["website"]}_{obj["productId"]}'

            product_info = self.server_api.get_product_by_key(obj["productKey"])
            if not product_info:
                self.google_uploader.upload(obj)
                self.log_func(f"productId => {product_id}({no}) : {obj}")
                if obj.get("error"):
                    obj["success"] = "N"
                self.server_api.add_products([obj])

            pro_value = (no / len(self.product_list)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            self.log_func(f'{name} : TotalProduct({no}/{len(self.product_list)})')

        latest_date = self.csv_appender.get_latest_reg_date()
        self.detail_product_list = self.server_api.get_products_after_reg_date(latest_date)




    @abstractmethod
    def init_set(self):
        pass

    @abstractmethod
    def selenium_get_product_list(self, main_url: str):
        pass

    @abstractmethod
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:
        """각 사이트별 상품 상세 정보 추출"""
        pass

