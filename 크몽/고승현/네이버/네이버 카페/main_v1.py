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
import json
import threading

# 전역 변수 설정
global_cookies = {}
cafe_id = ""
menu_list = []
menuid = ""
extracted_data = []

# GUI 설정
root = tk.Tk()
root.title("N 카페 게시글 추출기")
root.geometry("600x700")
root.configure(bg="#d2e7d3")

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
            messagebox.showwarning("경고", "로그인 실패: 300초 내에 로그인하지 않았습니다.")
            break

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

        # 쿠키 중 NID_AUT 또는 NID_SES 쿠키가 있는지 확인 (네이버 로그인 성공 시 생성되는 쿠키)
        if 'NID_AUT' in cookies and 'NID_SES' in cookies:
            logged_in = True
            global_cookies = cookies  # 로그인 성공 시 전역 변수에 쿠키 저장
            messagebox.showinfo("로그인 성공", "정상 로그인 되었습니다.")

    driver.quit()  # 작업이 끝난 후 드라이버 종료

# 로그인 초기화
def reset_login():
    global global_cookies
    global_cookies = {}
    messagebox.showinfo("초기화", "로그인 정보가 초기화되었습니다.")

# 카페 URL에서 카페 ID 및 메뉴 목록 가져오기
def fetch_cafe_info():
    global cafe_id
    cafe_url = cafe_url_entry.get()
    if not cafe_url:
        messagebox.showwarning("경고", "카페 URL을 입력해주세요.")
        return

    # get_cafe_id()와 get_menus() 함수 실행
    get_cafe_id(cafe_url)
    get_menus()

    # 메뉴 리스트를 드롭다운 메뉴에 추가
    menu_dropdown["values"] = [menu['menuName'] for menu in menu_list]
    messagebox.showinfo("정보", f"카페 정보가 성공적으로 가져왔습니다.")

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

# 카페 초기화
def reset_cafe():
    cafe_url_entry.delete(0, tk.END)

def fetch_articles_in_range(start_page, end_page):
    time.sleep(1)
    all_articles = []

    for page in range(start_page, end_page + 1):
        print(f"Fetching page {page}...")
        articles = fetch_article_data(page)
        if articles:
            all_articles.extend(articles)  # 각 페이지의 결과를 리스트에 합침
        else:
            print(f"Page {page}에서 데이터를 가져오지 못했습니다.")

    return all_articles

def fetch_article_details(cafe_id, article_id):
    # URL 생성
    time.sleep(1)
    url = f"https://apis.naver.com/cafe-web/cafe-articleapi/v2.1/cafes/{cafe_id}/articles/{article_id}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": "; ".join([f"{name}={value}" for name, value in global_cookies.items()])
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 요청이 실패하면 예외를 발생시킴

        # JSON 응답 반환
        return response.json()['result']

    except requests.exceptions.RequestException as e:
        print(f"Error fetching article details: {e}")
        return None

def fetch_article_data(page):
    global global_cookies, cafe_id, menuid

    print(f"menuid : {menuid}")

    url = f"https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json?search.clubid={cafe_id}&search.queryType=lastArticle&search.menuid={menuid}&search.page={page}&search.perPage=50"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": "; ".join([f"{name}={value}" for name, value in global_cookies.items()])
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 요청이 실패할 경우 예외를 발생시킴
        data = response.json()

        # "articleList"만 추출하여 리턴
        article_list = data.get("message", {}).get("result", {}).get("articleList", [])
        return article_list

    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def get_menus():
    global cafe_id, menu_list
    if cafe_id:
        # API 요청 URL 생성
        api_url = f"https://apis.naver.com/cafe-web/cafe2/SideMenuList?cafeId={cafe_id}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Cookie": "; ".join([f"{name}={value}" for name, value in global_cookies.items()])
        }

        # API 요청
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()

            # menus 배열에서 필요한 값들만 추출
            menus = data.get("message", {}).get("result", {}).get("menus", [])

            # 필요한 값들을 담은 배열 생성
            menu_list = [
                {
                    "cafeId": menu.get("cafeId"),
                    "menuId": menu.get("menuId"),
                    "menuName": menu.get("menuName")
                }
                for menu in menus
            ]

            print(f"menu_list : {menu_list}")
        else:
            print(f"API 요청 실패: {response.status_code}")
    else:
        print(f"로그인을 하세요.")

def extract_article_details(details, combined_article):
    # subject
    title = details.get("article", {}).get("subject", "")

    # menu name (HTML entity 제거)
    menu_name_html = details.get("article", {}).get("menu", {}).get("name", "")
    menu_name = re.sub(r'&#[0-9]+;', '', menu_name_html)

    # nick and email
    writer_info = details.get("article", {}).get("writer", {})
    nick = writer_info.get("nick", "")
    id = writer_info.get("id", "")
    email = f"{id}@naver.com"

    # read count, comment count, like count (from combined_articles)
    read_count = combined_article.get("readCount", 0)
    comment_count = combined_article.get("commentCount", 0)
    like_it_count = combined_article.get("likeItCount", 0)

    # date
    write_date_timestamp = details.get("article", {}).get("writeDate", 0)
    date = datetime.fromtimestamp(write_date_timestamp / 1000).strftime('%Y.%m.%d')

    # content (HTML에서 텍스트만 추출)
    content_html = details.get("article", {}).get("contentHtml", "")
    content = re.sub('<[^<]+?>', '', content_html).strip().replace('\n', '\n')

    # img_urls
    img_urls = writer_info.get("image", {}).get("url", "")

    # link
    cafe_id = details.get("cafeId", "")
    menu_id = details.get("menuId", "")
    article_id = details.get("articleId", "")
    link = f"https://cafe.naver.com/ArticleRead.nhn?clubid={cafe_id}&page=1&menuid={menu_id}&boardtype=L&articleid={article_id}&referrerAllArticles=false"

    # 최종 결과
    article_info = {
        "title": title,
        "id": id,
        "email": email,
        "nick": nick,
        "menu_name": menu_name,
        "readCount": read_count,
        "commentCount": comment_count,
        "likeItCount": like_it_count,
        "date": date,
        "content": content,
        "img_urls": img_urls,
        "link": link
    }

    return article_info

def select_menu(event):
    global menuid
    selected_menu = menu_dropdown.get()
    for menu in menu_list:
        if menu['menuName'] == selected_menu:
            menuid = menu['menuId']
            print(f"menuid : {menuid}")
            break

# 데이터 추출 시작
def start_extraction():
    try:
        start_page = int(start_page_entry.get())
        end_page = int(end_page_entry.get())
        if end_page < start_page:
            messagebox.showwarning("경고", "종료 페이지는 시작 페이지보다 크거나 같아야 합니다.")
            return
    except ValueError:
        messagebox.showwarning("경고", "페이지 번호를 올바르게 입력해주세요.")
        return

    # 추출 로직을 별도 스레드에서 실행
    extraction_thread = threading.Thread(target=run_extraction, args=(start_page, end_page))
    extraction_thread.start()

def run_extraction(start_page, end_page):
    # 추출 로직 실행
    combined_articles = fetch_articles_in_range(start_page, end_page)
    print(f"combined_articles : {combined_articles}")
    progress_bar["maximum"] = len(combined_articles)
    detailed_articles = []

    for i, article in enumerate(combined_articles):
        details = fetch_article_details(article['cafeId'], article['articleId'])
        if details:
            combined_article = {
                "readCount": article['readCount'],
                "commentCount": article['commentCount'],
                "likeItCount": article['likeItCount']
            }
            article_info = extract_article_details(details, combined_article)
            print(f"article_info : {article_info['id']}")
            detailed_articles.append(article_info)
            progress_bar["value"] = i + 1
            progress_label.config(text=f"진행 중: {i + 1}/{len(combined_articles)}")

    messagebox.showinfo("완료", f"총 {len(detailed_articles)}개의 기사가 수집되었습니다.")
    global extracted_data
    extracted_data = detailed_articles

# 데이터 저장
# 데이터 저장
def save_data(format_type):
    if not extracted_data:
        messagebox.showwarning("경고", "저장할 데이터가 없습니다.")
        return

    download_path = os.getcwd()  # 현재 작업 디렉토리를 기본 저장 경로로 설정

    file_name = file_name_entry.get()
    if not file_name:
        messagebox.showwarning("경고", "파일명을 입력해주세요.")
        return

    if format_type == 1:  # 엑셀
        df = pd.DataFrame(extracted_data)
        file_path = os.path.join(download_path, f"{file_name}.xlsx")
        df.to_excel(file_path, index=False)
    elif format_type == 2:  # CSV
        df = pd.DataFrame(extracted_data)
        file_path = os.path.join(download_path, f"{file_name}.csv")
        df.to_csv(file_path, index=False, encoding='utf-8-sig')  # 인코딩을 'utf-8-sig'로 설정하여 한글 깨짐 방지
    elif format_type == 3:  # 텍스트
        file_path = os.path.join(download_path, f"{file_name}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(extracted_data, indent=4, ensure_ascii=False))

    messagebox.showinfo("저장 완료", f"데이터가 {file_path}에 저장되었습니다.")


# GUI 요소 배치
# (1) 로그인 섹션
login_frame = tk.Frame(root, bg="#d2e7d3")
login_frame.pack(pady=10)
tk.Button(login_frame, text="로그인", command=naver_login).grid(row=0, column=0, rowspan=2, padx=10)

# (2) 카페 URL 및 메뉴 선택 섹션
cafe_frame = tk.Frame(root, bg="#d2e7d3")
cafe_frame.pack(pady=10)
tk.Label(cafe_frame, text="카페 URL", bg="#d2e7d3").grid(row=0, column=0)
cafe_url_entry = tk.Entry(cafe_frame, width=40)
cafe_url_entry.grid(row=0, column=1)
tk.Button(cafe_frame, text="가져오기", command=fetch_cafe_info).grid(row=0, column=2, padx=10)

tk.Label(cafe_frame, text="카페명:", bg="#d2e7d3").grid(row=1, column=0)
menu_dropdown = ttk.Combobox(cafe_frame, state="readonly", width=30)
menu_dropdown.grid(row=1, column=1)
menu_dropdown.bind("<<ComboboxSelected>>", select_menu)

# (3) 옵션 및 추출 섹션
option_frame = tk.Frame(root, bg="#d2e7d3")
option_frame.pack(pady=10)

# 로그인 초기화 및 카페 초기화 버튼 중앙 정렬
reset_buttons_frame = tk.Frame(option_frame, bg="#d2e7d3")
reset_buttons_frame.grid(row=0, column=0, columnspan=4, pady=10)
tk.Button(reset_buttons_frame, text="로그인 초기화", command=reset_login).grid(row=0, column=0, padx=20)
tk.Button(reset_buttons_frame, text="카페 초기화", command=reset_cafe).grid(row=0, column=1, padx=20)

tk.Label(option_frame, text="시작 페이지", bg="#d2e7d3").grid(row=1, column=0)
start_page_entry = tk.Entry(option_frame, width=5)
start_page_entry.grid(row=1, column=1, padx=5)
tk.Label(option_frame, text="종료 페이지", bg="#d2e7d3").grid(row=1, column=2)
end_page_entry = tk.Entry(option_frame, width=5)
end_page_entry.grid(row=1, column=3, padx=5)
tk.Button(option_frame, text="추출 시작", command=start_extraction).grid(row=2, column=0, columnspan=4, pady=10)

# 진행 상황 표시
progress_bar = ttk.Progressbar(option_frame, length=400, mode="determinate")
progress_bar.grid(row=3, column=0, columnspan=4)
progress_label = tk.Label(option_frame, text="진행 중: 0/0", bg="#d2e7d3")
progress_label.grid(row=4, column=0, columnspan=4)

# (4) 저장 섹션
save_frame = tk.Frame(root, bg="#d2e7d3")
save_frame.pack(pady=10)
tk.Label(save_frame, text="저장경로:", bg="#d2e7d3").grid(row=0, column=0)
tk.Label(save_frame, text=os.getcwd(), bg="#d2e7d3").grid(row=0, column=1)
tk.Label(save_frame, text="파일명:", bg="#d2e7d3").grid(row=1, column=0)
file_name_entry = tk.Entry(save_frame)
file_name_entry.insert(0, "추출 결과 Example")  # 기본 파일명 설정
file_name_entry.grid(row=1, column=1)
tk.Button(save_frame, text="엑셀 파일로 저장", command=lambda: save_data(1)).grid(row=2, column=0, pady=5)
tk.Button(save_frame, text="CSV 파일로 저장", command=lambda: save_data(2)).grid(row=2, column=1, pady=5)
tk.Button(save_frame, text="텍스트 파일로 저장", command=lambda: save_data(3)).grid(row=2, column=2, pady=5)

# 전역 변수 초기화
extracted_data = []

root.mainloop()