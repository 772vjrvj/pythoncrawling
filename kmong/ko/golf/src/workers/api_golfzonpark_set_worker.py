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
    log_signal = pyqtSignal(str)
    msg_signal = pyqtSignal(str, str)

    EXTERNAL_API_BASE_URL = "https://api.dev.24golf.co.kr"
    CRAWLING_SITE = (""
                     "")

    def __init__(self):
        super().__init__()
        self.processed_requests = set()
        self.token = ""
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
            self.log_signal.emit(f"▶ 시간 변환 중 오류 발생: {e}")
            return None

    def get_golf_token(self, store_id):
        try:
            url = f"{self.EXTERNAL_API_BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
            self.log_signal.emit(f"▶ 토큰 요청 url: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                return response.text.strip('"')
            else:
                self.log_signal.emit(f"▶ 토큰 요청 실패. 상태 코드: {response.status_code}")
                token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2OTBkN2VhNzUwZmY5YTY2ODllOWFmMyIsInJvbGUiOiJzaW5nbGVDcmF3bGVyIiwiZXhwIjo0ODk4ODQ0MDc3fQ.aEUYvIzMhqW6O2h6hQTG8IfzJNhpvll4fOdN7udz1yc"
                self.log_signal.emit(f"▶ 임시 토큰 사용")
                return token
        except Exception as e:
            self.log_signal.emit(f"▶ 토큰 요청 중 오류 발생: {e}")
            return None

    def send_to_external_api(self, data, action):
        payload = {}
        if action in ("register", "edit"):
            payload = {
                "externalId": data.get("bookingNumber"),
                "name": data.get("bookingName"),
                "phone": data.get("cellNumber"),
                "partySize": int(data.get("bookingCnt", 1)),
                "startDate": data.get("bookingStartDt"),
                "endDate": data.get("bookingEndDt"),
                "roomId": data.get("machineNumber"),
                "paymented": data.get("paymentYn", "N") == "Y",
                "paymentAmount": int(data.get("paymentAmount", 0)),
                "crawlingSite": self.CRAWLING_SITE,
                "requests": data.get("bookingMemo", "")
            }
        elif action == "delete":
            payload = {
                "externalId": data.get("bookingNumber"),
                "crawlingSite": self.CRAWLING_SITE,
                "reason": "고객 취소"
            }

        self.log_signal.emit(json.dumps(payload, ensure_ascii=False, indent=2))

        if not self.token:
            self.token = self.get_golf_token(data.get('shopNo'))
            if not self.token:
                return

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            url = f"{self.EXTERNAL_API_BASE_URL}/stores/{data.get('shopNo')}/reservation/crawl"
            method = {"register": requests.post, "edit": requests.patch, "delete": requests.delete}.get(action)
            if method:
                response = method(url, headers=headers, json=payload)
                if response.status_code == 200:
                    self.log_signal.emit(f"✅ 외부 시스템에 {action} 요청 전송 성공")
                else:
                    self.log_signal.emit(f"❌ 전송 실패 - 상태 코드: {response.status_code}")
        except Exception as e:
            self.log_signal.emit(f"▶ API 호출 오류: {e}")

    def handle_register(self, request):
        self.log_signal.emit(f"등록 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            self.log_signal.emit("\n📌 [등록 성공]")
            try:
                parsed = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                self.log_signal.emit("▶ 등록 요청 Body:")
                self.log_signal.emit(json.dumps(parsed, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                if resp_json.get("code") != "OK" and str(resp_json.get("status")) != "200":
                    self.log_signal.emit("❗ 등록 실패 응답")
                    return

                for entity in resp_json.get("entity", []) + resp_json.get("entitys", []):
                    if "bookingNumber" in entity:
                        parsed["bookingNumber"] = str(entity["bookingNumber"][0])
                        self.send_to_external_api(parsed, "register")
                        return

                self.log_signal.emit("❗ bookingNumber 없음")
            except Exception as e:
                self.log_signal.emit(f"▶ 등록 오류: {e}")

    def handle_edit(self, request):
        self.log_signal.emit(f"수정 대기중...")
        response = self.wait_for_response(request)
        if response and response.status_code == 200:
            self.log_signal.emit("\n✏️ [수정 성공]")
            try:
                parsed = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
                self.log_signal.emit("▶ 수정 요청 Body:")
                self.log_signal.emit(json.dumps(parsed, ensure_ascii=False, indent=2))

                resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
                if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                    self.send_to_external_api(parsed, "edit")
                else:
                    self.log_signal.emit(f"❗ 수정 실패 응답: {resp_json}")
            except Exception as e:
                self.log_signal.emit(f"▶ 수정 오류: {e}")

    def handle_delete(self, request):
        self.log_signal.emit(f"삭제 대기중...")
        response = self.wait_for_response(request)
        if not response or response.status_code != 200:
            self.log_signal.emit("❌ 삭제 응답 없음 또는 실패")
            return
        try:
            parsed = self.parse_form_data(request.body.decode('utf-8', errors='replace'))
            self.log_signal.emit("▶ 삭제 요청 Body:")
            self.log_signal.emit(json.dumps(parsed, ensure_ascii=False, indent=2))

            resp_json = json.loads(response.body.decode('utf-8', errors='replace'))
            if resp_json.get("code") == "OK" or str(resp_json.get("status")) == "200":
                self.send_to_external_api(parsed, "delete")
            else:
                self.log_signal.emit(f"❗ 삭제 실패 응답: {resp_json}")
        except Exception as e:
            self.log_signal.emit(f"▶ 삭제 오류: {e}")

    def process_request(self, request):
        url = request.url
        method = request.method

        if re.search(r'/rest/ui/booking/register(\?timestamp=|$)', url) and method == 'POST':
            self.handle_register(request)
        elif re.search(r'/rest/ui/booking/\d+/edit(\?timestamp=|$)', url) and method == 'POST':
            self.handle_edit(request)
        elif re.search(r'/rest/ui/booking/\d+/delete(\?timestamp=|$)', url) and method == 'POST':
            self.handle_delete(request)

    def run(self):
        self.driver.get("https://gpm.golfzonpark.com/")
        self.log_signal.emit("⏳ 등록, 수정, 삭제시 API 호출을 진행합니다... ")
        self.log_signal.emit("⏳ 요청 감지 대기 중... ")

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
            self.log_signal.emit("⛔ 종료 요청 감지, 브라우저 닫는 중...")
            self.driver.quit()

    def stop(self):
        self.driver.quit()
