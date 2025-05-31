import time
from collections import deque

from PyQt5.QtCore import QThread
from selenium.common import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.route.request_router import RequestRouter
from src.service.reservation_dom import DomReservationExtractor, JSFn
from src.service.reservation_service import ReservationService
from src.state.dom_state import DomState
from src.utils.config import SITE_URL, BASE_BOOKING_PATH, BASE_BOOKING_MOBILE_PATH, BASE_RESERVATION_MOBILE_PATH
from src.utils.log import log
from src.utils.selenium import SeleniumDriverManager


class MainWorker(QThread):
    def __init__(self, user_id, password, store_id, token):
        super().__init__()
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.token = token
        self.driver = None
        self.router = None
        self.dom_extr = None
        self.booking_tab_handle = None
        self.processed_requests = deque(maxlen=1000)
        self.first_time = True  # 최초 한 번만 자동 클릭

    def init(self):
        self.driver = SeleniumDriverManager().setup_driver()
        self.router = RequestRouter(
            ReservationService(self.token, self.store_id),
            BASE_BOOKING_PATH,
            BASE_BOOKING_MOBILE_PATH,
            BASE_RESERVATION_MOBILE_PATH,
            self.driver
        )

    def login(self):
        self.driver.get(SITE_URL)
        log("사이트 접속 완료")

        time.sleep(1)
        id_input = self.driver.find_element(By.ID, "user_id")
        id_input.clear()
        id_input.send_keys(self.user_id)

        pw_input = self.driver.find_element(By.ID, "user_pw")
        pw_input.clear()
        pw_input.send_keys(self.password)

        login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        log("로그인 완료")
        time.sleep(2)

    def click_reservation_button(self):
        try:
            wait = WebDriverWait(self.driver, 10)  # 최대 10초 대기
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".gz__btn.booking__btn")))
            button.click()
        except Exception as e:
            log(f"예약 버튼 클릭 실패: {e}")

    def wait_for_new_tab(self, old_handles):
        for _ in range(30):  # 최대 15초 대기
            time.sleep(0.5)
            new_handles = self.driver.window_handles
            if len(new_handles) > len(old_handles):
                for handle in new_handles:
                    if handle not in old_handles:
                        return handle
        return None

    def monitor_booking_tab(self):
        try:
            self.driver.switch_to.window(self.booking_tab_handle)
            log("예약 탭 감시 시작")

            self.dom_extr = DomReservationExtractor(self.driver)
            self.dom_extr.inject_observer()
            time.sleep(1)

            while self.booking_tab_handle in self.driver.window_handles:
                # ✅ 1. alert 발생 시 → 최대 60초 사용자 입력 대기
                try:
                    if EC.alert_is_present()(self.driver):
                        log("[ALERT] 감지됨 → 사용자 확인 대기 중 (최대 60초)...")
                        WebDriverWait(self.driver, 60).until_not(EC.alert_is_present())
                        log("[ALERT] 사용자 확인 완료")
                        time.sleep(0.5)  # DOM 반영 대기
                    else:
                        log("[ALERT] 없음 → 예약 버튼 클릭이 없었던 것으로 간주")
                except Exception:
                    log("[예약 실패] 사용자 확인 안됨 (60초 초과)")

                try:
                    dom_data = self.dom_extr.js_fn(JSFn.GET_BOOKING_DATA)
                    if dom_data and dom_data.get("timestamp") and dom_data.get("machineNumbers"):
                        log(f"[DOM] 예약 데이터 감지: {dom_data}")

                        name = dom_data.get("name")
                        phone = dom_data.get("phone")
                        timestamp = dom_data.get("timestamp")
                        action_type = dom_data.get("type")  # register, edit, delete 등

                        for room_id in dom_data.get("machineNumbers", []):
                            entry = {
                                "name": name,
                                "phone": phone,
                                "roomId": room_id,
                                "timestamp": timestamp,
                                "type": action_type
                            }
                            DomState.add(entry)
                        log(f"[DOM] 예약 데이터 결과: {DomState.get_all()}")
                    else:
                        log("[예약 실패] 데이터 미감지")
                except UnexpectedAlertPresentException:
                    log("[DOM] alert이 떠 있어 getBookingData 실패 → 다음 루프에서 재시도")
                except Exception as js_err:
                    log(f"[DOM] JS 호출 중 예외 발생: {js_err}")

                # ✅ 3. 네트워크 요청 처리
                for request in list(self.driver.requests):
                    if request.id in self.processed_requests:
                        continue
                    self.processed_requests.append(request.id)
                    self.router.handle(request)

                time.sleep(0.5)

            log("예약 탭 닫힘 → 감시 중지")
            self.booking_tab_handle = None

        except Exception as e:
            log(f"예약 탭 감시 중 예외 발생: {e}")
            self.booking_tab_handle = None


    def run(self):
        self.init()
        self.login()

        while True:
            if self.booking_tab_handle and self.booking_tab_handle in self.driver.window_handles:
                self.monitor_booking_tab()
            else:
                log("예약 탭 없음 → 새 탭 열림 대기")

                old_handles = self.driver.window_handles  # ✅ 반드시 클릭 전 저장

                if self.first_time:
                    self.first_time = False
                    self.click_reservation_button()

                new_handle = self.wait_for_new_tab(old_handles)
                if new_handle:
                    self.booking_tab_handle = new_handle
                    log(f"새 탭 감지됨: {new_handle}")
                else:
                    log("새 탭이 열리지 않음 → 다음 루프")
