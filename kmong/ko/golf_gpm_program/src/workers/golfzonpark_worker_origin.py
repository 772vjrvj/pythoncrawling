import json
import re
import time
from typing import Callable
from urllib.parse import urlparse, parse_qs

from PyQt5.QtCore import QThread

from src.utils.log import log, log_json
from src.api.action import send_to_external_api_action
from src.route.route import Route  # 위 클래스를 별도로 두는 경우
from src.utils.config import SITE_URL, BASE_BOOKING_PATH, BASE_BOOKING_MOBILE_PATH
from src.utils.data_api import wait_for_response, parse_urlencoded_form
from src.utils.selenium import SeleniumDriverManager
from src.utils.payload_builder import PayloadBuilder


class GolfzonparkWorker(QThread):

    # 생성자
    # region
    def __init__(self, user_id, password, store_id, token):
        super().__init__()
        self.processed_requests = set()
        self.token = token
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.cached_entities = []
        self.driver = SeleniumDriverManager().setup_driver()
    # endregion


    # 실행
    # region
    def run(self):
        self.driver.get(SITE_URL)
        log("⏳ 등록, 수정, 삭제시 API 호출을 진행합니다... ")

        time.sleep(2)  # 페이지 로딩 대기

        try:
            # ID 입력
            id_input = self.driver.find_element("id", "user_id")
            id_input.clear()
            id_input.send_keys(self.user_id)

            # PW 입력
            pw_input = self.driver.find_element("id", "user_pw")
            pw_input.clear()
            pw_input.send_keys(self.password)

            # 로그인 버튼 클릭
            login_btn = self.driver.find_element("xpath", "//button[@type='submit']")
            login_btn.click()

            log("✅ 로그인 시도 완료")

        except Exception as e:
            log(f"❌ 로그인 중 오류 발생: {e}")
            return

        log("⏳ 요청 감지 대기 중... ")

        try:
            while True:
                for request in list(self.driver.requests):
                    if request.id in self.processed_requests:
                        continue
                    response = wait_for_response(request)
                    if not response:
                        continue
                    self.processed_requests.add(request.id)
                    self.process_route(request)

                self.driver.requests.clear()
                time.sleep(0.5)
        except KeyboardInterrupt:
            log("⛔ 종료 요청 감지, 브라우저 닫는 중...")
            self.driver.quit()
    # endregion

    # 라우팅 및 매핑처리
    # region

    # 라우팅 처리
    def process_route(self, request):
        url = request.url
        method = request.method

        # 라우트 목록 정의
        routes = [
            Route('GET',  re.compile(fr'{BASE_BOOKING_PATH}/\d+(\?timestamp=|$)'),           self.request_set, 'select'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/register(\?timestamp=|$)'),      self.request_set, 'register'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/\d+/edit(\?timestamp=|$)'),      self.request_set, 'edit'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/\d+/ajax-edit(\?timestamp=|$)'), self.request_set, 'edit_move'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/\d+/delete(\?timestamp=|$)'),    self.request_set, 'delete'),
        ]

        # 라우팅 처리
        for route in routes:
            if route.matches(method, url):
                route.handler(request, route.action)
                return

        # 특수 처리: polling delete
        if method == 'GET' and url.startswith(BASE_BOOKING_MOBILE_PATH):
            params = parse_qs(urlparse(url).query)
            required_keys = {'timestamp', 'bookingStartDt', 'data', 'bookingNumber'}
            if required_keys.issubset(params):
                self.request_set_delete_mobile(request, 'delete_mobile')

    # 요청 세팅
    def request_set(self, request, action):
        log(f"[{action}] : 시작 ==============================")
        log(f"[{action}] : 대기중...")
        response = wait_for_response(request)
        if response and response.status_code == 200:
            log(f"[{action}] : 조회 성공")
            try:
                log(f"[{action}] : Request Body")
                req_json = parse_urlencoded_form(request.body.decode('utf-8', errors='replace'))
                log_json(req_json)

                log(f"[{action}] : Response Body")
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                log_json(resp_json)

                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                    log(f"[{action}] : 응답 실패 {resp_json.get("status")}")
                    log(f"[{action}] : 끝 ==============================")
                    return

                if action == 'select':
                    entities = resp_json.get("entitys", [])
                    if not isinstance(entities, list):
                        return
                    self.cached_entities = entities
                    log(f"[{action}] : {len(entities)}건의 예약 데이터를 캐시에 저장했습니다.")
                    log(f"[{action}] : 끝 ==============================")
                else:
                    self.process_mapping(req_json, resp_json, action)

            except Exception as e:
                log(f"[{action}] : 처리 오류 - {e}")
                log(f"[{action}] : 끝 ==============================")
        else:
            log(f"[{action}] : 요청 실패 또는 응답 없음")
            log(f"[{action}] : 끝 ==============================")

    # 모바일 삭제 요청 세팅
    def request_set_delete_mobile(self, request, action):
        response = wait_for_response(request)
        if response and response.status_code == 200:
            try:
                req_json = parse_urlencoded_form(request.body.decode('utf-8', errors='replace'))
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                    log(f"[{action}] : 응답 실패 {resp_json.get("status")}")
                    log(f"[{action}] : 끝 ==============================")

                    if resp_json.get("entity", {}).get("destroy", []):
                        log(f"[{action}] : 시작 ==============================")
                        log(f"[{action}] : 대기중...")
                        log(f"[{action}] : 조회 성공")
                        log(f"[{action}] : Request Body")
                        log_json(req_json)
                        log(f"[{action}] : Response Body")
                        log_json(resp_json)
                        self.process_mapping(req_json, resp_json, "polling_delete")
            except Exception as e:
                log(f"[{action}] : 처리 오류 - {e}")
                log(f"[{action}] : 끝 ==============================")
        else:
            log(f"[{action}] : 요청 실패 또는 응답 없음")
            log(f"[{action}] : 끝 ==============================")

    # 처리 매핑
    def process_mapping(self, req_json: dict, resp_json: dict, action: str):
        action_map: dict[str, Callable[[dict, dict], None]] = {
            "register": self.process_register,
            "edit": self.process_edit,
            "edit_move": self.process_move,
            "delete": self.process_admin_cancel,
            "delete_mobile": self.process_user_cancel
        }
        processor = action_map.get(action)
        if processor:
            processor(req_json, resp_json)
        else:
            log(f"🚫 알 수 없는 action: {action}")

    # endregion

    # PROCESS
    # region

    # 등록 처리
    def process_register(self, req_json: dict, resp_json: dict):
        for entity in PayloadBuilder.extract_entities(resp_json):
            external_id = entity.get("bookingNumber", [None])[0]
            machine_number = entity.get("machineNumber")
            reserve_no = req_json.get("reserveNo") or None
            payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number, reserve_no)
            send_to_external_api_action(self.token, self.store_id, "register", payload)

    # 수정 처리
    def process_edit(self, req_json: dict, resp_json: dict):
        entities = PayloadBuilder.extract_entities(resp_json)
        reserve_no = req_json.get("reserveNo") or None

        # 삭제 처리
        if reserve_no:
            payload = PayloadBuilder.delete("고객 취소", group_id=reserve_no)
        else:
            external_id = req_json.get("bookingNumber")
            payload = PayloadBuilder.delete("추가 수정시 기존 취소", external_id=external_id)
        send_to_external_api_action(self.token, self.store_id, "delete", payload)

        if entities:
            for entity in entities:
                external_id = entity.get("bookingNumber", [None])[0]
                machine_number = entity.get("machineNumber")
                payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number, reserve_no)
                send_to_external_api_action(self.token, self.store_id, "register", payload)
        else:
            external_id = req_json.get("bookingNumber")
            machine_number = req_json.get("machineNumber")
            payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number)
            send_to_external_api_action(self.token, self.store_id, "edit", payload)

    # 수정 처리(마우스 드래그로 시간, 방 변경)
    def process_move(self, req_json: dict):
        payload = PayloadBuilder.edit_move(req_json)
        send_to_external_api_action(self.token, self.store_id, "edit", payload)

    # 운영자 취소
    def process_admin_cancel(self, req_json: dict):
        booking_nums = req_json.get("bookingNums", [])
        if isinstance(booking_nums, str):
            booking_nums = [booking_nums]
        for booking_number in booking_nums:
            payload = PayloadBuilder.delete("운영자 취소", external_id=booking_number)
            send_to_external_api_action(self.token, self.store_id, "delete", payload)

    # 고객 취소
    def process_user_cancel(self, resp_json: dict):
        reserve_no = resp_json.get("entity", {}).get("destroy", [{}])[0].get("reserveNo", "")
        if reserve_no:
            payload = PayloadBuilder.delete("고객 취소", group_id=reserve_no)
            send_to_external_api_action(self.token, self.store_id, "delete", payload)

    # endregion


