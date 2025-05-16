import re
import time
import json
import requests

from PyQt5.QtCore import QThread
from urllib.parse import unquote
from urllib.parse import urlparse, parse_qs
from src.utils.log_util import log
from src.utils.config import EXTERNAL_API_BASE_URL, CRAWLING_SITE, SITE_URL, TEST_TOKEN
from src.utils.time_utils import to_iso_format
from src.utils.utils_selenium import SeleniumDriverManager

class ApiGolfzonparkSetLoadWorker(QThread):

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


    def init(self):
        self.token = self.get_golf_token()


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


    def stop(self):
        self.driver.quit()


    def process_request(self, request):
        url = request.url
        method = request.method

        if re.search(r'/rest/ui/booking/\d+(\?timestamp=|$)', url) and method == 'GET':
            self.handle_select(request)
        elif re.search(r'/rest/ui/booking/register(\?timestamp=|$)', url) and method == 'POST':
            self.handle_register(request)
        elif re.search(r'/rest/ui/booking/\d+/edit(\?timestamp=|$)', url) and method == 'POST':
            self.handle_edit(request)
        elif re.search(r'/rest/ui/booking/\d+/ajax-edit(\?timestamp=|$)', url) and method == 'POST':
            # 드래그 변경 시간, 룸
            self.handle_ajax_edit(request)
        elif re.search(r'/rest/ui/booking/\d+/delete(\?timestamp=|$)', url) and method == 'POST':
            self.handle_delete(request)
        elif re.search(r'/rest/ui/polling/booking/\d+', url) and method == 'GET':
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if 'timestamp' in params and 'bookingStartDt' in params and 'data' in params and 'bookingNumber' in params:
                self.handle_polling_delete(request, params)


    def wait_for_response(self, request, timeout=3.0, interval=0.1):
        total_wait = 0.0
        while not request.response and total_wait < timeout:
            time.sleep(interval)
            total_wait += interval
        return request.response


    # 요청 데이터 pase
    def parse_form_data(self, raw_body):
        decoded = unquote(raw_body)
        return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(decoded).items()}


    def get_golf_token(self):
        try:
            url = f"{EXTERNAL_API_BASE_URL}/auth/token/stores/{self.store_id}/role/singleCrawler"
            log(f"토큰 요청 url: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                token = response.text.strip()
                log(f'토큰 요청 성공 : {token}')
                return token
            else:
                log(f"토큰 요청 실패. 상태 코드: {response.status_code}")
                token = TEST_TOKEN
                log(f"임시 토큰 사용")
                return token
        except Exception as e:
            log(f"토큰 요청 중 오류 발생: {e}")
            return None


    def send_to_external_api_set(self, req_json, resp_json, action, params):
        if action == "register":
            entities = resp_json.get("entitys") or resp_json.get("entity") or []
            externalGroupId = ""
            for index, entity in enumerate(entities):
                if index == 0:
                    externalGroupId = str(entity.get("bookingNumber", [None])[0])
                booking_number = str(entity.get("bookingNumber", [None])[0])
                machine_number = str(entity.get("machineNumber"))

                payload = {
                    "externalId": booking_number,
                    "externalGroupId": externalGroupId,
                    "name": req_json.get("bookingName"),
                    "phone": req_json.get("cellNumber"),
                    "partySize": int(req_json.get("bookingCnt", 1)),
                    "startDate": to_iso_format(req_json.get("bookingStartDt")),
                    "endDate": to_iso_format(req_json.get("bookingEndDt")),
                    "roomId": machine_number,
                    "paymented": req_json.get("paymentYn", "N") == "Y",
                    "paymentAmount": int(req_json.get("paymentAmount", 0)),
                    "crawlingSite": CRAWLING_SITE,
                    "requests": req_json.get("bookingMemo", "")
                }

                self.send_to_external_api_action("register", payload)

        elif action == "edit":
            entities = resp_json.get("entitys") or resp_json.get("entity") or []
            if entities:
                # 기존 예약 사라진다.
                payload = {
                    "externalId": str(req_json.get("bookingNumber")),
                    "crawlingSite": CRAWLING_SITE,
                    "reason": "추가 수정시 기존 취소"
                }

                self.send_to_external_api_action("delete", payload)

                for entity in entities:
                    entity_booking_number = str(entity.get("bookingNumber", [None])[0])
                    machine_number = str(entity.get("machineNumber"))
                    payload = {
                        "externalGroupId": req_json.get("bookingNumber"),
                        "externalId": entity_booking_number,
                        "name": req_json.get("bookingName"),
                        "phone": req_json.get("cellNumber"),
                        "partySize": int(req_json.get("bookingCnt", 1)),
                        "startDate": to_iso_format(req_json.get("bookingStartDt")),
                        "endDate": to_iso_format(req_json.get("bookingEndDt")),
                        "roomId": machine_number,
                        "paymented": req_json.get("paymentYn", "N") == "Y",
                        "paymentAmount": int(req_json.get("paymentAmount", 0)),
                        "crawlingSite": CRAWLING_SITE,
                        "requests": req_json.get("bookingMemo", "")
                    }
                    self.send_to_external_api_action("register", payload)
            else:
                payload = {
                    "externalId": req_json.get("bookingNumber"),
                    "name": req_json.get("bookingName"),
                    "phone": req_json.get("cellNumber"),
                    "partySize": int(req_json.get("bookingCnt", 1)),
                    "startDate": to_iso_format(req_json.get("bookingStartDt")),
                    "endDate": to_iso_format(req_json.get("bookingEndDt")),
                    "roomId": req_json.get("machineNumber"),
                    "paymented": req_json.get("paymentYn", "N") == "Y",
                    "paymentAmount": int(req_json.get("paymentAmount", 0)),
                    "crawlingSite": CRAWLING_SITE,
                    "requests": req_json.get("bookingMemo", "")
                }
                self.send_to_external_api_action("edit", payload)

        elif action == "ajax_edit":
            booking_number = str(req_json.get("bookingNumber"))
            payload = {
                "externalId": booking_number,
                "startDate": to_iso_format(req_json.get("bookingStartDt")),
                "endDate": to_iso_format(req_json.get("bookingEndDt")),
                "roomId": req_json.get("machineNumber"),
                "crawlingSite": CRAWLING_SITE
            }
            self.send_to_external_api_action("edit", payload)

        elif action == "delete":
            booking_nums = req_json.get("bookingNums", [])
            if isinstance(booking_nums, str):
                booking_nums = [booking_nums]  # 문자열인 경우 리스트로 변환
            for booking_number in booking_nums:
                payload = {
                    "externalId": str(booking_number),
                    "crawlingSite": CRAWLING_SITE,
                    "reason": "고객 취소"
                }
                self.send_to_external_api_action("delete", payload)

        elif action == "polling_delete":
            if resp_json.get("entity") and resp_json.get("destroy"):
                # 협의필요
                booking_number = params.get("bookingNumber", [None])[0]
                payload = {
                    "externalGroupId": str(booking_number),
                    "crawlingSite": CRAWLING_SITE,
                    "reason": "고객 취소"
                }
                self.send_to_external_api_action("delete", payload)


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


    def handle_select(self, request):
        log(f"조회 대기중...")
        response = self.wait_for_response(request)

        if response and response.status_code == 200:
            log("\n📌 [조회 성공]")
            try:
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                log("조회 응답 Body:")
                log(json.dumps(resp_json, ensure_ascii=False, indent=2))

                entities = resp_json.get("entitys", [])
                if not isinstance(entities, list):
                    log("❗ entitys는 리스트가 아님")
                    return

                self.cached_entities = entities
                log(f"✔ {len(entities)}건의 예약 데이터를 캐시에 저장했습니다.")
                log(f"✔ {entities}")

            except Exception as e:
                log(f"조회 처리 오류: {e}")
        else:
            log("❗ 조회 실패 또는 응답 없음")


    def handle_register(self, request):
        log(f"등록 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            log("\n📌 [등록 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                log("등록 요청 Body:")
                log(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                log("등록 응답:")
                log(json.dumps(resp_json, ensure_ascii=False, indent=2))
                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                    log("❗ 등록 실패 응답")
                    return

                self.send_to_external_api_set(req_json, resp_json, "register", None)

            except Exception as e:
                log(f"등록 오류: {e}")


    def handle_edit(self, request):
        log(f"수정 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            log("\n✏️ [수정 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                log("수정 요청 Body:")
                log(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                log("수정 응답:")
                log(json.dumps(resp_json, ensure_ascii=False, indent=2))

                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api_set(req_json, resp_json, "edit", None)
                else:
                    log(f"❗ 수정 실패 응답: {resp_json}")
            except Exception as e:
                log(f"수정 처리 오류: {e}")


    def handle_ajax_edit(self, request):
        log(f"ajax 수정 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            log("\n✏️ [ajax 수정 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                log("ajax 수정 요청 Body:")
                log(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                log("ajax 수정 응답:")
                log(json.dumps(resp_json, ensure_ascii=False, indent=2))

                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api_set(req_json, resp_json, "ajax_edit", None)
                else:
                    log(f"❗ ajax 수정 실패 응답: {resp_json}")
            except Exception as e:
                log(f"ajax 수정 처리 오류: {e}")


    def handle_delete(self, request):
        log(f"삭제 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            log("\n🗑️ [삭제 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                log("삭제 요청 Body:")
                log(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                log("삭제 응답:")
                log(json.dumps(resp_json, ensure_ascii=False, indent=2))

                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api_set(req_json, resp_json, "delete", None)
                else:
                    log(f"❗ 삭제 실패 응답: {resp_json}")
            except Exception as e:
                log(f"삭제 처리 오류: {e}")
        else:
            log("❌ 삭제 응답 없음 또는 실패")


    def handle_polling_delete(self, request, params):
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                if resp_json.get("destroy"):
                    log("모바일 삭제 응답:")
                    log(json.dumps(resp_json, ensure_ascii=False, indent=2))

                    if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                        self.send_to_external_api_set(req_json, resp_json, "polling_delete", params)
                    else:
                        log(f"❗ 모바일 삭제 실패 응답: {resp_json}")
            except Exception as e:
                log(f"모바일 삭제 처리 오류: {e}")
        else:
            log("❌ 모바일 삭제 응답 없음 또는 실패")






