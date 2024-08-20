import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import pandas as pd

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

def fetch_article_data(cookies):
    url = "https://apis.naver.com/cafe-web/cafe-articleapi/v2.1/cafes/15092639/articles/7022968?fromList=true&menuId=493&tc=cafe_article_list&useCafeId=true&buid=1baaf70c-ffec-4309-86b0-b849bcbdc06e"

    headers = {
        "authority": "apis.naver.com",
        "method": "GET",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://m.cafe.naver.com",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "x-cafe-product": "mweb"
    }

    # 쿠키를 헤더에 추가
    headers['cookie'] = "; ".join([f"{name}={value}" for name, value in cookies.items()])

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 요청이 실패할 경우 예외를 발생시킴
        data = response.json()
        # JSON 데이터를 반환
        print(json.dumps(data, indent=4, ensure_ascii=False))
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def save_data(data, format_type, download_path):
    if format_type == 1:  # 엑셀
        df = pd.DataFrame([data])
        file_path = os.path.join(download_path, "result.xlsx")
        df.to_excel(file_path, index=False)
        print(f"데이터가 엑셀 파일로 저장되었습니다: {file_path}")
    elif format_type == 2:  # CSV
        df = pd.DataFrame([data])
        file_path = os.path.join(download_path, "result.csv")
        df.to_csv(file_path, index=False)
        print(f"데이터가 CSV 파일로 저장되었습니다: {file_path}")
    elif format_type == 3:  # 텍스트
        file_path = os.path.join(download_path, "result.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4, ensure_ascii=False))
        print(f"데이터가 텍스트 파일로 저장되었습니다: {file_path}")

def main():
    print("로그인 진행하시겠습니까? 엔터를 누르면 브라우저가 열립니다...")

    # Selenium WebDriver 설정
    driver = setup_driver()
    driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

    # 로그인 여부를 주기적으로 체크
    logged_in = False
    while not logged_in:
        # 1초 간격으로 쿠키 확인
        time.sleep(1)
        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

        # 쿠키 중 NID_AUT 또는 NID_SES 쿠키가 있는지 확인 (네이버 로그인 성공 시 생성되는 쿠키)
        if 'NID_AUT' in cookies and 'NID_SES' in cookies:
            logged_in = True
            print("로그인 성공, 다음 작업을 진행합니다...")

    # 로그인 후 작업 진행
    print(f"cookies : {json.dumps(cookies, indent=4, ensure_ascii=False)}")

    # requests를 이용해 API 호출, 로그인 후 받은 쿠키를 전달
    data = fetch_article_data(cookies)

    if data:
        # 사용자 홈 디렉토리의 다운로드 폴더 경로 가져오기
        home_directory = os.path.expanduser("~")
        download_path = os.path.join(home_directory, "Downloads")

        print(f"download_path : {download_path}")

        # 저장 방식을 선택 - 유효한 입력이 있을 때까지 반복
        while True:
            try:
                format_type = int(input("저장 방식을 선택하세요 (1: 엑셀, 2: CSV, 3: 텍스트): "))
                if format_type in [1, 2, 3]:
                    break
                else:
                    print("1, 2, 3 중 하나를 선택하세요.")
            except ValueError:
                print("유효한 숫자를 입력하세요.")

        # 데이터 저장
        save_data(data, format_type, download_path)

    # 종료 전 대기
    input("종료 대기...")  # 추가 작업을 위해 대기

    # 브라우저 종료
    driver.quit()

if __name__ == "__main__":
    main()