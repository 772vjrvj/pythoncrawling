import requests
from bs4 import BeautifulSoup

from requests.exceptions import RequestException


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
            print("로그인 요청 성공!")
            for cookie in sess.cookies:
                # 수정된 부분: cookie.name과 cookie.value 사용
                sess.cookies.set(cookie.name, cookie.value)
                print(f"{cookie.name}: {cookie.value}")
            return sess
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

if __name__ == '__main__':

    username = "kkckkc"
    password = "k@4358220"

    if username and password:
        main(username, password)
    else:
        print("아이디와 패스워드를 확인하세요.")


