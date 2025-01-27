from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import ttk, filedialog, font, messagebox
import tkinter as tk
import pandas as pd
import threading
import requests
import random
import ctypes
import time
import json
import math
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager



# region
# ══════════════════════════════════════════════════════
# 전역 변수
# ══════════════════════════════════════════════════════

# 엑셀 업로드 후 url 리스트
id_list = []

# 추출값 페센트 리스트
extracted_data_list = []  # 모든 데이터 저장용

# 일시 중지
stop_flag = False

# 네이버 로그인 쿠키
global_cookies = ''

# 완료후 깜빡임 상태
flashing = True

# 엑셀 경로
filepath = None

# ══════════════════════════════════════════════════════
# endregion



# region
# ══════════════════════════════════════════════════════
# 셀레니움
# ══════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════
# endregion



# region
# ══════════════════════════════════════════════════════
# 엑셀 관련
# ══════════════════════════════════════════════════════

# 드래그 엑셀 파일로 이름 업로드
def on_drop(event):
    global id_list, filepath
    filepath = event.data.strip('{}')
    id_list = read_excel_file(filepath)
    update_log(id_list)
    # 리스트 상태 확인 및 버튼 활성화
    check_list_and_toggle_button(id_list)

# 윈도우 엑셀 파일로 이름 업로드
def browse_file():
    global id_list, filepath
    filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if filepath:
        id_list = read_excel_file(filepath)
        update_log(id_list)
        # 리스트 상태 확인 및 버튼 활성화
        check_list_and_toggle_button(id_list)

# 엑셀에 url 리스트를 가져오는 함수
def update_log(id_list):
    log_text_widget.delete(1.0, tk.END)
    for url in id_list:
        log_text_widget.insert(tk.END, url + "\n")
    log_text_widget.insert(tk.END, f"\n총 {len(id_list)}개의 URL이 있습니다.\n")
    log_text_widget.see(tk.END)

# url들이 정상인지를 확인하여 버튼을 활성 비활성화 한다.
def check_list_and_toggle_button(id_list):
    if id_list:
        start_button.config(state=tk.NORMAL)
    else:
        start_button.config(state=tk.DISABLED)

# url에서 id를 추출
def extract_blog_id(url):
    # "PostList.naver"에서 blogId 추출
    postlist_pattern = r'[?&]blogId=([^&]+)'
    postlist_match = re.search(postlist_pattern, url)

    if postlist_match:
        return postlist_match.group(1)  # blogId 값 추가

    # 기본 URL에서 ID 추출 (www 포함)
    base_pattern = r'https?://(?:www\.)?(?:blog|m\.blog)\.naver\.com/([^/?&]+)'
    match = re.search(base_pattern, url)

    if match:
        return match.group(1)  # 첫 번째 그룹 (ID)

    return ''  # ID가 없을 경우 빈 문자열 반환

# 엑셀의 url리스트를 읽어오는 함수.
def read_excel_file(filepath):
    df = pd.read_excel(filepath, sheet_name=0)
    id_list = []
    url_list = df.iloc[:, 1].tolist()
    for url in url_list:
        new_url = extract_blog_id(url)
        id_list.append(new_url)
    return id_list

# 엑셀저장
def save_excel_file(new_data):
    global filepath
    # 기존 엑셀 파일 읽기
    df = pd.read_excel(filepath, sheet_name=0)

    # 기존 데이터와 new_data의 길이가 맞지 않는 경우, 예외 처리
    if len(df) != len(new_data):
        messagebox.showwarning("경고", "기존 데이터와 새로운 데이터의 길이가 일치하지 않습니다.")
        raise ValueError("기존 데이터와 새로운 데이터의 길이가 일치하지 않습니다.")

    # 새로운 데이터를 H열에 추가
    df['H'] = new_data  # 'H' 컬럼이 없으면 새로 생성하고, 있으면 기존 데이터를 덮어씀

    # 업데이트된 데이터 저장
    df.to_excel(filepath, index=False)

# ══════════════════════════════════════════════════════
# endregion



# region
# ══════════════════════════════════════════════════════
# 네이버 API
# ══════════════════════════════════════════════════════

# 네이버 로그아웃
def naver_logout():
    global global_cookies, login_button, login_board, id_list, extracted_data_list
    global_cookies = None
    login_button.config(text="로그인", command=naver_login)
    login_board.config(text="관리자님 로그인을 진행해주세요.", fg="red")
    messagebox.showinfo("알림", "로그인 아웃: 정상 로그아웃 되었습니다.")
    start_button.config(text="시작", bg="#d0f0c0", fg="black", state=tk.DISABLED)
    id_list = []
    extracted_data_list = []  # 모든 데이터 저장용


# 네이버 로그인
def naver_login():
    global global_cookies, login_button, login_board
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
                global_cookies = cookies
                messagebox.showinfo("알림", "로그인 성공: 정상 로그인 되었습니다.")
                login_button.config(text="로그아웃", command=naver_logout)
                login_board.config(text="관리자님 로그인 되었습니다. 작업을 진행해주세요.", fg="blue")
                break
    except Exception as e:
        messagebox.showwarning("경고", f"로그인 중 오류가 발생했습니다.{e}")
    finally:
        driver.quit()

# 내 블로그 30개 번호 가져오기
def fetch_naver_blog_my_logNos(blog_id, current_page):
    global global_cookies
    """주어진 블로그 ID와 현재 페이지를 사용하여 게시글 제목을 가져옵니다."""
    url = f"https://m.blog.naver.com/api/blogs/{blog_id}/post-list?categoryNo=0&itemCount=30&page={current_page}&userId="
    headers = {
        "authority": "m.blog.naver.com",
        "method": "GET",
        "path": "/api/blogs/roketmissile/post-list?categoryNo=0&itemCount=10&page=1&userId=",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
        "referer": "https://m.blog.naver.com/roketmissile?tab=1",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, cookies=global_cookies)
        # response = requests.get(url, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get("isSuccess"):
                items = json_data['result']['items']
                logNos = []
                for item in items:
                    logNos.append(item.get("logNo"),)
                return logNos[:30]
    except requests.RequestException as e:
        messagebox.showwarning("경고", "게시글을 가져오는중 에러가 발생했습니다.")
        return []
    except json.JSONDecodeError as e:
        messagebox.showwarning("경고", "게시글을 가져오는중 에러가 발생했습니다.")
        return []

# 블로그 게시글에서 해시태그들을 가져오기
def fetch_gs_tag_name(blog_id, logNo):

    url = f'https://m.blog.naver.com/{blog_id}/{logNo}?referrerCode=1'

    # HTTP GET 요청
    headers = {
        'authority': 'm.blog.naver.com',
        'method': 'GET',
        'path': f'/{blog_id}/{logNo}?referrerCode=1',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }

    # response = requests.get(url, headers=headers)
    response = requests.get(url, headers=headers, cookies=global_cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # <script> 태그 찾기
        for script in soup.find_all('script'):
            if 'gsTagName' in script.text:
                # gsTagName 변수 찾기
                start = script.text.find('gsTagName = "') + len('gsTagName = "')
                end = script.text.find('";', start)
                gs_tag_value = script.text[start:end]

                # 콤마로 나누고 최대 5개 반환
                tags = gs_tag_value.split(',')
                return tags[:5]  # 최대 5개 반환

    return []  # 요청 실패 시 빈 리스트 반환

# 검색 블로그 20개 번호 가져오기
def fetch_naver_blog_search_logNos(query, page):
    url = "https://s.search.naver.com/p/review/48/search.naver"

    # 페이로드를 딕셔너리 형태로 정의
    payload = {
        "ssc": "tab.blog.all",
        "api_type": 8,
        "query": f"{query}",
        "start": f"{page + 1}",
        "sm": "tab_hty.top",
        "prank": f'{page}',
        "ngn_country": "KR"
    }
    query_encoding = quote(query)

    # 헤더 설정
    headers = {
        "authority": "s.search.naver.com",
        "method": "GET",
        "path": "/p/review/48/search.naver",
        "scheme": "https",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://search.naver.com",
        "referer": f"https://search.naver.com/search.naver?sm=tab_hty.top&ssc=tab.blog.all&query={query_encoding}&oquery={query_encoding}&tqi=iyLxLlqo1awssNDx7HsssssstkG-146063",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers, params=payload, cookies=global_cookies)
    # response = requests.get(url, headers=headers, params=payload)
    if response.status_code == 200:
        # JSON 응답 파싱
        json_data = response.json()
        contents = json_data.get("contents", "")

        # HTML 파싱
        soup = BeautifulSoup(contents, 'html.parser')

        # class="detail_box" 안에 있는 title_area의 a 태그 찾기
        detail_boxes = soup.find_all(class_="detail_box")
        logNos = []  # 제목과 LogNo를 담을 리스트

        for box in detail_boxes:
            title_area = box.find(class_="title_area")
            if title_area:
                a_tag = title_area.find('a')
                if a_tag:
                    # href 속성에서 LogNo 추출
                    href = a_tag['href']
                    log_no = href.split('/')[-1]  # URL의 마지막 부분이 LogNo
                    logNos.append(log_no)

        return logNos[:30]  # LogNo 리스트
    else:
        new_print("조회된 해시태크 목록이 없습니다.")
        return []

# ══════════════════════════════════════════════════════
# endregion



# region
# ══════════════════════════════════════════════════════
# 윈도우 처리
# ══════════════════════════════════════════════════════

# 완료후 깜빡임 상태를 관리하는 함수
def flash_window(root):
    global flashing

    # FLASHWINFO 구조체 정의
    class FLASHWINFO(ctypes.Structure):
        _fields_ = [('cbSize', ctypes.c_uint),
                    ('hwnd', ctypes.c_void_p),
                    ('dwFlags', ctypes.c_uint),
                    ('uCount', ctypes.c_uint),
                    ('dwTimeout', ctypes.c_uint)]

    FLASHW_ALL = 3  # 모든 플래시
    hwnd = root.winfo_id()  # Tkinter 창의 윈도우 핸들 얻기
    flash_info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, FLASHW_ALL, 0, 0)

    def flash():
        while flashing:
            ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash_info))
            time.sleep(0.5)  # 0.5초 간격으로 깜빡임

    threading.Thread(target=flash, daemon=True).start()  # 깜빡임을 별도의 쓰레드에서 실행

# 중지후 깜빡임 상태를 나태나는 윈도우 함수
def stop_flash_window(root):
    global flashing
    flashing = False

    # FLASHWINFO 구조체 정의
    class FLASHWINFO(ctypes.Structure):
        _fields_ = [('cbSize', ctypes.c_uint),
                    ('hwnd', ctypes.c_void_p),
                    ('dwFlags', ctypes.c_uint),
                    ('uCount', ctypes.c_uint),
                    ('dwTimeout', ctypes.c_uint)]

    hwnd = root.winfo_id()
    flash_info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, 0, 0, 0)
    ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash_info))

# 시작 버튼 누르면 실행되는 함수
def toggle_start_stop():
    if global_cookies:
        global id_list
        new_print("작업시작")
        if not id_list:
            messagebox.showwarning("경고", "엑셀 목록이 없습니다.")
            return
        if start_button.config('text')[-1] == '시작':
            start_button.config(text="중지", bg="red", fg="white")
            threading.Thread(target=start_processing).start()
        else:
            stop_processing()
    else:
        messagebox.showinfo("알림", "로그인을 진행해주세요.")

# 정지 버튼 정지 처리
def stop_processing():
    global stop_flag, id_list, extracted_data_list
    stop_flag = True
    id_list = []  # 배열 초기화
    extracted_data_list = []  # 모든 데이터 저장용
    start_button.config(text="시작", bg="#d0f0c0", fg="black", state=tk.DISABLED)
    new_print(f'작업중지')
    messagebox.showinfo("알림", "중지되었습니다..")

# 화면 로그
def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)

# ══════════════════════════════════════════════════════
# endregion



# region
# ══════════════════════════════════════════════════════
# 실제 메인 실행 로직
# ══════════════════════════════════════════════════════

# 대기시간 처리
def time_sleep():
    time.sleep(random.uniform(1, 1.5))

# 진행률 업데이트
def remaining_time_update(index, total_ids):
    progress["value"] = index + 1
    progress_label.config(text=f"진행률: {int((index + 1) / total_ids * 100)}%")

    # 30개글 x 5개 태그 x 2 번 (태그별 검색 조회) x 1.25 소요시간 = 375
    remaining_time = (total_ids - (index + 1)) * 375
    eta_label.config(text=f"남은 시간: {time.strftime('%H:%M:%S', time.gmtime(remaining_time))}")

# 실제 시작 처리 메인 로직
def start_processing():
    global stop_flag, extracted_data_list, id_list
    global root

    stop_flag = False
    # 기존 로그 화면 초기화
    log_text_widget.delete(1.0, tk.END)

    extracted_data_list = []
    total_ids = len(id_list)
    progress["maximum"] = total_ids
    remaining_time_update(-1, total_ids)

    # 전체 블로그 주소 id
    for index, blog_id in enumerate(id_list):
        new_print(f'아이디 : {blog_id} 계산 시작 ====================')
        hash_tag_cnt = 0
        if stop_flag:
            return
        try:
            # 내 블로그 30개 번호 가져오기
            logNos = fetch_naver_blog_my_logNos(blog_id, 1)
            new_print(f'아이디 : {blog_id}, 게시글 수 {len(logNos)} ====================')
            time_sleep()

            # 각 블로그안에 게시글 30개 리스트
            for idx, logNo in enumerate(logNos):
                if stop_flag:
                    return
                tags = fetch_gs_tag_name(blog_id, logNo)
                new_print(f'아이디 : {blog_id}, 게시글 번호 : {logNo}, 태그 목록 : {tags}')
                time_sleep()

                exit_loops = False
                for ix, tag in enumerate(tags):
                    if stop_flag:
                        return
                    # 검색 블로그 20개 번호 가져오기
                    search_logNos = fetch_naver_blog_search_logNos(tag, 0)
                    new_print(f'아이디 : {blog_id}, 게시글 번호 : {logNo}, 태그 : {tag}, 검색글 수 : {len(search_logNos)}')
                    time_sleep()

                    for i, search_logNo in enumerate(search_logNos):
                        if stop_flag:
                            return
                        if str(search_logNo) == str(logNo):
                            new_print(f'아이디 : {blog_id}, 게시글 번호 : {logNo}, 태그 : {tag}, 찾은 검색글 위치 : {i+1} 번째')
                            hash_tag_cnt += 1
                            exit_loops = True  # 플래그 변수를 True로 설정
                            break

                    if exit_loops:  # 플래그가 True인 경우 외부 루프 종료
                        break

            # 소수점 2자리 까지 (3번째 부터 버림)
            hash_tag_per = math.floor((hash_tag_cnt / 30) * 100 * 100) / 100
            extracted_data_list.append(hash_tag_per)

        except Exception as e:
            extracted_data ={}
            new_print(extracted_data, level="WARN")

        # 진행률 업데이트
        remaining_time_update(index, total_ids)

    if not stop_flag:
        save_excel_file(extracted_data_list)
        new_print("작업 완료.", level="SUCCESS")
        flash_window(root)
        messagebox.showinfo("알림", "작업이 완료되었습니다.")
        stop_flash_window(root)  # 메시지박스 확인 후 깜빡임 중지

# ══════════════════════════════════════════════════════
# endregion



# region
# ══════════════════════════════════════════════════════
# 메인 초기화
# ══════════════════════════════════════════════════════

# 초기화
def main():
    global log_text_widget, start_button, progress, progress_label, eta_label, root, login_button, login_board

    root = TkinterDnD.Tk()
    root.title("블로그 빅 프로그램")
    root.geometry("600x700")

    font_large = font.Font(size=10)

    # 시작 버튼
    login_button = tk.Button(root, text="로그인", command=naver_login, font=font_large, bg="#d0f0c0", fg="black", width=25)
    login_button.pack(pady=10)

    login_board = tk.Label(root, text="관리자님 로그인을 진행해주세요.\n(로그인 완료 되면 잠시 기다려주세요...)", width=40, height=5, font=font_large, bg="white", fg="red",
                           borderwidth=1, relief="solid", highlightbackground="black", highlightthickness=1)
    login_board.pack(pady=10)

    btn_browse = tk.Button(root, text="엑셀 파일 선택", command=browse_file, font=font_large, width=20)
    btn_browse.pack(pady=10)

    lbl_or = tk.Label(root, text="또는", font=font_large)
    lbl_or.pack(pady=5)

    lbl_drop = tk.Label(root, text="여기에 파일을 드래그 앤 드롭하세요", relief="solid", width=40, height=5, font=font_large, bg="white")
    lbl_drop.pack(pady=10)

    lbl_drop.drop_target_register(DND_FILES)
    lbl_drop.dnd_bind('<<Drop>>', on_drop)

    # 시작 버튼
    start_button = tk.Button(root, text="시작", command=toggle_start_stop, font=font_large, bg="#d0f0c0", fg="black", width=25, state=tk.DISABLED)
    start_button.pack(pady=10)

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

    progress_label = tk.Label(progress_frame, text="진행률: 0%", font=font_large)
    eta_label = tk.Label(progress_frame, text="남은 시간: 00:00:00", font=font_large)

    progress_label.pack(side=tk.TOP, padx=5)
    eta_label.pack(side=tk.TOP, padx=5)

    style = ttk.Style()
    style.configure("TProgressbar", thickness=30, troughcolor='white', background='green')
    progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    progress.pack(fill=tk.X, padx=10, pady=10, expand=True)

    root.mainloop()

# 최초 시작 메인
if __name__ == "__main__":
    main()

# ══════════════════════════════════════════════════════
# endregion