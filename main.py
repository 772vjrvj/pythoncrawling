import datetime
import json
import random
import re
import threading
import time
import tkinter as tk
from datetime import timedelta
from tkinter import ttk, messagebox

import pandas as pd
import requests
from bs4 import BeautifulSoup

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver



# 전역 변수 추가
stop_event = threading.Event()
search_thread = None
time_val = 5

# 전역 변수 추가
stop_event = threading.Event()
search_thread = None
global_naver_cookies = {}  # 네이버 로그인 쿠키를 저장
global_server_cookies = {}  # 다른 서버 로그인 쿠키를 저장
URL = "http://vjrvj.cafe24.com"
login_server_check = ''


def fetch_search_results(query, page):
    try:
        url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Priority': 'u=0, i',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'referer': '',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, cookies=global_naver_cookies)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch search results: {e}")
    return None


def fetch_place_info(place_id):
    try:
        url = f"https://m.place.naver.com/place/{place_id}"

        headers = {
            'authority': 'm.place.naver.com',
            'method': 'GET',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        }

        response = requests.get(url, headers=headers, cookies=global_naver_cookies)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))

            if script_tag:
                json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
                if json_text:
                    data = json.loads(json_text.group(1))

                    name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")

                    prices = []
                    for key, value in data.items():
                        if key.startswith(f"Menu:{place_id}"):
                            prices.append(value)

                    facilities = []
                    for key, value in data.items():
                        if key.startswith("InformationFacilities:"):
                            facilities.append(value)

                    url = f"https://m.place.naver.com/place/{place_id}/home"

                    result = {
                        "아이디": place_id,
                        "이름": name,
                        "URL": url
                    }

                    return result

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
    except Exception as e:
        print(f"Error processing data for Place ID: {place_id}: {e}")
    return None


def fetch_link_url(place_id):
    url = "https://me2do.naver.com/common/requestJsonpV2"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "me2do.naver.com",
        "referer": f"https://pcmap.place.naver.com/{place_id}/home?from=map&fromPanelNum=1&additionalHeight=76&timestamp=202410090914",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    params = {
        "_callback": "window.spi_9197316230",
        "svcCode": "0022",
        "url": f"https://m.place.naver.com/share?id={place_id}&tabsPath=%2Fhome&appMode=detail"
    }
    link_url = ""
    try:
        # GET 요청 보내기
        response = requests.get(url, headers=headers, params=params, cookies=global_naver_cookies)

        # 응답 내용에서 콜백 함수 제거 (JSON 부분만 추출하기 위해 정규 표현식 사용)
        jsonp_data = response.text
        json_data = re.search(r'window\.spi_9197316230\((.*)\)', jsonp_data).group(1)

        # 추출된 JSON 문자열을 파이썬 딕셔너리로 변환
        data = json.loads(json_data)

        # 필요한 'url' 값 출력
        print(data['result']['url'])
        link_url = data['result']['url']
        return link_url

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return link_url


def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)


def main(query, total_queries, current_query_index):
    try:
        page = 1
        results = []
        all_ids = set()
        all_ids_list = []
        total_count = 0

        new_print(f"크롤링 시작")
        while True:
            if stop_event.is_set():
                return

            if login_server_check == 'fail':
                stop_event.set()
                messagebox.showerror("로그인 세션이 끊겼습니다.")
                return

            result = fetch_search_results(query, page)
            if not result:
                break

            place_list = result.get("result", {}).get("place", {}).get("list", [])
            ids_this_page = [place.get("id") for place in place_list if place.get("id")]

            new_print(f"페이지 : {page}, 목록 : {ids_this_page}")

            if not ids_this_page:
                break

            all_ids.update(ids_this_page)
            page += 1
            time.sleep(random.uniform(1, 2))

        if not stop_event.is_set():
            all_ids_list = list(all_ids)
            total_count = len(all_ids_list)
            new_print(f"전체 매물 수 : {total_count}")

            progress['maximum'] = total_count
            progress['value'] = 0
            set_progress(query, total_queries, current_query_index)

        for idx, place_id in enumerate(all_ids_list, start=1):
            if stop_event.is_set():
                return

            if login_server_check == 'fail':
                stop_event.set()
                messagebox.showerror("로그인 세션이 끊겼습니다.")
                return

            place_info = fetch_place_info(place_id)
            if place_info:
                place_info["공유 URL"] = fetch_link_url(place_id)
                results.append(place_info)

                new_print(f"번호 : {idx}, 이름 : {place_info['이름']}")
                time.sleep(random.uniform(1, 2))

                if not stop_event.is_set():
                    progress['value'] += 1
                    set_progress(query, total_queries, current_query_index)

        if not stop_event.is_set():
            progress['maximum'] = total_count
            progress['value'] = total_count
            set_progress(query, total_queries, current_query_index)
            query_no_spaces = query.replace(" ", "")
            save_to_excel(results, query_no_spaces)

    except Exception as e:
        print(f"Unexpected error: {e}")


def set_progress(query, total_queries, current_query_index):
    # 개별 진행률 업데이트
    progress_label.config(text=f"[{query}] 진행률: {progress['value'] / progress['maximum'] * 100:.2f}% ({progress['value']}/{progress['maximum']})")
    remaining_time = (progress['maximum'] - progress['value']) * time_val
    eta = str(timedelta(seconds=remaining_time)).split(".")[0]  # 소수점 제거
    eta_label.config(text=f"예상 소요 시간: {eta}")
    progress.update_idletasks()

    # 전체 진행률 업데이트
    overall_progress_percentage = ((current_query_index + progress['value'] / progress['maximum']) / total_queries) * 100
    overall_progress_label.config(text=f"전체 진행률: {overall_progress_percentage:.2f}%")
    overall_progress['value'] = overall_progress_percentage
    overall_progress.update_idletasks()


def save_to_excel(results, query_no_spaces, mode='w'):
    new_print(f"엑셀 저장 시작...")
    blogs = []
    for result in results:
        blog = {}
        blog["아이디"] = result["아이디"]
        blog["이름"] = result["이름"]
        blog["정보 URL"] = result["URL"]
        blog["공유 URL"] = result["공유 URL"]
        blogs.append(blog)

    # 현재 날짜와 시간 구하기
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 파일 이름에 현재 날짜와 시간 추가, 파일 이름을 안전하게 처리
    file_name = sanitize_filename(f'{query_no_spaces}_{timestamp}.xlsx')
    try:
        if mode == 'a':
            existing_df = pd.read_excel(file_name)
            new_df = pd.DataFrame(blogs)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(blogs)
        df.to_excel(file_name, index=False)
    except FileNotFoundError:
        df = pd.DataFrame(blogs)
        df.to_excel(file_name, index=False)

    new_print(f"엑셀 저장 {file_name}")
    # 메시지박스 표시


def sanitize_filename(name):
    # 파일 이름에 사용할 수 없는 문자들을 제거합니다.
    return re.sub(r'[\\/*?:"<>|]', "", name)


def start_app():
    global root, search_entry, search_button, log_text_widget, progress, progress_label, eta_label, overall_progress_label, overall_progress

    root = tk.Tk()
    root.title("네이버 블로그 프로그램")
    root.geometry("700x750")  # 크기 조정

    font_large = ('Helvetica', 10)  # 폰트 크기

    # 옵션 프레임
    option_frame = tk.Frame(root)
    option_frame.pack(fill=tk.X, padx=10, pady=10)

    # 검색어 입력 프레임
    search_frame = tk.Frame(root)
    search_frame.pack(pady=20)

    # 검색어 레이블
    search_label = tk.Label(search_frame, text="검색어:", font=font_large)
    search_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

    # 검색어 입력 필드
    search_entry = tk.Entry(search_frame, font=font_large, width=25)
    search_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    # 검색 버튼
    search_button = tk.Button(search_frame, text="검색", font=font_large, bg="lightgreen", command=on_search)
    search_button.grid(row=0, column=2, padx=5, pady=5)

    # 안내 문구
    guide_label = tk.Label(search_frame, text="* 콤마(,)로 구분하여 검색어를 작성해주세요 *", font=font_large, fg="red")
    guide_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    # 검색 프레임의 열 비율 설정
    search_frame.columnconfigure(1, weight=1)

    # 로그 화면
    log_label = tk.Label(root, text="로그 화면", font=font_large)
    log_label.pack(fill=tk.X, padx=10)

    log_frame = tk.Frame(root)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    x_scrollbar = tk.Scrollbar(log_frame, orient=tk.HORIZONTAL)
    x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    y_scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL)
    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    log_text_widget = tk.Text(log_frame, wrap=tk.NONE, height=10, font=font_large, xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
    log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    x_scrollbar.config(command=log_text_widget.xview)
    y_scrollbar.config(command=log_text_widget.yview)

    # 진행률
    progress_frame = tk.Frame(root)
    progress_frame.pack(fill=tk.X, padx=10, pady=10)

    # 개별 진행률 표시
    progress_label = tk.Label(progress_frame, text="진행률: 0%", font=font_large)
    progress_label.pack(side=tk.TOP, padx=5)

    # 예상 소요 시간
    eta_label = tk.Label(progress_frame, text="예상 소요 시간: 00:00:00", font=font_large)
    eta_label.pack(side=tk.TOP, padx=5)


    # 개별 진행률 게이지 바 (전체 진행률 아래로 이동)
    progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    progress.pack(fill=tk.X, padx=10, pady=(0, 10), expand=True)

    # 전체 진행률 표시 (위로 이동)
    overall_progress_label = tk.Label(progress_frame, text="전체 진행률: 0%", font=font_large)
    overall_progress_label.pack(side=tk.TOP, padx=5)

    # 전체 진행률 게이지 바
    overall_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    overall_progress.pack(fill=tk.X, padx=10, pady=(0, 10), expand=True)

    root.mainloop()


def run_main(querys):
    try:
        query_list = [q.strip() for q in querys.split(",")]
        total_queries = len(query_list)
        for idx, query in enumerate(query_list):
            if stop_event.is_set():
                break

            if login_server_check == 'fail':
                stop_event.set()
                messagebox.showerror("로그인 세션이 끊겼습니다.")
                break

            new_print(f"검색어: {query} 크롤링 시작", "INFO")
            progress_label.config(text=f"[{query}] 진행률: 0%")
            main(query, total_queries, idx)

        if not stop_event.is_set():
            messagebox.showwarning("경고", "크롤링이 완료되었습니다.")
            search_button.config(bg="lightgreen", fg="black", text="검색")

    except Exception as e:
        new_print(f"Unexpected error in thread: {e}", "ERROR")


def on_search():
    global search_thread, stop_event
    query = search_entry.get().strip()
    if query:
        if search_thread and search_thread.is_alive():
            # 중지 버튼이 클릭되면 작업 중지
            new_print("크롤링 중지")
            stop_event.set()  # 이벤트 설정
            search_button.config(bg="lightgreen", fg="black", text="검색")

            # 진행률 게이지바 초기화
            progress['value'] = 0
            overall_progress['value'] = 0
            progress_label.config(text="진행률: 0%")
            overall_progress_label.config(text="전체 진행률: 0%")
            eta_label.config(text="예상 소요 시간: 00:00:00")
            messagebox.showwarning("경고", "크롤링이 중지되었습니다.")
        else:
            # 시작 버튼 클릭 시 모든 진행률 초기화
            stop_event.clear()  # 이벤트 초기화
            log_text_widget.delete('1.0', tk.END)  # 로그 초기화
            progress['value'] = 0  # 개별 진행률 초기화
            overall_progress['value'] = 0  # 전체 진행률 초기화
            progress_label.config(text="진행률: 0%")
            overall_progress_label.config(text="전체 진행률: 0%")
            eta_label.config(text="예상 소요 시간: 00:00:00")
            search_button.config(bg="red", fg="white", text="중지")
            search_thread = threading.Thread(target=run_main, args=(query,))
            search_thread.start()
    else:
        messagebox.showwarning("경고", "검색어를 입력하세요.")

# 여기에 main 함수와 기타 필요한 함수들을 포함시키세요.


# 셀레니움 세팅
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=500,650")
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

    # 창 크기 설정 (예: 너비 1080, 높이 750)
    driver.set_window_size(500, 650)

    # 창 위치 설정 (왼쪽 끝으로 이동)
    driver.set_window_position(0, 0)


    return driver


# 네이버 로그인 창 함수
def naver_login_window():
    def on_naver_login():
        global global_naver_cookies  # 네이버 쿠키를 저장하기 위해 전역 변수 사용

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
                messagebox.showwarning("경고", "로그인 실패: 300초 내에 로그인하지 않았습니다.")
                break

            cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

            # 쿠키 중 NID_AUT 또는 NID_SES 쿠키가 있는지 확인 (네이버 로그인 성공 시 생성되는 쿠키)
            if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                logged_in = True
                global_naver_cookies = cookies  # 네이버 로그인 성공 시 쿠키 저장
                messagebox.showinfo("로그인 성공", "정상 로그인 되었습니다.")

        driver.quit()  # 작업이 끝난 후 드라이버 종료
        naver_login_root.destroy()
        start_app()

    # 네이버 로그인 창 생성
    naver_login_root = tk.Tk()
    naver_login_root.title("네이버 로그인")

    # 창 크기 설정
    naver_login_root.geometry("300x120")  # 창 크기
    screen_width = naver_login_root.winfo_screenwidth()  # 화면 너비
    screen_height = naver_login_root.winfo_screenheight()  # 화면 높이
    window_width = 300  # 창 너비
    window_height = 120  # 창 높이

    # 창을 화면의 가운데로 배치
    position_top = int(screen_height / 2 - window_height / 2)
    position_left = int(screen_width / 2 - window_width / 2)
    naver_login_root.geometry(f'{window_width}x{window_height}+{position_left}+{position_top}')

    # 네이버 로그인 버튼
    naver_login_button = tk.Button(naver_login_root, text="네이버 로그인", command=on_naver_login)
    naver_login_button.pack(pady=30)

    naver_login_root.mainloop()


# 서버 로그인 함수 (네이버와 다른 서버 구분)
def login_to_server(username, password, session):
    global global_server_cookies
    url = f"{URL}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # JSON 형식으로 서버에 POST 요청으로 로그인 시도
        response = session.post(url, json=payload, headers=headers)  # 헤더 추가

        # 요청이 성공했는지 확인
        if response.status_code == 200:
            # 세션 관리로 쿠키는 자동 처리
            global_server_cookies = session.cookies.get_dict()
            return True
        else:
            return False
    except Exception as e:
        return False


# 세션체크
def check_session(session, server_type="server"):
    global login_server_check
    cookies = global_server_cookies if server_type == "server" else global_naver_cookies
    url = f"{URL}/session/check-me"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # /check-me 엔드포인트를 호출하여 세션 상태 확인
    response = session.get(url, headers=headers, cookies=cookies)

    if response.status_code == 200:
        login_server_check = response.text


# 세션 실시간 요청
def check_session_periodically(session, server_type="server"):
    while True:
        if global_naver_cookies:
            check_session(session, server_type)  # 세션 상태를 체크
        time.sleep(60)  # 2분 대기


# 비밀변경
def change_password(session, username, current_password, new_password):
    url = f"{URL}/auth/change-password"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "id": username,
        "currentPassword": current_password,
        "newPassword": new_password
    }

    try:
        # PUT 요청을 사용하여 비밀번호 변경
        response = session.put(url, params=payload, headers=headers)

        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False


# 취소 버튼 클릭 이벤트
def return_to_login():
    change_pw_root.destroy()
    login_window()


# 비밀번호 변경 버튼 클릭 이벤트
def on_change_password():
    user_id = id_entry_cp.get()
    current_pw = current_pw_entry.get()
    new_pw = new_pw_entry.get()

    # 여기에 비밀번호 변경 API 호출 로직 추가
    session = requests.Session()
    result = change_password(session, user_id, current_pw, new_pw)

    if result:
        messagebox.showinfo("비밀번호 변경", "비밀번호가 변경되었습니다.")
        change_pw_root.destroy()
        login_window()
    else:
        messagebox.showerror("비밀번호 변경", "비밀번호 변경에 실패하였습니다.")


# 비밀번호 변경 창 열기
def open_change_password_window():
    login_root.destroy()  # 로그인 창 닫기
    change_password_window()  # 비밀번호 변경 창 열기


# 비밀번호 변경 창
def change_password_window():
    global change_pw_root, id_entry_cp, current_pw_entry, new_pw_entry

    change_pw_root = tk.Tk()
    change_pw_root.title("비밀번호 변경")

    # 창 크기 설정
    change_pw_root.geometry("300x250")
    screen_width = change_pw_root.winfo_screenwidth()
    screen_height = change_pw_root.winfo_screenheight()
    window_width = 300
    window_height = 270

    # 창을 화면의 가운데로 배치
    position_top = int(screen_height / 2 - window_height / 2)
    position_left = int(screen_width / 2 - window_width / 2)
    change_pw_root.geometry(f'{window_width}x{window_height}+{position_left}+{position_top}')

    # 창 닫기 이벤트 처리
    change_pw_root.protocol("WM_DELETE_WINDOW", return_to_login)

    # ID 입력
    id_label_cp = tk.Label(change_pw_root, text="ID:")
    id_label_cp.pack(pady=10)
    id_entry_cp = tk.Entry(change_pw_root, width=20)
    id_entry_cp.pack(pady=5)

    # 현재 비밀번호 입력
    current_pw_label = tk.Label(change_pw_root, text="현재 비밀번호:")
    current_pw_label.pack(pady=10)
    current_pw_entry = tk.Entry(change_pw_root, show="*", width=20)
    current_pw_entry.pack(pady=5)

    # 변경할 비밀번호 입력
    new_pw_label = tk.Label(change_pw_root, text="변경 비밀번호:")
    new_pw_label.pack(pady=10)
    new_pw_entry = tk.Entry(change_pw_root, show="*", width=20)
    new_pw_entry.pack(pady=5)

    # 버튼 프레임
    button_frame = tk.Frame(change_pw_root)
    button_frame.pack(pady=10)

    # 비밀번호 변경 버튼
    change_pw_button = tk.Button(button_frame, text="비밀번호 변경", command=on_change_password)
    change_pw_button.grid(row=0, column=0, padx=5)

    # 취소 버튼
    cancel_button = tk.Button(button_frame, text="취소", command=return_to_login)
    cancel_button.grid(row=0, column=1, padx=5)

    change_pw_root.mainloop()


# 로그인
def on_login():
    user_id = id_entry.get()
    user_pw = pw_entry.get()

    # 서버 세션 관리
    session = requests.Session()
    if login_to_server(user_id, user_pw, session):
        messagebox.showinfo("로그인 성공", "로그인 성공!")
        login_root.destroy()
        # 로그인 성공 후, 세션 상태를 주기적으로 체크하는 쓰레드 시작
        session_thread = threading.Thread(target=check_session_periodically, args=(session, "server"), daemon=True)
        session_thread.start()

        # 로그인 후 네이버 로그인 창을 띄운다
        naver_login_window()
    else:
        messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 틀렸습니다.")




# 로그인 창
def login_window():
    global login_root, id_entry, pw_entry

    login_root = tk.Tk()
    login_root.title("로그인")

    # 창 크기 설정
    login_root.geometry("300x200")
    screen_width = login_root.winfo_screenwidth()
    screen_height = login_root.winfo_screenheight()
    window_width = 300
    window_height = 200

    # 창을 화면의 가운데로 배치
    position_top = int(screen_height / 2 - window_height / 2)
    position_left = int(screen_width / 2 - window_width / 2)
    login_root.geometry(f'{window_width}x{window_height}+{position_left}+{position_top}')

    # ID 입력
    id_label = tk.Label(login_root, text="ID:")
    id_label.pack(pady=10)
    id_entry = tk.Entry(login_root, width=20)
    id_entry.pack(pady=5)

    # PW 입력
    pw_label = tk.Label(login_root, text="PW:")
    pw_label.pack(pady=10)
    pw_entry = tk.Entry(login_root, show="*", width=20)
    pw_entry.pack(pady=5)

    # 버튼 프레임
    button_frame = tk.Frame(login_root)
    button_frame.pack(pady=10)

    # 로그인 버튼
    login_button = tk.Button(button_frame, text="로그인", command=on_login)
    login_button.grid(row=0, column=0, padx=5)

    # 비밀번호 변경 버튼
    change_pw_button = tk.Button(button_frame, text="비밀번호 변경", command=open_change_password_window)
    change_pw_button.grid(row=0, column=1, padx=5)

    login_root.mainloop()



if __name__ == "__main__":
    login_window()  # 로그인 창 호출
    # start_app()
