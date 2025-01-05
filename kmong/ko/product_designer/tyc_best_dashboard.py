import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

from requests.exceptions import RequestException

def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    ###### 자동 제어 감지 방지 #####
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    ##### 화면 최대 #####
    chrome_options.add_argument("--start-maximized")

    ##### 화면이 안보이게 함 #####
    chrome_options.add_argument("--headless")

    ##### 자동 경고 제거 #####
    chrome_options.add_experimental_option('useAutomationExtension', False)

    ##### 로깅 비활성화 #####
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    ##### 자동화 탐지 방지 설정 #####
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    ##### 자동으로 최신 크롬 드라이버를 다운로드하여 설치하는 역할 #####
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    ##### CDP 명령으로 자동화 감지 방지 #####
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver


def set_login_selenium(username, password):

    # 셀레니움 드라이버 초기화
    driver = setup_driver()

    url = "https://tyc.best/dashboard/login.asp"

    # 웹페이지 요청
    driver.get(url)

    time.sleep(3)

    # 아이디 입력
    memb_id = driver.find_element(By.ID, "MEMB_ID")
    memb_id.clear()  # 기존 값 지우기 (필요 시)
    memb_id.send_keys(username)  # 원하는 아이디 입력

    # 패스워드 입력
    passwd = driver.find_element(By.ID, "passwd")
    passwd.clear()  # 기존 값 지우기 (필요 시)
    passwd.send_keys(password)  # 원하는 패스워드 입력

    # 엔터 키 입력 (Enter_Check 함수 실행)
    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-block.w-100")
    login_button.click()

    time.sleep(3)

    sess = requests.Session()

    cookies = driver.get_cookies()
    for cookie in cookies:
        sess.cookies.set(cookie['name'], cookie['value'])

    version = driver.capabilities["browserVersion"]
    driver.quit()
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}"
    }
    sess.headers = headers
    return sess




def set_login(username, password):
    login_url = "https://tyc.best/include/login_chk.asp"  # 로그인 처리 URL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # 로그인 데이터
    login_data = {
        "MEMB_ID": username,  # 아이디
        "PASS2": password    # 비밀번호
    }

    # 세션 생성
    sess = requests.Session()
    try:
        # 로그인 요청
        response = sess.post(login_url, data=login_data, headers=headers)

        # 로그인 요청 결과 확인
        if response.ok:

            for cookie in sess.cookies:
                sess.cookies.set(cookie['name'], cookie['value'])
                return sess
            else:
                print("대시보드 접근 실패!")
                return None
        else:
            print("로그인 요청 실패!")
            print(response.status_code, response.text)
            return None
    except Exception as e:
        print(f"오류 발생: {e}")
        return None




def get_request(sess, url):
    try:
        # GET 요청 보내기
        response = sess.get(url, timeout=10)  # 타임아웃 설정

        # 상태 코드 확인
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            print(f"Unexpected status code: {response.status_code}")
            return None

    except RequestException as req_error:
        print(f"Request failed: {req_error}")
        return None



def main_reward(sess):

    url = "https://tyc.best/dashboard/index.asp"

    try:
        # HTML 가져오기
        soup = get_request(sess, url)

        # soup이 None인 경우 처리
        if not soup:
            print("Failed to fetch or parse the HTML content.")
            return []

        # 최종 데이터 저장할 배열
        data_list = []

        # 첫 번째 div 탐색
        main_divs = soup.find_all("div", class_="col-xxl-auto col-xl-3 col-sm-6 box-col-6")
        for main_div in main_divs:
            try:
                # 두 번째 div 탐색
                widget_contents = main_div.find_all("div", class_="widget-content")
                for widget_content in widget_contents:
                    # 세 번째 div 탐색
                    inner_divs = widget_content.find_all("div")
                    if len(inner_divs) >= 2:
                        h4_tag = inner_divs[2].find("h4")
                        span_tag = inner_divs[2].find("span", class_="f-light")
                        if h4_tag and span_tag:
                            # 데이터 저장
                            data = {
                                "값": h4_tag.text.strip(),
                                "이름": span_tag.text.strip()
                            }
                            data_list.append(data)
            except Exception as e:
                print(f"Error processing a widget content: {e}")

        return data_list

    except Exception as e:
        print(f"An error occurred in main_reward: {e}")
        return []



def mining_reward(sess):
    try:
        # GET 요청 보내기
        url = "https://tyc.best/dashboard/depth/bonus/bonus_daylist.asp"
        soup = get_request(sess, url)

        data_list = []

        # soup이 None인 경우 처리
        if soup:
            table = soup.find("table", class_="basic_table")
            if table:
                headers = [th.text.strip() for th in table.find("thead").find_all("th")]
                tbody = table.find("tbody")
                if tbody and headers:
                    rows = tbody.find_all("tr")
                    if not (rows and len(rows) == 1 and rows[0].find("td", colspan="7") and "No articles.." in rows[0].text):
                        for row in rows:
                            cells = [cell.text.strip() for cell in row.find_all("td")]
                            if len(cells) == len(headers):  # 헤더와 열 개수 일치 확인
                                data_list.append(dict(zip(headers, cells)))
        # 결과 반환
        return data_list

    except Exception as e:
        print(f"An unexpected error occurred in mining_reward: {e}")
        return []


def mining_reward_test_html():
    try:
        # 실행 경로의 index.html 파일 읽기
        file_path = "index.html"
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(html_content, "html.parser")

        data_list = []

        # soup이 None인 경우 처리
        if soup:
            table = soup.find("table", class_="basic_table")
            if table:
                headers = [th.text.strip() for th in table.find("thead").find_all("th")]
                tbody = table.find("tbody")
                if tbody and headers:
                    rows = tbody.find_all("tr")
                    if not (rows and len(rows) == 1 and rows[0].find("td", colspan="7") and "No articles.." in rows[0].text):
                        for row in rows:
                            cells = [cell.text.strip() for cell in row.find_all("td")]
                            if len(cells) == len(headers):  # 헤더와 열 개수 일치 확인
                                data_list.append(dict(zip(headers, cells)))

        # 결과 반환
        return data_list

    except FileNotFoundError:
        print("Error: 'index.html' file not found.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in mining_reward: {e}")
        return []


def main(username, password):

    sess = set_login(username, password)
    main_reward_list = main_reward(sess)
    print(f'main_reward_list : {main_reward_list}')
    mining_reward_list = mining_reward(sess)
    print(f'mining_reward_list : {mining_reward_list}')
    # mining_reward_test_list = mining_reward_test_html()
    # print(f'mining_reward_test_list : {mining_reward_test_list}')

if __name__ == '__main__':

    username = "kkckkc"
    password = "k@4358220"

    if username and password:
        main(username, password)
    else:
        print("아이디와 패스워드를 확인하세요.")


