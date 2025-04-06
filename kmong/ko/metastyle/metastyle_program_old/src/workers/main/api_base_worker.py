import time
from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal

from src.utils.api_server import ApiServer
from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_google_cloud_upload import GoogleUploader
from src.utils.utils_selenium import SeleniumDriverManager
from src.utils.utils_time import get_current_formatted_datetime

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    InvalidSelectorException,
    WebDriverException
)


# PyQt5 QThread와 ABCMeta의 메타클래스 병합
class QThreadABCMeta(type(QThread), ABCMeta):
    pass

# 병합된 메타클래스를 사용하는 추상 클래스 정의
class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    
    # 초기화
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
        self.config = SITE_CONFIGS.get(self.name)

    # 실행
    def run(self):
        if self.checked_list:
            # 시작
            self.base_init_set()

            # 메인
            self.main()

            # 끝
            self.progress_end()
        else:
            self.log_func("선택된 항목이 없습니다.")

    # 메인
    def main(self):
        for index, check_obj in enumerate(self.checked_list, start=1):

            # 삭제 test
            # self.delete_test()
            # return

            if not self.running:
                self.log_func("크롤링이 중지되었습니다.")
                break

            name = check_obj['name']
            obj = {
                "website": self.name,
                "categoryFull": name
            }
            
            # 목록 전체 삭제 test
            # self.google_uploader.delete(obj)
            # return

            self.blob_product_ids = self.google_uploader.verify_upload(obj)
            site_url = self.config.get('check_list', {}).get(name, "")
            main_url = f"{self.base_url}{site_url}"
            self.log_func(f"main_url : {main_url}")

            self.selenium_get_product_list(main_url)
            self.selenium_get_product_detail_list(name)
            self.csv_appender.append_rows_to_metastyle_all(self.detail_product_list)
            self.detail_product_list = []

    # 초기 세팅 모은 함수
    def base_init_set(self):

        self.log_func("크롤링 시작 ========================================")
        self.log_func(f"체크한 항목 : {self.checked_list}")

        # 기본 정보 세팅
        self.basic_set()

        # 객체 드라이버 초기화
        self.driver_set()

        # 서버 데이터 동기화
        self.server_sync()

        # 사이트별 초기화
        self.init_set()

    # 드라이버 객체 세팅
    def driver_set(self):
        self.log_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.csv_appender = CsvAppender("DB", self.log_func)
        
        # Web 서버 객체 초기화
        self.server_api = ApiServer(log_func=self.log_func)
        
        # 셀레니움 초기화
        self.driver_manager = SeleniumDriverManager(headless=True)
        self.driver = self.driver_manager.start_driver(self.base_url, 1200, True)
        
        # 구글 업로더 초기화
        self.google_uploader = GoogleUploader(self.log_func)
    
    # 서버 동기화
    def server_sync(self):
        self.log_func("서버와 데이터 동기화를 시작합니다...")
        latest_date = self.csv_appender.get_latest_reg_date("metastyle_all.csv")
        if not latest_date:
            latest_date = "1900.01.01 00:00:00"
        self.log_func("서버 요청중...")
        self.detail_product_list = self.server_api.get_products_after_reg_date(latest_date)
        self.csv_appender.append_rows_to_metastyle_all(self.detail_product_list)
        self.log_func("서버와 데이터 동기화를 완료하였습니다!!!")

    # 로그
    def log_func(self, msg):
        self.log_signal.emit(msg)
        print(msg) # 테스트 일때만

    # 정지
    def stop(self):
        self.running = False
    
    # 상세목록
    def selenium_get_product_detail_list(self, name):
        loaded_objs = self.csv_appender.load_rows("metastyle_all.csv")

        uploaded_ids = set()

        for obj in loaded_objs:
            if not self.running:
                self.log_func("크롤링이 중지되었습니다.")
                break
            pid = str(obj["productId"])
            uploaded_ids.add(pid)

        for no, product in enumerate(self.product_list, start=1):
            if not self.running:
                self.log_func("크롤링이 중지되었습니다.")
                break

            product_id = product["productId"]
            url = product["url"]

            if product_id in uploaded_ids:
                self.log_func(f"[SKIP] 성공적으로 처리된 product_id: {product_id}")
                continue

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
            else:
                self.log_func(f'이미 등록된 데이터 입니다 : {product_info}')

            pro_value = (no / len(self.product_list)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            self.log_func(f'{name} : TotalProduct({no}/{len(self.product_list)})')

        latest_date = self.csv_appender.get_latest_reg_date()
        self.detail_product_list = self.server_api.get_products_after_reg_date(latest_date)

    # 에러처리
    def handle_selenium_exception(self, context, exception):
        if isinstance(exception, NoSuchElementException):
            self.log_func(f"❌ {context} - 요소 없음")
        elif isinstance(exception, StaleElementReferenceException):
            self.log_func(f"❌ {context} - Stale 요소")
        elif isinstance(exception, TimeoutException):
            self.log_func(f"⏱️ {context} - 로딩 시간 초과")
        elif isinstance(exception, ElementClickInterceptedException):
            self.log_func(f"🚫 {context} - 클릭 방해 요소 존재")
        elif isinstance(exception, ElementNotInteractableException):
            self.log_func(f"🚫 {context} - 요소가 비활성 상태")
        elif isinstance(exception, InvalidSelectorException):
            self.log_func(f"🚫 {context} - 선택자 오류")
        elif isinstance(exception, WebDriverException):
            self.log_func(f"⚠️ {context} - WebDriver 오류")
        else:
            self.log_func(f"❗ {context} - 알 수 없는 오류")

    # 기본 변수 세팅
    def basic_set(self):
        self.base_url   = self.config.get("base_url")
        self.brand_type = self.config.get("brand_type")
        self.country    = self.config.get("country")

    # 마무리
    def progress_end(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 초기 함수
    @abstractmethod
    def init_set(self):
        pass

    # 목록
    @abstractmethod
    def selenium_get_product_list(self, main_url: str):
        pass

    # 상세목록 추출
    @abstractmethod
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:
        """각 사이트별 상품 상세 정보 추출"""
        pass

    # 삭제 test용
    def delete_test(self):
        obj_list = self.csv_appender.load_rows()
        delete_obj_list = []
        for index_dt, obj in enumerate(obj_list):
            print(f'index_dt : {index_dt}')
            if obj.get('website') != "H&M":
                continue
            delete_obj_list.append(obj)

            # if obj.get('imageUrl') == "" or obj.get('imageUrl') == None or obj.get('imageUrl') == 'https://static.zara.net/stdstatic/6.63.1/images/transparent-background.png' or obj.get('imageUrl') == 'https://static.zara.net/stdstatic/6.59.2/images/transparent-background.png' :
            #     print(f'삭제할 놈 obj : {obj}')
            #     delete_obj_list.append(obj)
            #
            # if obj.get('productKey') == "ZARA_435257838" or obj.get('productKey') == "ZARA_434455281":
            #     print(f'삭제할 놈 obj : {obj}')
            #     delete_obj_list.append(obj)

        for idxd, delete_obj in enumerate(delete_obj_list):
            print(f'삭제시작 idx : {idxd}, delete_obj : {delete_obj}')
            # self.google_uploader.delete_image(delete_obj)
            self.server_api.delete_product(delete_obj.get('productKey'))
