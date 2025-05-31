from PyQt5.QtCore import QThread
from src.utils.config import SITE_URL, BASE_BOOKING_PATH, BASE_BOOKING_MOBILE_PATH, BASE_RESERVATION_MOBILE_PATH
from src.utils.selenium import SeleniumDriverManager
from src.service.reservation_service import ReservationService
from src.route.request_router import RequestRouter
from src.utils.log import log
import time
from collections import deque
import hashlib
import datetime


class MainWorker(QThread):
    def __init__(self, user_id, password, store_id, token):
        super().__init__()
        self.token = token
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.processed_requests = deque(maxlen=1000)  # ✅ 해시값 기준 중복 방지
        self.processed_objects = set()               # ✅ request 객체 자체 중복 방지
        self.driver = None
        self.router = None
        self.start_time = datetime.datetime.utcnow()  # ✅ 기준 시간

    def init(self):
        self.driver = SeleniumDriverManager().setup_driver()

        self.router = RequestRouter(
            ReservationService(self.token, self.store_id),
            BASE_BOOKING_PATH,
            BASE_BOOKING_MOBILE_PATH,
            BASE_RESERVATION_MOBILE_PATH,
            self.driver
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
                log(f"시작 확인 len : {len(list(self.driver.requests))}")
                for request in list(self.driver.requests):
                    if request.response and request.response.status_code == 304:
                        continue  # 캐시 응답이면 무시

                    if id(request) in self.processed_objects:
                        continue

                    req_key = self._get_request_key(request)
                    if not req_key or req_key in self.processed_requests:
                        continue

                    self.processed_requests.append(req_key)
                    self.processed_objects.add(id(request))
                    self.router.handle(request)

                try:
                    storage = self.driver._request_storage
                    storage._requests.clear()
                    storage._id_to_request.clear()
                    storage._request_id_counter = 0
                except Exception as e:
                    log(f"요청 저장소 클리어 실패: {e}")


                log(f"끝 확인 len : {len(list(self.driver.requests))}")
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


    def _get_request_key(self, request):
        try:
            url_base = request.url.split("?")[0]
            body = request.body.decode(errors="ignore") if request.body else ""

            # ✅ 응답 바디 일부도 포함시켜 중복 체크 강화
            response_body = ""
            if request.response and request.response.body:
                response_body = request.response.body.decode(errors="ignore")[:100]  # 일부만

            raw = f"{request.method}:{url_base}:{body}:{response_body}"
            return hashlib.sha256(raw.encode()).hexdigest()
        except Exception as e:
            log(f"요청 키 생성 중 오류: {e}")
            return None
