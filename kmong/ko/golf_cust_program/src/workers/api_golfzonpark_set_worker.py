import re
import time
import json
import requests

from PyQt5.QtCore import QThread
from urllib.parse import unquote
from urllib.parse import urlparse, parse_qs

from requests import RequestException

from src.utils.log import log, log_json
from src.utils.config import EXTERNAL_API_BASE_URL, CRAWLING_SITE, SITE_URL, TEST_TOKEN, BASE_BOOKING_PATH, BASE_BOOKING_MOBILE_PATH
from src.utils.payload_builder import PayloadBuilder
from src.utils.time import to_iso_format
from src.utils.selenium import SeleniumDriverManager
from src.vo.routes import Route  # 위 클래스를 별도로 두는 경우



class ApiGolfzonparkSetLoadWorker(QThread):
    
    # 생성자
    def __init__(self, user_id, password, store_id):
        super().__init__()
        self.processed_requests = set()
        self.token = ""
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.cached_entities = []
        self.driver = SeleniumDriverManager().setup_driver()
        self.token = None

    # 초기화
    def init(self):
        self.token = self.get_golf_token()

    # 실행
    def run(self):
        self.init()
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
                    response = self.wait_for_response(request)
                    if not response:
                        continue
                    self.processed_requests.add(request.id)
                    self.process_request(request)

                self.driver.requests.clear()
                time.sleep(0.5)
        except KeyboardInterrupt:
            log("⛔ 종료 요청 감지, 브라우저 닫는 중...")
            self.driver.quit()

    # 중지
    def stop(self):
        self.driver.quit()

    # 토큰 요청
    def get_golf_token(self):
        url = f"{EXTERNAL_API_BASE_URL}/auth/token/stores/{self.store_id}/role/singleCrawler"
        log(f"토큰 요청 URL: {url}")
        try:
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                token = response.text.strip()  # JSON이면 response.json().get("token") 등으로 교체
                log(f"✅ 토큰 요청 성공: {token}")
                return token
            else:
                log(f"❌ 토큰 요청 실패 - 상태 코드: {response.status_code}")
        except RequestException as e:
            log(f"🚨 토큰 요청 중 오류 발생: {e}")

        # 실패 fallback
        log("⚠️ 임시 토큰 사용")
        return TEST_TOKEN

    # 응답 대기
    def wait_for_response(self, request, timeout=3.0, interval=0.1):
        start = time.monotonic()
        while not request.response:
            if time.monotonic() - start > timeout:
                log(f"⏰ 응답 대기 시간 초과 (timeout={timeout}s) - URL: {request.url}")
                return None
            time.sleep(interval)
        return request.response

    # 요청 데이터 pase
    def parse_form_data(self, raw_body):
        decoded = unquote(raw_body)
        return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(decoded).items()}
    
    # 라우팅 처리
    def process_request(self, request):
        url = request.url
        method = request.method

        # 라우트 목록 정의
        routes = [
            Route('GET',  re.compile(fr'{BASE_BOOKING_PATH}/\d+(\?timestamp=|$)'),           self.handle_action, 'select'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/register(\?timestamp=|$)'),      self.handle_action, 'register'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/\d+/edit(\?timestamp=|$)'),      self.handle_action, 'edit'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/\d+/ajax-edit(\?timestamp=|$)'), self.handle_action, 'edit_move'),
            Route('POST', re.compile(fr'{BASE_BOOKING_PATH}/\d+/delete(\?timestamp=|$)'),    self.handle_action, 'delete'),
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
                self.handle_action_delete_mobile(request, 'delete_mobile')


    def send_to_external_api_set(self, req_json, resp_json, action):
        # 등록
        if action == "register":
            for entity in PayloadBuilder.extract_entities(resp_json):
                external_id    = entity.get("bookingNumber", [None])[0]
                machine_number = entity.get("machineNumber")
                reserve_no     = req_json.get("reserveNo") or None
                payload        = PayloadBuilder.register_or_edit(req_json, external_id, machine_number, reserve_no)
                self.send_to_external_api_action("register", payload)

        # 수정 : 웹 1개 수정, 웹 추가 수정, 모바일 1개 수정, 모바일 추가 수정
        elif action == "edit":
            entities = PayloadBuilder.extract_entities(resp_json)
            # 모바일 예약 번호
            reserve_no     = req_json.get("reserveNo") or None

            # 삭제 처리 [시작] ====================
            # 모바일 예약인 경우 externalGroupId가 reserve_no인 것을 모두 지운다.
            if reserve_no:
                payload = PayloadBuilder.delete("고객 취소", group_id=reserve_no)
            # 모바일 예약이 아닌경우 externalId 해당 예약만 지운다.
            else:
                external_id = req_json.get("bookingNumber")
                payload = PayloadBuilder.delete("추가 수정시 기존 취소", external_id=external_id)
            self.send_to_external_api_action("delete", payload)
            # 삭제 처리 [끝] ====================

            if entities:
                # 수정 예약
                for entity in entities:
                    external_id    = entity.get("bookingNumber", [None])[0]
                    machine_number = entity.get("machineNumber")
                    payload        = PayloadBuilder.register_or_edit(req_json, external_id, machine_number, reserve_no)
                    self.send_to_external_api_action("register", payload)
            else:
                external_id = req_json.get("bookingNumber")
                machine_number = req_json.get("machineNumber")
                payload = PayloadBuilder.register_or_edit(req_json, external_id, machine_number)
                self.send_to_external_api_action("edit", payload)

        # 마우스 드래그 앤 드랍으로 날짜와 room 수정
        elif action == "edit_move":
            payload = PayloadBuilder.edit_move(req_json)
            self.send_to_external_api_action("edit", payload)

        # 운영자 취소
        elif action == "delete":
            booking_nums = req_json.get("bookingNums", [])
            if isinstance(booking_nums, str):
                booking_nums = [booking_nums]  # 문자열인 경우 리스트로 변환
            for booking_number in booking_nums:
                payload = PayloadBuilder.delete("운영자 취소", external_id=booking_number)
                self.send_to_external_api_action("delete", payload)

        # 고객 취소
        elif action == "delete_mobile":
            reserve_no = (resp_json.get("entity", {})
                                   .get("destroy", [{}])[0]
                                   .get("reserveNo", ""))
            if reserve_no:
                payload = PayloadBuilder.delete("고객 취소", group_id=reserve_no)
                self.send_to_external_api_action("delete", payload)


    def handle_action(self, request, action):
        log(f"[{action}] : 시작 ==============================")
        log(f"[{action}] : 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            log(f"[{action}] : 조회 성공")
            try:
                log(f"[{action}] : Request Body")
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
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
                    self.send_to_external_api_set(req_json, resp_json, action)

            except Exception as e:
                log(f"[{action}] : 처리 오류 - {e}")
                log(f"[{action}] : 끝 ==============================")
        else:
            log(f"[{action}] : 요청 실패 또는 응답 없음")
            log(f"[{action}] : 끝 ==============================")


    def handle_action_delete_mobile(self, request, action):
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
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
                        self.send_to_external_api_set(req_json, resp_json, "polling_delete")
            except Exception as e:
                log(f"[{action}] : 처리 오류 - {e}")
                log(f"[{action}] : 끝 ==============================")
        else:
            log(f"[{action}] : 요청 실패 또는 응답 없음")
            log(f"[{action}] : 끝 ==============================")


    def send_to_external_api_action(self, action, payload):
        dumps_payload = json.dumps(payload, ensure_ascii=False, indent=2)
        log(f'payload : {dumps_payload}, action : {action}')
        filtered_payload = {
            k: v for k, v in payload.items()
            if v not in [None, '', [], {}]
        }
        log(f'filtered_payload : {filtered_payload}, action : {action}')

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            url = f"{EXTERNAL_API_BASE_URL}/stores/{self.store_id}/reservation/crawl"
            method = {"register": requests.post, "edit": requests.patch, "delete": requests.delete}.get(action)
            log(url)
            if method:
                response = method(url, headers=headers, json=filtered_payload)

                if response.status_code == 200 or response.status_code == 201:
                    log(f"✅ 외부 시스템에 [{action}] 요청 전송 성공")
                else:
                    log(f"❌ [{action}] 전송 실패 - 상태 코드: {response.status_code}")
                    try:
                        log(f"❗ 응답 내용: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
                    except Exception:
                        log(f"❗ 응답 본문 (raw): {response.text}")
            else:
                log(f"❗ 지원되지 않는 action: {action}")

        except Exception as e:
            log(f"API 호출 중 예외 발생: {e}")





