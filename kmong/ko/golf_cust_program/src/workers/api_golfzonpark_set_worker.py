import time
import re
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

class ApiGolfzonparkSetLoadWorker(QThread):

    EXTERNAL_API_BASE_URL = "https://api.dev.24golf.co.kr"
    CRAWLING_SITE = ("GolfzonPark")

    def __init__(self, user_id, password, store_id):
        super().__init__()
        self.processed_requests = set()
        self.token = ""
        self.user_id = user_id
        self.password = password
        self.store_id = store_id
        self.cached_entities = []
        self.driver = self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # PyInstaller 환경을 고려한 인증서 경로 설정
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        cert_dir = os.path.join(base_path, 'seleniumwire')
        cert_path = os.path.join(cert_dir, 'ca.crt')
        key_path = os.path.join(cert_dir, 'ca.key')

        print(f"cert_path: {cert_path}")
        print(f"key_path: {key_path}")

        seleniumwire_options = {
            'disable_encoding': True,
            'verify_ssl': True,
            'intercept': True,  # 후킹 활성화
            'ca_cert': cert_path,
            'ca_key': key_path,
            'exclude_hosts': [
                'gstatic.com', 'google.com', 'googletagmanager.com', 'gvt1.com',
                'polyfill-fastly.io', 'fonts.googleapis.com', 'fonts.gstatic.com',
                'bizmall.golfzon.com', 'uf.gzcdn.net', 'https://i.gzcdn.net'
            ]
        }

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
        })

        return driver

    def wait_for_response(self, request, timeout=3.0, interval=0.1):
        total_wait = 0.0
        while not request.response and total_wait < timeout:
            time.sleep(interval)
            total_wait += interval
        return request.response

    def parse_form_data(self, raw_body):
        decoded = unquote(raw_body)
        return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(decoded).items()}

    def convert_to_kst_datetime(self, kst_time_str):
        try:
            kst_time = datetime.strptime(kst_time_str, "%Y%m%d%H%M%S")
            return kst_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"▶ 시간 변환 중 오류 발생: {e}")
            return None

    def to_iso_format(self, kst_str):
        try:
            # '20250530102000' → datetime 객체로 파싱
            dt = datetime.strptime(kst_str, "%Y%m%d%H%M%S")
            # ISO 포맷 + 한국 시간대 오프셋
            return dt.isoformat() + "+09:00"
        except Exception as e:
            print(f"❗ 날짜 변환 오류: {e}")
            return kst_str


    def get_golf_token(self):
        try:
            url = f"{self.EXTERNAL_API_BASE_URL}/auth/token/stores/{self.store_id}/role/singleCrawler"
            print(f"▶ 토큰 요청 url: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                token = response.text.strip()
                print(f'▶ 토큰 요청 성공 : {token}')
                return token
            else:
                print(f"▶ 토큰 요청 실패. 상태 코드: {response.status_code}")
                token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2OTBkN2VhNzUwZmY5YTY2ODllOWFmMyIsInJvbGUiOiJzaW5nbGVDcmF3bGVyIiwiZXhwIjo0ODk4ODQ0MDc3fQ.aEUYvIzMhqW6O2h6hQTG8IfzJNhpvll4fOdN7udz1yc"
                print(f"▶ 임시 토큰 사용")
                return token
        except Exception as e:
            print(f"▶ 토큰 요청 중 오류 발생: {e}")
            return None

    def send_to_external_api_set(self, req_json, resp_json, action):

        if action == "register":
            entities = resp_json.get("entitys") or resp_json.get("entity") or []
            for entity in entities:
                booking_number = str(entity.get("bookingNumber", [None])[0])
                machine_number = str(entity.get("machineNumber"))

                payload = {
                    "externalId": booking_number,
                    "name": req_json.get("bookingName"),
                    "phone": req_json.get("cellNumber"),
                    "partySize": int(req_json.get("bookingCnt", 1)),
                    "startDate": self.to_iso_format(req_json.get("bookingStartDt")),
                    "endDate": self.to_iso_format(req_json.get("bookingEndDt")),
                    "roomId": machine_number,
                    "paymented": req_json.get("paymentYn", "N") == "Y",
                    "paymentAmount": int(req_json.get("paymentAmount", 0)),
                    "crawlingSite": self.CRAWLING_SITE,
                    "requests": req_json.get("bookingMemo", "")
                }

                self.send_to_external_api_action("register", payload)

        elif action == "edit":
            entities = resp_json.get("entitys") or resp_json.get("entity") or []
            if entities:
                # 기존 예약 사라진다.
                payload = {
                    "externalId": str(req_json.get("bookingNumber")),
                    "crawlingSite": self.CRAWLING_SITE,
                    "reason": "추가 수정시 기존 취소"
                }

                self.send_to_external_api_action("delete", payload)

                for entity in entities:
                    entity_booking_number = str(entity.get("bookingNumber", [None])[0])
                    machine_number = str(entity.get("machineNumber"))
                    payload = {
                        "externalId": entity_booking_number,
                        "name": req_json.get("bookingName"),
                        "phone": req_json.get("cellNumber"),
                        "partySize": int(req_json.get("bookingCnt", 1)),
                        "startDate": self.to_iso_format(req_json.get("bookingStartDt")),
                        "endDate": self.to_iso_format(req_json.get("bookingEndDt")),
                        "roomId": machine_number,
                        "paymented": req_json.get("paymentYn", "N") == "Y",
                        "paymentAmount": int(req_json.get("paymentAmount", 0)),
                        "crawlingSite": self.CRAWLING_SITE,
                        "requests": req_json.get("bookingMemo", "")
                    }
                    self.send_to_external_api_action("register", payload)
            else:
                payload = {
                    "externalId": req_json.get("bookingNumber"),
                    "name": req_json.get("bookingName"),
                    "phone": req_json.get("cellNumber"),
                    "partySize": int(req_json.get("bookingCnt", 1)),
                    "startDate": self.to_iso_format(req_json.get("bookingStartDt")),
                    "endDate": self.to_iso_format(req_json.get("bookingEndDt")),
                    "roomId": req_json.get("machineNumber"),
                    "paymented": req_json.get("paymentYn", "N") == "Y",
                    "paymentAmount": int(req_json.get("paymentAmount", 0)),
                    "crawlingSite": self.CRAWLING_SITE,
                    "requests": req_json.get("bookingMemo", "")
                }
                self.send_to_external_api_action("edit", payload)
        elif action == "ajax_edit":
            booking_number = str(req_json.get("bookingNumber"))
            matched_entity = next(
                (e for e in self.cached_entities if str(e.get("bookingNumber")) == booking_number),
                None
            )
            if not matched_entity:
                print(f"❗ ajax_edit: 작업실패 {booking_number}")
                return  # 작업 중단
            payload = {
                "externalId": booking_number,
                "name": matched_entity.get("bookingName"),
                "phone": matched_entity.get("cellNumber"),
                "partySize": int(matched_entity.get("bookingCnt", 1)),
                "startDate": self.to_iso_format(req_json.get("bookingStartDt")),
                "endDate": self.to_iso_format(req_json.get("bookingEndDt")),
                "roomId": req_json.get("machineNumber"),
                "paymented": matched_entity.get("paymentYn") == "Y",
                "paymentAmount": int(matched_entity.get("paymentAmount", 0)),
                "crawlingSite": self.CRAWLING_SITE,
                "requests": matched_entity.get("bookingMemo")
            }
            self.send_to_external_api_action("edit", payload)
        elif action == "delete":
            booking_nums = req_json.get("bookingNums", [])
            if isinstance(booking_nums, str):
                booking_nums = [booking_nums]  # 문자열인 경우 리스트로 변환
            for booking_number in booking_nums:
                payload = {
                    "externalId": str(booking_number),
                    "crawlingSite": self.CRAWLING_SITE,
                    "reason": "고객 취소"
                }
                self.send_to_external_api_action("delete", payload)



    def send_to_external_api_action(self, action, payload):
        dumps_payload = json.dumps(payload, ensure_ascii=False, indent=2)
        print(f'payload : {dumps_payload}, action : {action}')

        if not self.token:
            self.token = self.get_golf_token()
            if not self.token:
                return

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            url = f"{self.EXTERNAL_API_BASE_URL}/stores/{self.store_id}/reservation/crawl"
            method = {"register": requests.post, "edit": requests.patch, "delete": requests.delete}.get(action)
            print(url)
            if method:
                response = method(url, headers=headers, json=payload)

                if response.status_code == 200 or response.status_code == 201:
                    print(f"✅ 외부 시스템에 [{action}] 요청 전송 성공")
                else:
                    print(f"❌ [{action}] 전송 실패 - 상태 코드: {response.status_code}")
                    try:
                        print("❗ 응답 내용:", json.dumps(response.json(), ensure_ascii=False, indent=2))
                    except Exception:
                        print("❗ 응답 본문 (raw):", response.text)
            else:
                print(f"❗ 지원되지 않는 action: {action}")

        except Exception as e:
            print(f"▶ API 호출 중 예외 발생: {e}")


    def handle_select(self, request):
        print(f"조회 대기중...")
        response = self.wait_for_response(request)

        if response and response.status_code == 200:
            print("\n📌 [조회 성공]")
            try:
                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                print("▶ 조회 응답 Body:")
                print(json.dumps(resp_json, ensure_ascii=False, indent=2))

                entities = resp_json.get("entitys", [])
                if not isinstance(entities, list):
                    print("❗ entitys는 리스트가 아님")
                    return

                self.cached_entities = entities
                print(f"✔ {len(entities)}건의 예약 데이터를 캐시에 저장했습니다.")
                print(f"✔ {entities}")

            except Exception as e:
                print(f"▶ 조회 처리 오류: {e}")
        else:
            print("❗ 조회 실패 또는 응답 없음")


    def handle_register(self, request):
        print(f"등록 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            print("\n📌 [등록 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                print("▶ 등록 요청 Body:")
                print(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                print("▶ 등록 응답:")
                print(json.dumps(resp_json, ensure_ascii=False, indent=2))
                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                    print("❗ 등록 실패 응답")
                    return

                self.send_to_external_api_set(req_json, resp_json, "register")

            except Exception as e:
                print(f"▶ 등록 오류: {e}")

    def handle_edit(self, request):
        print(f"수정 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            print("\n✏️ [수정 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                print("▶ 수정 요청 Body:")
                print(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                print("▶ 수정 응답:")
                print(json.dumps(resp_json, ensure_ascii=False, indent=2))

                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api_set(req_json, resp_json, "edit")
                else:
                    print(f"❗ 수정 실패 응답: {resp_json}")
            except Exception as e:
                print(f"▶ 수정 처리 오류: {e}")

    def handle_ajax_edit(self, request):
        print(f"ajax 수정 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            print("\n✏️ [ajax 수정 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                print("▶ ajax 수정 요청 Body:")
                print(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                print("▶ ajax 수정 응답:")
                print(json.dumps(resp_json, ensure_ascii=False, indent=2))

                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api_set(req_json, resp_json, "ajax_edit")
                else:
                    print(f"❗ ajax 수정 실패 응답: {resp_json}")
            except Exception as e:
                print(f"▶ ajax 수정 처리 오류: {e}")


    def handle_delete(self, request):
        print(f"삭제 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            print("\n🗑️ [삭제 성공]")
            try:
                req_json = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                print("▶ 삭제 요청 Body:")
                print(json.dumps(req_json, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                print("▶ 삭제 응답:")
                print(json.dumps(resp_json, ensure_ascii=False, indent=2))

                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api_set(req_json, resp_json, "delete")
                else:
                    print(f"❗ 삭제 실패 응답: {resp_json}")
            except Exception as e:
                print(f"▶ 삭제 처리 오류: {e}")
        else:
            print("❌ 삭제 응답 없음 또는 실패")



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

    def run(self):
        self.driver.get("https://gpm.golfzonpark.com/")
        print("⏳ 등록, 수정, 삭제시 API 호출을 진행합니다... ")

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

            print("✅ 로그인 시도 완료")

        except Exception as e:
            print(f"❌ 로그인 중 오류 발생: {e}")
            return

        print("⏳ 요청 감지 대기 중... ")

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
            print("⛔ 종료 요청 감지, 브라우저 닫는 중...")
            self.driver.quit()

    def stop(self):
        self.driver.quit()
