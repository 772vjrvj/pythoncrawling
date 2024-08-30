from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import pandas as pd
import re
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import requests

# 전역 변수 설정
global_cookies = {}
cafe_id = ""
menu_list = []
menuid = ""
extracted_data = []

# 셀레니움 드라이버 세팅
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

# 네이버 로그인
def naver_login():
    global global_cookies  # 전역 변수를 사용하기 위해 global 키워드 사용

    driver = setup_driver()
    driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

    # 로그인 여부를 주기적으로 체크
    logged_in = False
    max_wait_time = 300  # 최대 대기 시간 (초)
    start_time = time.time()

    while not logged_in:
        # 1초 간격으로 쿠키 확인
        time.sleep(1)
        elapsed_time = time.time() - start_time

        # 최대 대기 시간 초과 시 while 루프 종료
        if elapsed_time > max_wait_time:
            print("경고 로그인 실패: 300초 내에 로그인하지 않았습니다.")
            break

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

        # 쿠키 중 NID_AUT 또는 NID_SES 쿠키가 있는지 확인 (네이버 로그인 성공 시 생성되는 쿠키)
        if 'NID_AUT' in cookies and 'NID_SES' in cookies:
            logged_in = True
            global_cookies = cookies  # 로그인 성공 시 전역 변수에 쿠키 저장
            print("로그인 성공 정상 로그인 되었습니다.")

    driver.quit()  # 작업이 끝난 후 드라이버 종료

# 로그인 초기화
def reset_login():
    global global_cookies
    global_cookies = {}
    print("로그인 정보가 초기화되었습니다.")

# 카페 ID 가져오기
def get_cafe_id(cafe_url):
    global cafe_id
    # 카페 URL에서 cluburl 값 추출
    club_url = cafe_url.split('/')[-1]

    # API 요청 URL 생성
    api_url = f"https://apis.naver.com/cafe-web/cafe2/CafeGateInfo.json?cluburl={club_url}"

    # API 요청
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": "; ".join([f"{name}={value}" for name, value in global_cookies.items()])
    }

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()

        # cafeId 추출
        cafe_id = data.get("message", {}).get("result", {}).get("cafeInfoView", {}).get("cafeId", None)

        if cafe_id:
            print(f"카페 ID: {cafe_id}")
        else:
            print(f"cafeId를 찾을 수 없습니다.")
    else:
        print(f"API 요청 실패: {response.status_code}")

# 메인 함수
def main():
    naver_login()  # 네이버 로그인 실행

    if global_cookies:  # 로그인 성공 시
        cafe_url = input("카페 URL을 입력하세요: ")
        get_cafe_id(cafe_url)  # 카페 ID 가져오기
    else:
        print("로그인에 실패했습니다.")

if __name__ == "__main__":
    main()
