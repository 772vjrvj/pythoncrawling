import datetime
import json
import random
import re
import threading
import time
import tkinter as tk
from tkinter import messagebox

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
            # 'cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; NACT=1; nid_inf=391290400; NID_AUT=BKWCh2nwSx87OqhQiU7fA53ABVeIM0NVMvSL50BLM9CsrtH2hS3M5nj4JkmZmLa5; NID_SES=AAABrK7oOJ3oxSpt990kiHxmKrg4harLTIhsTFL4RNy721y0kPWFyndoU2cAObU+KJUscFZV7gaVh8lMUyj/pIpfJPAb2Kt9Acnx2/0GP0qd95hsxnijuZU4yCTu+37rUwjcJoQI217JYznF8kRHVg9+yuCQJ4hDtP3/TSENNHeX4zw9RudCmqQoLp9HEUZjzmzRNII8lXg2c+XmDMg13hTxaFnF+6wDkb6dtzRGKK7VrV5bTPiL0/taU0rS3zytdz984pGZieeS74tG7KdSx+IO9WAQ8bNU99Vgk7QiQ4lA17VHmCtxHa1BXXsj3/hJG3J1S6/9WQjuxWqmGPnW2g0tHtcFMqqN0AaF9/fdEoFrY9YKJ3S8M06MyDSBqMuigP3mul7VFGM37qKxpnz/lvnDZ4SDNY32EKYnStMUssjPxr7pnuF+cGubpwM5DNK8/X4FewZRiOT6J1hUjGpPFOuq8hvCqOj1rqjHNcqlxziFSC42w4N/FoNEVn9SaAXvBh1L75nTcm3wXGMKzMxygVCZPc99dsO+XUhpbusDOlN62HGLNJwPteOhKo7ZyQb4k5YWXA==; NID_JKL=CNZkLlqEX2rtTV3YMO64OWCpmUjIqDGQwtQED8C+LlE=; BUC=50ImD0ovxSThrenHO4dcb-MPmonlTPAc0WgfuSDYqZk=',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'referer': '',
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
                    road = data.get(f"PlaceDetailBase:{place_id}", {}).get("road", "")
                    address = data.get(f"PlaceDetailBase:{place_id}", {}).get("address", "")
                    roadAddress = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")
                    category = data.get(f"PlaceDetailBase:{place_id}", {}).get("category", "")
                    conveniences = data.get(f"PlaceDetailBase:{place_id}", {}).get("conveniences", [])
                    virtualPhone = data.get(f"PlaceDetailBase:{place_id}", {}).get("virtualPhone", [])
                    visitorReviewsScore = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsScore", "")
                    visitorReviewsTotal = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsTotal", "")

                    root_query = data.get("ROOT_QUERY", {})
                    place_detail_key = f'placeDetail({{"input":{{"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                    # 기본 place_detail_key 값이 없으면 checkRedirect 포함된 key로 재시도
                    if place_detail_key not in root_query:
                        place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                    fsasReviewsTotal = root_query.get(place_detail_key, {}).get('fsasReviews', {}).get("total", "")
                    if not fsasReviewsTotal:
                        fsasReviewsTotal = root_query.get(place_detail_key, {}).get("fsasReviews({\"fsasReviewsType\":\"restaurant\"})", {}).get("total", "")

                    # business_hours 초기 시도
                    business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"shopWindow\"]})", [])

                    # business_hours 값이 없으면 다른 source를 시도
                    if not business_hours:
                        business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"jto\",\"shopWindow\"]})", [])

                    new_business_hours_json = root_query.get(place_detail_key, {}).get('newBusinessHours', [])

                    if not new_business_hours_json:
                        new_business_hours_json = root_query.get(place_detail_key, {}).get("newBusinessHours({\"format\":\"restaurant\"})", [])

                    # 별점, 방문자 리뷰 수, 블로그 리뷰 수가 0이거나 없으면 공백 처리
                    visitorReviewsScore = visitorReviewsScore if visitorReviewsScore and visitorReviewsScore != "0" else ""
                    visitorReviewsTotal = visitorReviewsTotal if visitorReviewsTotal and visitorReviewsTotal != "0" else ""
                    fsasReviewsTotal = fsasReviewsTotal if fsasReviewsTotal and fsasReviewsTotal != "0" else ""

                    # category를 대분류와 소분류로 나누기
                    category_list = category.split(',') if category else ["", ""]
                    main_category = category_list[0] if len(category_list) > 0 else ""
                    sub_category = category_list[1] if len(category_list) > 1 else ""

                    url = f"https://m.place.naver.com/place/{place_id}/home"
                    map_url = f"https://map.naver.com/p/entry/place/{place_id}"

                    urls = []
                    homepages = root_query.get(place_detail_key, {}).get('shopWindow', {}).get("homepages", "")
                    if homepages:
                        # etc 배열에서 url 가져오기
                        for item in homepages.get("etc", []):
                            urls.append(item.get("url", ""))

                        # repr의 url 가져오기
                        repr_data = homepages.get("repr")
                        repr_url = repr_data.get("url", "") if repr_data else ""
                        if repr_url:
                            urls.append(repr_url)

                    result = {
                        "이름": name,
                        "주소(지번)": address,
                        "주소(도로명)": roadAddress,
                        "대분류": main_category,
                        "소분류": sub_category,
                        "별점": visitorReviewsScore,
                        "방문자리뷰수": visitorReviewsTotal,
                        "블로그리뷰수": fsasReviewsTotal,
                        "이용시간1": format_business_hours(business_hours),
                        "이용시간2": format_new_business_hours(new_business_hours_json),
                        "카테고리": category,
                        "URL": url,
                        "지도": map_url,
                        "편의시설": ', '.join(conveniences) if conveniences else '',
                        "전화번호": virtualPhone,
                        "사이트": urls,
                        "주소지정보": road,
                    }

                    return result

    except requests.exceptions.RequestException as e:
        new_print(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
    except Exception as e:
        new_print(f"Error processing data for Place ID: {place_id}: {e}")
    return None



def format_business_hours(business_hours):
    formatted_hours = []
    try:
        if business_hours:
            for hour in business_hours:
                day = hour.get('day', '') or ''
                start_time = hour.get('startTime', '') or ''
                end_time = hour.get('endTime', '') or ''
                if day and start_time and end_time:
                    formatted_hours.append(f"{day} {start_time} - {end_time}")
    except Exception as e:
        new_print(f"Unexpected error: {e}")
        return ""
    return '\n'.join(formatted_hours).strip() if formatted_hours else ""



def format_new_business_hours(new_business_hours):
    formatted_hours = []
    try:
        if new_business_hours:
            for item in new_business_hours:
                status_description = item.get('businessStatusDescription', {}) or {}
                status = status_description.get('status', '') or ''
                description = status_description.get('description', '') or ''

                if status:
                    formatted_hours.append(status)
                if description:
                    formatted_hours.append(description)

                for info in item.get('businessHours', []) or []:
                    day = info.get('day', '') or ''
                    business_hours = info.get('businessHours', {}) or {}
                    start_time = business_hours.get('start', '') or ''
                    end_time = business_hours.get('end', '') or ''

                    break_hours = info.get('breakHours', []) or []
                    break_times = [f"{bh.get('start', '') or ''} - {bh.get('end', '') or ''}" for bh in break_hours]
                    break_times_str = ', '.join(break_times) + ' 브레이크타임' if break_times else ''

                    last_order_times = info.get('lastOrderTimes', []) or []
                    last_order_times_str = ', '.join([f"{lo.get('type', '')}: {lo.get('time', '')}" for lo in last_order_times]) + ' 라스트오더' if last_order_times else ''

                    if day:
                        formatted_hours.append(day)
                    if start_time and end_time:
                        formatted_hours.append(f"{start_time} - {end_time}")
                    if break_times_str:
                        formatted_hours.append(break_times_str)
                    if last_order_times_str:
                        formatted_hours.append(last_order_times_str)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ""
    return '\n'.join(formatted_hours).strip() if formatted_hours else ""



def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)



def main(query, total_queries, current_query_index, total_locs, locs_index, check):
    try:
        page = 1
        results = []
        all_ids = set()
        all_ids_list = []

        # 키워드에 매핑되는 아이디 수집
        new_print(f"크롤링 시작")
        while True:
            if stop_event.is_set():
                return

            result = fetch_search_results(query, page)
            if not result:
                break

            place_list = result.get("result", {}).get("place", {}).get("list", [])
            ids_this_page = [place.get("id") for place in place_list if place.get("id")]

            new_print(f"전국 : {locs_index}/{total_locs}, 키워드 : {current_query_index}/{total_queries}, 페이지 : {page}, 검색어 : {query}==============================================")
            new_print(f"페이지 : {page}, 목록 : {ids_this_page}")

            if not ids_this_page:
                break

            all_ids.update(ids_this_page)
            page += 1
            time.sleep(random.uniform(1, 2))

        if not stop_event.is_set():
            all_ids_list = list(all_ids)
            total_count = len(all_ids_list)
            new_print(f"전국 : {locs_index}/{total_locs}, 키워드 : {current_query_index}/{total_queries}, 전체 : {total_count}, 검색어 : {query}==============================================")

        for idx, place_id in enumerate(all_ids_list, start=1):
            if stop_event.is_set():
                return

            place_info = fetch_place_info(place_id)
            results.append(place_info)

        if not stop_event.is_set():
            save_to_excel(results)

    except Exception as e:
        print(f"Unexpected error: {e}")



def save_to_excel(results, mode='w'):
    new_print(f"엑셀 저장 시작...")

    # 현재 날짜와 시간 구하기
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 파일 이름에 현재 날짜와 시간 추가, 파일 이름을 안전하게 처리
    file_name = f'naver_place_{timestamp}.xlsx'
    try:
        if mode == 'a':
            existing_df = pd.read_excel(file_name)
            new_df = pd.DataFrame(results)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(results)
        df.to_excel(file_name, index=False)
    except FileNotFoundError:
        df = pd.DataFrame(results)
        df.to_excel(file_name, index=False)

    new_print(f"엑셀 저장 완료 {file_name}")
    # 메시지박스 표시



def sanitize_filename(name):
    # 파일 이름에 사용할 수 없는 문자들을 제거합니다.
    return re.sub(r'[\\/*?:"<>|]', "", name)



def run_main(querys):
    global checkbox_var

    locs = [
        { '시도' : '전북' , '시군구' : '무주군' , '읍면동' : '무주읍' },
        { '시도' : '서울' , '시군구' : '종로구' , '읍면동' : '청운동' }
    ]

    try:
        query_list = [q.strip() for q in querys.split(",")]
        total_queries = len(query_list)
        total_locs = len(locs)

        if checkbox_var:
            for index, loc in enumerate(locs, start=1):
                if stop_event.is_set():
                    break
                name = f'{loc["시도"]} {loc["시군구"]} {loc["읍면동"]} '
                for idx, query in enumerate(query_list, start=1):
                    if stop_event.is_set():
                        break
                    full_name = name + query
                    new_print(f"전국 : {index}/{total_locs}, 키워드 : {idx}/{total_queries}, 검색어 : {full_name}==============================================")
                    main(query, total_queries, idx, total_locs, index, checkbox_var)
        else:
            for ix, qr in enumerate(query_list, start=1):
                if stop_event.is_set():
                    break
                new_print(f"전국 : 0/0, 키워드 : {ix}/{total_queries}, 검색어 : {qr}==============================================")
                main(qr, total_queries, ix, 0, 0, checkbox_var)

        if not stop_event.is_set():
            messagebox.showwarning("경고", "크롤링이 완료되었습니다.")
            search_button.config(bg="lightgreen", fg="black", text="검색")

    except Exception as e:
        new_print(f"Unexpected error in thread: {e}", "ERROR")


# 검색 버튼
def on_search():
    global search_thread, stop_event
    query = search_entry.get().strip()
    if query:
        if search_thread and search_thread.is_alive():
            # 중지 버튼이 클릭되면 작업 중지
            new_print("크롤링 중지")
            stop_event.set()  # 이벤트 설정
            search_button.config(bg="lightgreen", fg="black", text="검색")
            messagebox.showwarning("경고", "크롤링이 중지되었습니다.")
        else:
            # 시작 버튼 클릭 시 모든 진행률 초기화
            stop_event.clear()  # 이벤트 초기화
            log_text_widget.delete('1.0', tk.END)  # 로그 초기화
            search_button.config(bg="red", fg="white", text="중지")
            search_thread = threading.Thread(target=run_main, args=(query,))
            search_thread.start()
    else:
        messagebox.showwarning("경고", "검색어를 입력하세요.")


# 여기에 main 함수와 기타 필요한 함수들을 포함시키세요.
def start_app():
    global root, search_entry, search_button, log_text_widget, checkbox_var

    root = tk.Tk()
    root.title("네이버 블로그 프로그램")
    root.geometry("700x600")  # 크기 조정

    # 체크박스를 사용하려면 root가 먼저 생성되어야 합니다.
    checkbox_var = tk.BooleanVar()  # 체크박스의 상태를 저장할 변수

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

    # 체크박스 생성
    checkbox = tk.Checkbutton(search_frame, text="전국 선택", font=font_large, variable=checkbox_var)
    checkbox.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

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

    root.mainloop()


# 셀레니움 세팅
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
    naver_login_root.geometry("300x150")  # 창 크기
    screen_width = naver_login_root.winfo_screenwidth()  # 화면 너비
    screen_height = naver_login_root.winfo_screenheight()  # 화면 높이
    window_width = 300  # 창 너비
    window_height = 150  # 창 높이

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
            print("Login successful")
            print("Response data:", response.json())

            # 세션 관리로 쿠키는 자동 처리
            print("Cookies after login:", session.cookies)
            global_server_cookies = session.cookies.get_dict()
            print("Cookies:", global_server_cookies)
            return True
        else:
            print("Login failed with status code:", response.status_code)
            print("Error message:", response.text)
            return False
    except Exception as e:
        print("An error occurred during login:", e)
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

    try:
        # /check-me 엔드포인트를 호출하여 세션 상태 확인
        response = session.get(url, headers=headers, cookies=cookies)
        print("Request headers for check-me:", response.request.headers)

        if response.status_code == 200:
            print("Session check successful:", response.text)
            login_server_check = response.text
        else:
            print("Session check failed with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred while checking session:", e)


# 세션 실시간 요청
def check_session_periodically(session, server_type="server"):
    while True:
        time.sleep(300)  # 5분 대기
        check_session(session, server_type)  # 세션 상태를 체크


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


# 로그인 창 생성
def login_window():
    global login_root, id_entry, pw_entry

    login_root = tk.Tk()
    login_root.title("로그인")

    # 창 크기 설정
    login_root.geometry("300x200")  # 창 크기
    screen_width = login_root.winfo_screenwidth()  # 화면 너비
    screen_height = login_root.winfo_screenheight()  # 화면 높이
    window_width = 300  # 창 너비
    window_height = 200  # 창 높이

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

    # 로그인 버튼
    login_button = tk.Button(login_root, text="로그인", command=on_login)
    login_button.pack(pady=10)

    login_root.mainloop()


# 메인
if __name__ == "__main__":
    # login_window()  # 로그인 창 호출
    start_app()