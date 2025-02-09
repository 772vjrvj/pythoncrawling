import json
import threading
import time
from tkinter import messagebox
import urllib.parse

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# 전역 변수
global_naver_keyword_cookies = None
driver = None
bearer_token = ""
refresh_token = ""
name= "keyword"
stop_thread = threading.Event()
URL = "https://주식회사비전.com/open/update-cookie"

# 드라이버 세팅
def setup_driver():
    global driver
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # 화면 없이 실행 (필요에 따라 제거 가능)

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    driver.set_window_position(0, 0)
    driver.set_window_size(500, 800)
    return driver

# 쿠키 업데이트 함수
def updatePlaceCookie(name, cookies_dict, refresh_token, bearer_token):
    if not cookies_dict:
        print("경고: 쿠키가 없습니다.")
        return

    # 필요한 쿠키 키 목록
    required_keys = {"NNB", "NID_AUT", "NID_SES"}

    # 기존 쿠키 딕셔너리에서 필요한 쿠키만 필터링
    filtered_cookies = {key: value for key, value in cookies_dict.items() if key in required_keys}

    # 쿠키 문자열 생성
    cookie_string = '; '.join([f"{key}={urllib.parse.quote(str(value))}" for key, value in filtered_cookies.items()])
    print(f"쿠키 길이: {len(cookie_string)} bytes")
    data = {
        "name": name,
        "cookie": cookie_string,
        "refreshToken": refresh_token,
        "bearerToken": bearer_token
    }

    try:
        response = requests.post(URL, json=data)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        print("서버 응답:", response.text)  # 응답 본문 출력
    except requests.exceptions.RequestException as e:
        print("쿠키 업데이트 실패:", e)
    except json.JSONDecodeError:
        print("JSON 파싱 오류: 서버 응답이 올바른 JSON 형식이 아닙니다.", response.text)

# 새로고침 함수
def reload():
    global driver, global_naver_keyword_cookies, bearer_token, refresh_token

    if driver is None:
        print("경고: driver가 없습니다.")
        return

    driver.refresh()
    time.sleep(3)

    tokens_json = driver.execute_script("return window.localStorage.getItem('tokens');")
    global_naver_keyword_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

    if not tokens_json:
        print("경고: tokens 값이 없습니다.")
        return

    try:
        tokens = json.loads(tokens_json)
    except json.JSONDecodeError:
        print("경고: tokens JSON 디코딩 실패")
        return

    keys = list(tokens.keys())

    if keys:
        account_data = tokens[keys[0]]
        bearer_token = f'Bearer {account_data.get("bearer")}'
        refresh_token = account_data.get("refreshToken")
        name = 'keyword'
        updatePlaceCookie(name, global_naver_keyword_cookies, refresh_token, bearer_token)
    else:
        print("경고: 지정된 키가 없습니다.")

        # 주기적인 쿠키 업데이트

def periodic_cookie_update():
    while True:
        try:
            reload()
        except Exception as e:
            print(f"토큰 업데이트 중 오류 발생: {e}")
        time.sleep(600)  # 5분 대기

# 네이버 로그인
def naver_login():
    global driver, bearer_token, refresh_token, global_naver_keyword_cookies, name

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
                messagebox.showwarning("경고", "로그인 실패: 300초 내에 로그인하지 않았습니다.")
                break

            cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
            if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                logged_in = True
                break

        if logged_in:
            driver.get("https://manage.searchad.naver.com/customers/1689588/tool/keyword-planner")
            time.sleep(3)

            tokens_json = driver.execute_script("return window.localStorage.getItem('tokens');")
            global_naver_keyword_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

            if not tokens_json:
                print("경고: 값이 없습니다.")
                return

            try:
                tokens = json.loads(tokens_json)
            except json.JSONDecodeError:
                print("경고: tokens JSON 디코딩 실패")
                return

            keys = list(tokens.keys())

            if keys:
                account_data = tokens[keys[0]]
                bearer_token = f'Bearer {account_data.get("bearer")}'
                refresh_token = account_data.get("refreshToken")
                updatePlaceCookie(name, global_naver_keyword_cookies, refresh_token, bearer_token)
                time.sleep(10)
                periodic_cookie_update()  # 스레드 시작 전에 한 번 실행
            else:
                print("경고: 지정된 키가 없습니다.")

    except Exception as e:
        print("경고", f"로그인 중 오류가 발생했습니다: {e}")

# 실행
if __name__ == "__main__":
    naver_login()
