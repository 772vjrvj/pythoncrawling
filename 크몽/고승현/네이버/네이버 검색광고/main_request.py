import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import base64
from datetime import datetime, timedelta, timezone

global_cookies = ""
bearer_token = ""

def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")

    # 사용자 에이전트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 탐지 방지 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 크롬 드라이버 실행 및 자동화 방지 우회
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver


def main():

    # 기본 URL과 동적 키워드 설정
    base_url = "https://manage.searchad.naver.com/keywordstool"
    keyword = "무선마우스"
    params = {
        "format": "json",
        "hintKeywords": keyword,
        "siteId": "",
        "month": "",
        "biztpId": "",
        "event": "",
        "includeHintKeywords": "0",
        "showDetail": "1",
        "keyword": "",
    }

    # 헤더 설정
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": bearer_token,
        "priority": "u=1, i",
        "referer": "https://manage.searchad.naver.com/customers/3216661/tool/keyword-planner",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-accept-language": "ko",
    }

    # GET 요청 보내기
    response = requests.get(base_url, headers=headers, params=params, cookies=global_cookies)


    # 응답 처리
    if response.status_code == 200:
        try:
            data = response.json()
            keyword_list = data.get("keywordList", [])
            print("Keyword List:")
            for kw in keyword_list:
                if kw['relKeyword'] == keyword:
                    return kw
        except ValueError:
            print("응답이 JSON 형식이 아닙니다.")
    else:
        print(f"요청 실패: 상태 코드 {response.status_code}")


def get_auth():
    # URL 설정
    url = "https://atower.searchad.naver.com/auth/enigma?_d=l6z8"

    # 헤더 설정
    headers = {
        "origin": "https://manage.searchad.naver.com",
        "priority": "u=1, i",
        "referer": "https://manage.searchad.naver.com/customers/3216661/tool/keyword-planner",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "authority": "atower.searchad.naver.com",
        "method": "GET",
        "path": "/auth/enigma?_d=l6z8",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache"
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers, cookies=global_cookies)

    # 응답 처리
    if response.status_code == 200:
        try:
            data = response.json()
            token = data.get("token")
            refresh_token = data.get("refreshToken")
            print(f"Token: {token}")
            print(f"Refresh Token: {refresh_token}")
            return token
        except ValueError:
            print("응답이 JSON 형식이 아닙니다.")
            return ''
    else:
        print(f"요청 실패: 상태 코드 {response.status_code}")
        return ''

def naver_login():
    global global_cookies, bearer_token
    try:
        driver = setup_driver()
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))

        logged_in = False
        max_wait_time = 300
        start_time = time.time()

        while not logged_in:
            time.sleep(1)
            elapsed_time = time.time() - start_time

            if elapsed_time > max_wait_time:
                print("경고", "로그인 실패: 300초 내에 로그인하지 않았습니다.")
                break

            cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
            if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                global_cookies = cookies
                logged_in = True
                break

        # 로그인 후 관리 페이지로 이동
        if logged_in:

            bearer_token = get_auth()
            print(f'bearer_token : {bearer_token}')

            # JWT Payload에서 exp 확인
            payload = decode_jwt_payload(bearer_token)
            if "exp" in payload:
                exp_timestamp = payload["exp"]

                # UTC 시간대가 있는 datetime 객체 생성
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)  # UTC 시간
                print(f"만료 시간 (UTC): {exp_datetime}")

                # 한국 시간(KST, UTC+9)으로 변환
                kst_datetime = exp_datetime.astimezone(timezone(timedelta(hours=9)))
                print(f"만료 시간 (KST): {kst_datetime}")

                # 현재 시간 (UTC와 KST)
                current_utc = datetime.now(timezone.utc)  # 현재 UTC 시간
                current_kst = current_utc.astimezone(timezone(timedelta(hours=9)))  # 현재 KST 시간
                print(f"현재 시간 (UTC): {current_utc}")
                print(f"현재 시간 (KST): {current_kst}")

                # 현재 시간과 만료 시간의 차이 계산
                remaining_time = exp_datetime - current_utc  # 남은 시간 (UTC 기준)
                if remaining_time.total_seconds() > 0:
                    print(f"토큰의 유효 시간: {remaining_time}")
                else:
                    print("토큰이 만료되었습니다.")
            else:
                print("JWT 토큰에 만료 시간(exp)이 포함되어 있지 않습니다.")

    except Exception as e:
        print("경고", f"로그인 중 오류가 발생했습니다.{e}")
    finally:
        driver.quit()

def decode_jwt_payload(token):
    payload = token.split(".")[1]
    # Base64 디코딩 (패딩 문제 해결 포함)
    padded_payload = payload + "=" * (-len(payload) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded_payload)
    decoded_payload = json.loads(decoded_bytes)
    return decoded_payload


if __name__ == "__main__":
    naver_login()
    input("아무 키나 입력하세요...")
    kw = main()
    print(f'PC 검색수 {kw['monthlyPcQcCnt']}') # PC 검색
    print(f'모바일 검색수 {kw['monthlyMobileQcCnt']}') # 모바일 검색