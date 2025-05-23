import re
import json
from urllib.parse import urlparse, parse_qs

from src.route.route import Route
from src.utils.log import log, log_json
from src.utils.data_api import wait_for_response, parse_urlencoded_form

class RequestRouter:
    def __init__(self, service, base_booking_path, base_mobile_path):
        self.service = service
        self.base_booking_path = base_booking_path
        self.base_mobile_path = base_mobile_path
        self.cached_entities = []
        self.routes = [
            Route('GET',  re.compile(fr'{self.base_booking_path}/\d+(\?timestamp=|$)'),           self.request_set, 'select'),
            Route('POST', re.compile(fr'{self.base_booking_path}/register(\?timestamp=|$)'),      self.request_set, 'register'),
            Route('POST', re.compile(fr'{self.base_booking_path}/\d+/edit(\?timestamp=|$)'),      self.request_set, 'edit'),
            Route('POST', re.compile(fr'{self.base_booking_path}/\d+/ajax-edit(\?timestamp=|$)'), self.request_set, 'edit_move'),
            Route('POST', re.compile(fr'{self.base_booking_path}/\d+/delete(\?timestamp=|$)'),    self.request_set, 'delete'),
        ]

    def handle(self, request):
        url = request.url
        method = request.method

        for route in self.routes:
            if route.matches(method, url):
                route.handler(request, route.action)
                return

        # 특수 케이스: 모바일 삭제
        if method == 'GET' and url.startswith(self.base_mobile_path):
            params = parse_qs(urlparse(url).query)
            required_keys = {'timestamp', 'bookingStartDt', 'data', 'bookingNumber'}
            if required_keys.issubset(params):
                self.request_set_delete_mobile(request, 'delete_mobile')

    def request_set(self, request, action):
        response = wait_for_response(request)
        if response and response.status_code == 200:
            try:
                req_json = parse_urlencoded_form(request.body.decode('utf-8', errors='replace'))
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))

                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                    log(f"[{action}] : 응답 실패 {resp_json.get('status')}")
                    return

                if action == 'select':
                    entities = resp_json.get("entitys", [])
                    if isinstance(entities, list):
                        self.cached_entities = entities
                        # log(f"[{action}] : {len(entities)}건의 예약 데이터를 캐시에 저장했습니다.")
                else:
                    log(f"[{action}] : Request Body")
                    log_json(req_json)
                    log(f"[{action}] : Response Body")
                    log_json(resp_json)
                    self.dispatch_action(req_json, resp_json, action)

            except Exception as e:
                log(f"[{action}] : 처리 오류 - {e}")
        else:
            log(f"[{action}] : 요청 실패 또는 응답 없음")

    def request_set_delete_mobile(self, request, action):
        response = wait_for_response(request)
        if response and response.status_code == 200:
            try:
                req_json = parse_urlencoded_form(request.body.decode('utf-8', errors='replace'))
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
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
