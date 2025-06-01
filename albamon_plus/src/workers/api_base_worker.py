import time
from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal


from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    InvalidSelectorException,
    WebDriverException
)

from src.core.global_state import GlobalState
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils


# PyQt5 QThread와 ABCMeta의 메타클래스 병합
class QThreadABCMeta(type(QThread), ABCMeta):
    pass

# 병합된 메타클래스를 사용하는 추상 클래스 정의
class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    msg_signal = pyqtSignal(str, str, object)

    # 초기화
    def __init__(self):
        super().__init__()
        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.sess = None
        self.running = True
        self.driver = None
        self.base_url = None
        self.before_pro_value = 0


    # 실행
    def run(self):
        # 시작
        self.base_init()

        # 메인
        self.main()

        # 끝
        self.base_end()


    # 초기 세팅 모은 함수
    def base_init(self):
        self.log_func("크롤링 시작 ========================================")

        # 객체 드라이버 초기화
        self.driver_set()

        # 사이트별 초기화
        self.init()


    # 마무리
    def base_end(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()


    # 드라이버 객체 세팅
    def driver_set(self):
        self.log_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_func)

        # 엑셀 객체 초기화
        self.file_driver = FileUtils(self.log_func)
        
        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless=False)


        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)
        self.sess = self.selenium_driver.get_session()


    # 로그
    def log_func(self, msg):
        self.log_signal.emit(msg)
        # print(msg) # 테스트 일때만

    # 정지
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()

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

    # 초기 함수
    @abstractmethod
    def init(self):
        pass

    # 메인 함수
    @abstractmethod
    def main(self):
        pass
