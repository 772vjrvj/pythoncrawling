from PyQt5.QtCore import QThread
from src.utils.config import SITE_URL, BASE_BOOKING_PATH, BASE_BOOKING_MOBILE_PATH
from src.utils.selenium import SeleniumDriverManager
from src.service.reservation_service import ReservationService
from src.route.request_router import RequestRouter
from src.utils.log import log
import time

class MainWorker(QThread):
    def __init__(self, user_id, password, store_id, token):
        super().__init__()
        self.token = token
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.processed_requests = set()
        self.driver = None
        self.router = None

    def init(self):
        self.driver = SeleniumDriverManager().setup_driver()

        self.router = RequestRouter(
            ReservationService(self.token, self.store_id),
            BASE_BOOKING_PATH,
            BASE_BOOKING_MOBILE_PATH
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
                    self.processed_requests.add(request.id)
                    self.router.handle(request)

                self.driver.requests.clear()
                time.sleep(0.5)
        except KeyboardInterrupt:
            log("종료 요청 감지, 브라우저 닫는 중...")
            self.driver.quit()

    def login(self):
        # 모든 input 필드 중에서 type="text"인 것 찾기 (아이디)
        id_input = self.driver.find_element("css selector", 'input.gz__input[type="text"]')
        id_input.clear()
        id_input.send_keys(self.user_id)

        # 모든 input 필드 중에서 type="password"인 것 찾기 (비밀번호)
        pw_input = self.driver.find_element("css selector", 'input.gz__input[type="password"]')
        pw_input.clear()
        pw_input.send_keys(self.password)

        # 로그인 버튼 클릭
        login_btn = self.driver.find_element(
            "css selector", "button.gz__btn.gz__btn--lg.gz__btn--block.gz__btn--primary.form__submit"
        )
        login_btn.click()

        log("✅ 로그인 시도 완료")