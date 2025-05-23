import re
import json
from urllib.parse import urlparse, parse_qs

from src.route.route import Route
from src.utils.log import log, log_json
from src.utils.data_api import wait_for_response, parse_urlencoded_form

class RequestRouter:
    def __init__(self, service, base_booking_path, base_mobile_path, base_reservation_mobile_path):
        self.service = service
        self.base_booking_path = base_booking_path
        self.base_mobile_path = base_mobile_path
        self.base_reservation_mobile_path = base_reservation_mobile_path
        self.cached_entities = []
        self.routes = [
            Route('GET',  re.compile(fr'{self.base_booking_path}/\d+(\?timestamp=|$)'),           self.request_set, 'select'),
            Route('POST', re.compile(fr'{self.base_booking_path}/register(\?timestamp=|$)'),      self.request_set, 'register'),
            Route('POST', re.compile(fr'{self.base_booking_path}/\d+/edit(\?timestamp=|$)'),      self.request_set, 'edit'),
            Route('POST', re.compile(fr'{self.base_booking_path}/\d+/ajax-edit(\?timestamp=|$)'), self.request_set, 'edit_move'),
            Route('POST', re.compile(fr'{self.base_booking_path}/\d+/delete(\?timestamp=|$)'),    self.request_set, 'delete')
        ]

    def handle(self, request):
        url = request.url
        method = request.method
        parsed_path = urlparse(url).path

        for route in self.routes:
            if route.matches(method, url):
                route.handler(request, route.action)
                return

        # 특수 케이스: 모바일 삭제
        if method == 'GET' and parsed_path.startswith(self.base_mobile_path):
            log(f"[delete] : {parsed_path}")
            log(f"[delete] : {self.base_mobile_path}")
            params = parse_qs(urlparse(url).query)
            required_keys = {'timestamp', 'bookingStartDt', 'data', 'bookingNumber'}
            if required_keys.issubset(params):
                self.request_set_delete_mobile(request, 'delete_mobile')


    def request_set(self, request, action):
        response = wait_for_response(request)

        # 요청 바디 파싱
        try:
            req_json = parse_urlencoded_form(request.body.decode('utf-8', errors='replace'))
        except Exception as e:
            log(f"[{action}] : 요청 바디 디코딩 실패 - {e}")
            req_json = {}

        # 응답 유무 확인
        if response is None:
            log(f"[{action}] : 응답 없음 (response is None)")
            return

        # 응답 바디 파싱
        try:
            resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
        except Exception as e:
            log(f"[{action}] : 응답 바디 디코딩 실패 - {e}")
            resp_json = {}

        # 로그 출력 (select는 출력 생략)
        if action != 'select':
            log(f"[{action}] : Request Body")
            log_json(req_json)
            log(f"[{action}] : Response Body")
            log_json(resp_json)

        # 상태 코드 확인
        if response.status_code != 200:
            log(f"[{action}] : HTTP 응답 실패 (status code: {response.status_code})")


        try:
            # 응답 코드 및 상태 체크
            if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                log(f"[{action}] : 응답 실패 (code: {resp_json.get('code')}, status: {resp_json.get('status')})")


            # SELECT 요청인 경우 캐시 저장
            if action == 'select':
                entities = resp_json.get("entitys", [])
                if isinstance(entities, list):
                    self.cached_entities = entities
                    # log(f"[{action}] : {len(entities)}건의 예약 데이터를 캐시에 저장했습니다.")
            else:
                self.dispatch_action(req_json, resp_json, action)

        except Exception as e:
            log(f"[{action}] : 처리 중 예외 발생 - {e}")

    def request_set_delete_mobile(self, request, action):
        response = wait_for_response(request)
        if response:
            try:
                req_json = parse_urlencoded_form(request.body.decode('utf-8', errors='replace'))
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                if resp_json.get("code") == "OK" and str(resp_json.get("status")) == "200":
                    if resp_json.get("entity", {}).get("destroy", []):
                        self.dispatch_action(req_json, resp_json, 'delete_mobile')
            except Exception as e:
                log(f"[{action}] : 처리 오류 - {e}")

    def dispatch_action(self, req_json, resp_json, action):
        action_map = {
            "register": self.service.register,
            "edit": self.service.edit,
            "edit_move": self.service.edit_move,
            "delete": self.service.delete_admin,
            "delete_mobile": self.service.delete_mobile,
        }
        processor = action_map.get(action)
        if processor:
            processor(req_json, resp_json)
        else:
            log(f"🚫 알 수 없는 action: {action}")
