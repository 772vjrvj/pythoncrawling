import requests
from bs4 import BeautifulSoup
import re
import time
import random
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import timedelta
import threading
import math
import html  # html 모듈을 추가로 임포트


# 전역 변수 추가
stop_event = threading.Event()
search_thread = None
time_val = 4
# 공통 헤더 정의
LIST_HEADERS = {
    "authority": "terms.naver.com",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}
SEARCH_HEADERS = LIST_HEADERS.copy()

def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)


def set_progress():
    # 개별 진행률 업데이트
    progress_label.config(text=f"[진행률: {progress['value'] / progress['maximum'] * 100:.2f}% ({progress['value']}/{progress['maximum']})")
    remaining_time = (progress['maximum'] - progress['value']) * time_val
    eta = str(timedelta(seconds=remaining_time)).split(".")[0]  # 소수점 제거
    eta_label.config(text=f"예상 소요 시간: {eta}")
    progress.update_idletasks()


def start_app():
    global root, search_entry, search_button, log_text_widget, progress, progress_label, eta_label, overall_progress_label, overall_progress

    root = tk.Tk()
    root.title("네이버 백과사전 프로그램")
    root.geometry("700x750")  # 크기 조정

    font_large = ('Helvetica', 10)  # 폰트 크기

    # 옵션 프레임
    option_frame = tk.Frame(root)
    option_frame.pack(fill=tk.X, padx=10, pady=10)

    # 검색어 입력 프레임
    search_frame = tk.Frame(root)
    search_frame.pack(pady=20)

    # 검색어 레이블
    search_label = tk.Label(search_frame, text="URL:", font=font_large)
    search_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

    # 검색어 입력 필드
    search_entry = tk.Entry(search_frame, font=font_large, width=25)
    search_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    # 검색 버튼
    search_button = tk.Button(search_frame, text="검색", font=font_large, bg="lightgreen", command=on_search)
    search_button.grid(row=0, column=2, padx=5, pady=5)

    # 안내 문구
    guide_label = tk.Label(search_frame, text="* 백과사전 검색 및 카테고리 URL을 입력하세요 *", font=font_large, fg="red")
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

    root.mainloop()


def fetch_list_total_count(url):
    response = requests.get(url, headers=LIST_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    count_text = soup.select_one(".path_area .count").get_text(strip=True)
    total_count = int(''.join(filter(str.isdigit, count_text)))
    return total_count


def fetch_search_total_count(url):
    response = requests.get(url, headers=SEARCH_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    count_text = soup.select_one(".subject_item.selected .count").get_text(strip=True)
    total_count = int(''.join(filter(str.isdigit, count_text)))
    return total_count


def calculate_total_pages(total_count, per_page):
    return math.ceil(total_count / per_page)


def fetch_list_titles_by_page(url, page_num):
    paginated_url = f"{url}&page={page_num}"
    response = requests.get(paginated_url, headers=LIST_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = []
    li_items = soup.select("ul.content_list > li")
    for li in li_items:
        title_tag = li.select_one(".subject .title > a")
        if title_tag:
            # a 태그 전체 텍스트를 가져옴 (strong 태그 없음)
            titles.append(title_tag.get_text(strip=True))
    return titles


def fetch_search_titles_by_page(url, page_num, skip_first=False):
    paginated_url = f"{url}&page={page_num}"
    new_print(f'{page_num} 페이지, URL : {paginated_url}')
    response = requests.get(paginated_url, headers=SEARCH_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = []
    search_results = soup.select(".search_result_area")
    if page_num == 1 and skip_first:
        search_results = search_results[1:]

    for result in search_results:
        title_tag = result.select_one(".info_area .subject .title > a")
        if title_tag:
            # a 태그의 HTML 내용을 문자열로 가져옴
            full_html = title_tag.decode_contents()

            # 모든 HTML 태그 제거
            cleaned_title = re.sub(r'<.*?>', '', full_html)  # 모든 태그 제거
            # HTML 엔티티를 변환
            cleaned_title = html.unescape(cleaned_title)  # &amp;를 &로 변환
            titles.append(cleaned_title.strip())  # 공백 제거 후 리스트에 추가

    return titles


def process_list_url(url):
    total_count = fetch_list_total_count(url)
    new_print(f'총 추출건수 : {total_count}')
    total_pages = calculate_total_pages(total_count, 15)
    new_print(f'총 페이지 : {total_pages}')

    progress['maximum'] = total_pages
    progress['value'] = 0
    set_progress()

    all_titles = []
    for page_num in range(1, total_pages + 1):

        if stop_event.is_set():
            return all_titles

        page_titles = fetch_list_titles_by_page(url, page_num)
        new_print(f'{page_num} 페이지, 제목 수 : {len(page_titles)}')
        new_print(f'{page_num} 페이지, 제목 : {page_titles}')
        all_titles.extend(page_titles)

        progress['value'] = page_num
        set_progress()

        time.sleep(random.uniform(3, 5))

    return all_titles


def process_search_url(url):
    total_count = fetch_search_total_count(url)
    new_print(f'총 추출건수 : {total_count}')
    total_pages = calculate_total_pages(total_count, 10)
    new_print(f'총 페이지 : {total_pages}')

    progress['maximum'] = total_pages
    progress['value'] = 0
    set_progress()

    all_titles = []
    for page_num in range(1, total_pages + 1):

        if stop_event.is_set():
            return all_titles

        page_titles = fetch_search_titles_by_page(url, page_num, skip_first=(page_num == 1))
        new_print(f'{page_num} 페이지, 제목 수 : {len(page_titles)}')
        new_print(f'{page_num} 페이지, 제목 : {page_titles}')
        all_titles.extend(page_titles)

        progress['value'] = page_num
        set_progress()

        time.sleep(random.uniform(3, 5))

    return all_titles


def save_titles_to_excel(titles, output_file):
    # 제품 데이터를 DataFrame으로 변환
    df = pd.DataFrame(titles, columns=["제목"])
    df.to_excel(output_file, index=False)


def run_main(query):
    try:
        new_print(query)
        all_titles = []
        if "list.naver" in query:
            all_titles = process_list_url(query)
        elif "search.naver" in query:
            all_titles = process_search_url(query)

        # 결과를 Excel 파일로 저장
        output_file = "추출한_제목들.xlsx"  # 저장할 엑셀 파일 경로
        save_titles_to_excel(all_titles, output_file)

        if not stop_event.is_set():
            messagebox.showwarning("경고", "크롤링이 완료되었습니다.")
            search_button.config(bg="lightgreen", fg="black", text="검색")

    except Exception as e:
        new_print(f"Unexpected error in thread: {e}", "ERROR")


def on_search():
    global search_thread, stop_event
    query = search_entry.get().strip()
    if query:
        if ("https://terms.naver.com/search.naver" not in query and
                "https://terms.naver.com/list.naver" not in query):
            new_print("지원하지 않는 URL 형식입니다.")

        elif search_thread and search_thread.is_alive():
            # 중지 버튼이 클릭되면 작업 중지
            new_print("크롤링 중지")
            stop_event.set()  # 이벤트 설정
            search_button.config(bg="lightgreen", fg="black", text="검색")

            # 진행률 게이지바 초기화
            progress['value'] = 0
            progress_label.config(text="진행률: 0%")
            eta_label.config(text="예상 소요 시간: 00:00:00")
            messagebox.showwarning("경고", "크롤링이 중지되었습니다.")
        else:
            # 시작 버튼 클릭 시 모든 진행률 초기화
            stop_event.clear()  # 이벤트 초기화
            log_text_widget.delete('1.0', tk.END)  # 로그 초기화
            progress['value'] = 0  # 개별 진행률 초기화
            progress_label.config(text="진행률: 0%")
            eta_label.config(text="예상 소요 시간: 00:00:00")
            search_button.config(bg="red", fg="white", text="중지")
            search_thread = threading.Thread(target=run_main, args=(query,))
            search_thread.start()
    else:
        messagebox.showwarning("경고", "검색어를 입력하세요.")


# 여기에 main 함수와 기타 필요한 함수들을 포함시키세요.
if __name__ == "__main__":
    start_app()
