from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Chrome 설정
chrome_options = Options()
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

seleniumwire_options = {
    'disable_encoding': True,
}

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options,
    seleniumwire_options=seleniumwire_options
)

driver.get("https://gpm.golfzonpark.com/")

print("⏳ 예약 요청 감지 대기 중... Ctrl+C로 종료")

processed_requests = set()

try:
    while True:
        for request in driver.requests:
            if request.id in processed_requests:
                continue

            if '/rest/ui/booking/' in request.url:
                print(f"\n[📡 요청 감지] {request.url}")
                print(f"▶ Method: {request.method}")
                if request.body:
                    print(f"▶ 요청 Body: {request.body.decode('utf-8', errors='replace')[:500]}...")

                if request.response:
                    print(f"[📦 응답 감지] {request.url}")
                    print(f"▶ 상태 코드: {request.response.status_code}")
                    if request.response.body:
                        print(f"▶ 응답 Body: {request.response.body.decode('utf-8', errors='replace')[:500]}...")

            processed_requests.add(request.id)

        time.sleep(1)

except KeyboardInterrupt:
    driver.quit()
