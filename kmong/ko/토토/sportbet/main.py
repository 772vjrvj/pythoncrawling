from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
import json

def setup_driver():
    chrome_options = Options()

    # 헤드리스 모드로 실행
    # chrome_options.add_argument("--headless")

    # GPU 비활성화
    chrome_options.add_argument("--disable-gpu")

    # 샌드박스 보안 모드를 비활성화합니다.
    chrome_options.add_argument("--no-sandbox")

    # /dev/shm 사용 비활성화
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 시크릿 모드로 실행
    chrome_options.add_argument("--incognito")

    # 사용자 에이전트를 설정하여 브라우저의 기본값 대신 특정 값을 사용하게 합니다.
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 웹 드라이버를 사용한 자동화임을 나타내는 Chrome의 플래그를 비활성화하여 자동화 도구의 사용을 숨깁니다.
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # 자동화 확장 기능의 사용을 비활성화합니다.
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 사용하여 호환되는 크롬 드라이버를 자동으로 다운로드하고 설치합니다.
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 크롬 개발자 프로토콜 명령을 실행하여 브라우저의 navigator.webdriver 속성을 수정함으로써, 자동화 도구 사용을 감지하고 차단하는 스크립트를 우회합니다.
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    return driver

def get_event_ids():
    driver = setup_driver()
    event_ids = []

    try:
        # 사이트로 이동
        driver.get("https://sportbet.one/sports/soccer")

        time.sleep(5)
        # class="event-short nav-link" 요소들을 모두 찾음
        event_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "event-short.nav-link"))
        )

        for link in event_links:
            href_value = link.get_attribute("href")
            match = re.search(r'-\d+$', href_value)
            if match:
                event_id = match.group(0)[1:]  # '-' 문자를 제거하고 숫자만 가져옴
                print(f"event_id : {event_id}")
                event_ids.append(event_id)

        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return event_ids

def fetch_and_print_json(event_ids):
    driver = setup_driver()
    base_url = "https://api.sportbet.one/v1/events?ids="
    full_url = base_url + "_".join(event_ids)

    try:
        driver.get(full_url)
        # 페이지의 모든 텍스트 가져오기
        body_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'pre'))
        ).text

        # JSON 데이터 파싱
        data = json.loads(body_text)

        # 예쁘게 출력
        print(json.dumps(data, indent=4, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()

# 실행
event_ids = get_event_ids()
fetch_and_print_json(event_ids)
