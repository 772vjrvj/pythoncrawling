from PyQt5.QtCore import QThread
from src.utils.config import SITE_URL, BASE_BOOKING_PATH, BASE_BOOKING_MOBILE_PATH, BASE_RESERVATION_MOBILE_PATH
from src.utils.selenium import SeleniumDriverManager
from src.service.reservation_service import ReservationService
from src.route.request_router import RequestRouter
from src.utils.log import log
import time
from collections import deque

class MainWorker(QThread):
    def __init__(self, user_id, password, store_id, token):
        super().__init__()
        self.token = token
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.processed_requests = deque(maxlen=1000)  # ✅ 최근 1000개만 기억
        self.driver = None
        self.router = None

    def init(self):
        self.driver = SeleniumDriverManager().setup_driver()

        self.router = RequestRouter(
            ReservationService(self.token, self.store_id),
            BASE_BOOKING_PATH,
            BASE_BOOKING_MOBILE_PATH,
            BASE_RESERVATION_MOBILE_PATH
        )

    def run(self):
        self.init()
        self.driver.get(SITE_URL)
        log("등록, 수정, 삭제시 API 호출을 진행합니다...")

        time.sleep(2)

        try:
            self.login()
        except Exception as e:
            log(f"로그인 중 오류 발생: {e}")
            return

        log("요청 감지 대기 중...")

        try:
            while True:
                for request in list(self.driver.requests):
                    if request.id in self.processed_requests:
                        continue
                    self.processed_requests.append(request.id)
                    self.router.handle(request)
                time.sleep(0.5)
        except KeyboardInterrupt:
            log("종료 요청 감지, 브라우저 닫는 중...")
            self.driver.quit()

    def login(self):
        id_input = self.driver.find_element("id", "user_id")
        id_input.clear()
        id_input.send_keys(self.user_id)

        pw_input = self.driver.find_element("id", "user_pw")
        pw_input.clear()
        pw_input.send_keys(self.password)

        login_btn = self.driver.find_element("xpath", "//button[@type='submit']")
        login_btn.click()
        log("로그인 시도 완료")
