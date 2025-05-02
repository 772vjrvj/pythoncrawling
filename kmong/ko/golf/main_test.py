import time
import re
import json
from urllib.parse import parse_qs, unquote
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import requests
from urllib.parse import parse_qs, unquote
from datetime import datetime, timedelta


# 전역 변수
processed_requests = set()
last_booking_data = {}

# 외부 시스템 API 설정
EXTERNAL_API_BASE_URL = "https://api.dev.24golf.co.kr"
CRAWLING_SITE = "golfzonpark"
token = ""

def send_to_external_api(data, action):
    global token
    """
    외부 시스템 API에 예약 정보를 전달합니다.
    action: 'register', 'edit', 'delete'
    """
    # 외부 시스템의 storeId를 매핑합니다.
    store_id = data.get('shopNo')

    # 예약 정보를 외부 시스템 API의 요구사항에 맞게 변환합니다.
    payload = ""
    if action == "register" or action == "edit":
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
            "crawlingSite": CRAWLING_SITE,
            "requests": data.get("bookingMemo", "")
        }
    elif action == "delete":
        payload = {
            "externalId": data.get("bookingNumber"),
            "crawlingSite": CRAWLING_SITE,
            "reason": "고객 취소"
        }

    data = json.dumps(payload, ensure_ascii=False, indent=2)
    print(f'payload({action}) : {data}')

    if not token:
        token = get_golf_token(store_id)
        if token:
            print(f"▶ 토큰 조회 성공 : {token}")
        else:
            print(f"▶ 토큰 조회 실패")
            return
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        if action == "register":
            url = f"{EXTERNAL_API_BASE_URL}/stores/{store_id}/reservation/crawl"
            response = requests.post(url, headers=headers, json=payload)
        elif action == "edit":
            url = f"{EXTERNAL_API_BASE_URL}/stores/{store_id}/reservation/crawl"
            response = requests.patch(url, headers=headers, json=payload)
        elif action == "delete":
            url = f"{EXTERNAL_API_BASE_URL}/stores/{store_id}/reservation/crawl"
            response = requests.delete(url, headers=headers, json=payload)
        else:
            print(f"▶ 알 수 없는 작업: {action}")
            return

        if response.status_code == 200:
            print(f"✅ 외부 시스템에 {action} 요청을 성공적으로 전달했습니다.")
        else:
            print(f"❌ 외부 시스템에 {action} 요청을 전달하는 데 실패했습니다. 상태 코드: {response.status_code}")
    except Exception as e:
        print(f"▶ 외부 시스템 API 호출 중 오류 발생: {e}")


def get_golf_token(store_id):
    """
    외부 시스템에서 토큰을 가져옵니다.
    """

    try:
        url = f"{EXTERNAL_API_BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
        print(f"▶ 토큰 요청 url: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip('"')
        else:
            print(f"▶ 토큰 요청 실패. 상태 코드: {response.status_code}")
            return None
    except Exception as e:
        print(f"▶ 토큰 요청 중 오류 발생: {e}")
        return None


def convert_to_kst_datetime(kst_time_str):
    """
    KST 시간 문자열을 'yyyy-MM-dd HH:mm:ss' 형식으로 변환합니다.
    예: '20250530020000' → '2025-05-30 02:00:00'
    """
    try:
        kst_time = datetime.strptime(kst_time_str, "%Y%m%d%H%M%S")
        return kst_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"▶ 시간 변환 중 오류 발생: {e}")
        return None


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    seleniumwire_options = {
        'disable_encoding': True,
        'verify_ssl': True,
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

# 응답 도착을 기다리는 함수
def wait_for_response(request, timeout=3.0, interval=0.1):
    """
    응답이 도착할 때까지 최대 timeout 초 동안 대기
    """
    total_wait = 0.0
    while not request.response and total_wait < timeout:
        time.sleep(interval)
        total_wait += interval
    return request.response


def parse_form_data(raw_body):
    decoded = unquote(raw_body)
    return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(decoded).items()}


def handle_register(request):
    response = wait_for_response(request)
    if response and response.status_code == 200:
        print("\n📌 [등록 성공]")
        try:
            raw_body = request.body.decode('utf-8', errors='replace')
            parsed = parse_form_data(raw_body)
            print("▶ 등록 요청 Body (JSON 변환):")
            print(json.dumps(parsed, ensure_ascii=False, indent=2))

            response_body = response.body.decode('utf-8', errors='replace')
            response_json = json.loads(response_body)

            # 성공 여부 확인
            is_success = (
                    response_json.get("code") == "OK"
                    or str(response_json.get("status")) == "200"
            )

            if not is_success:
                print(f"❗ 등록 응답에서 성공 코드가 아님: {response_json}")
                return

            # bookingNumber 추출
            booking_number = None
            entity_list = response_json.get("entity") or response_json.get("entitys") or []
            for entity in entity_list:
                if isinstance(entity, dict) and "bookingNumber" in entity:
                    booking_number = entity["bookingNumber"][0]
                    break

            if booking_number:
                parsed["bookingNumber"] = str(booking_number)
                send_to_external_api(parsed, "register")
            else:
                print("❗ bookingNumber를 응답에서 찾을 수 없습니다.")

        except Exception as e:
            print(f"▶ 등록 요청 처리 중 오류 발생: {e}")


def handle_edit(request):
    response = wait_for_response(request)
    if response and response.status_code == 200:
        print("\n✏️ [수정 성공]")
        try:
            raw_body = request.body.decode('utf-8', errors='replace')
            parsed = parse_form_data(raw_body)
            print("▶ 수정 요청 Body (JSON 변환):")
            print(json.dumps(parsed, ensure_ascii=False, indent=2))

            response_body = response.body.decode('utf-8', errors='replace')
            response_json = json.loads(response_body)

            # 성공 여부 확인
            is_success = (
                    response_json.get("code") == "OK"
                    or str(response_json.get("status")) == "200"
            )

            if is_success:
                send_to_external_api(parsed, "edit")
            else:
                print(f"❗ 수정 응답에서 성공 코드가 아님: {response_json}")

        except Exception as e:
            print(f"▶ 수정 요청 처리 실패: {e}")


def handle_view(request):
    response = wait_for_response(request)  # 응답 대기 추가
    if response and response.status_code == 200:
        try:
            body = response.body.decode('utf-8', errors='replace')
            json_body = json.loads(body)

            if isinstance(json_body.get("entitys"), list):
                for booking in json_body["entitys"]:
                    print(f"▶ 조회된 예약:\n{json.dumps(booking, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"▶ 조회 응답 처리 실패: {e}")


def handle_delete(request):
    response = wait_for_response(request)
    if not response or response.status_code != 200:
        print("❌ 삭제 요청 응답 실패 또는 상태 코드 200 아님")
        return
    try:
        # 요청 바디 파싱
        raw_body = request.body.decode('utf-8', errors='replace')
        parsed = parse_form_data(raw_body)
        print("▶ 삭제 요청 Body (JSON 변환):")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))

        # 응답 바디 파싱 및 성공 여부 확인
        response_body = response.body.decode('utf-8', errors='replace')
        response_json = json.loads(response_body)

        # 성공 조건 확인 (code: OK 또는 status: "200")
        is_success = (
                response_json.get("code") == "OK"
                or str(response_json.get("status")) == "200"
        )

        if is_success:
            send_to_external_api(parsed, "delete")
        else:
            print(f"❗ 삭제 응답에서 성공 코드가 아님: {response_json}")

    except Exception as e:
        print(f"▶ 삭제 요청 처리 실패: {e}")


def process_request(request):
    url = request.url
    method = request.method

    if re.search(r'/rest/ui/booking/register(\?timestamp=|$)', url) and method == 'POST':
        handle_register(request)

    elif re.search(r'/rest/ui/booking/\d+/edit(\?timestamp=|$)', url) and method == 'POST':
        handle_edit(request)

    # elif re.search(r'/rest/ui/booking/\d+\?timestamp=', url):
    #     handle_view(request)

    elif re.search(r'/rest/ui/booking/\d+/delete(\?timestamp=|$)', url) and method == 'POST':
        handle_delete(request)


def main():
    driver = setup_driver()
    driver.get("https://gpm.golfzonpark.com/")
    print("⏳ 요청 감지 대기 중... Ctrl+C로 종료")

    try:
        while True:
            for request in list(driver.requests):
                # 응답이 아직 없으면 대기하지 않고 skip
                if request.id in processed_requests:
                    continue

                response = wait_for_response(request)
                if not response:
                    continue  # 응답이 없으면 다음으로

                # 여기서 처리 시작
                processed_requests.add(request.id)
                process_request(request)

            driver.requests.clear()
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n⛔ 종료 요청 감지, 브라우저 닫는 중...")
        driver.quit()


if __name__ == "__main__":
    main()
