import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
from tkinter import filedialog, font, messagebox
import time
import random
import threading
import requests
import os
from tkinter import ttk  # 진행률 표시를 위한 모듈 추가
import ctypes
from bs4 import BeautifulSoup
import re
import json


url_list = []
extracted_data_list = []  # 모든 데이터 저장용
stop_flag = False  # 중지를 위한 플래그

def read_excel_file(filepath):
    df = pd.read_excel(filepath, sheet_name=0)
    url_list = df.iloc[:, 0].tolist()
    return url_list

def update_log(url_list):
    log_text_widget.delete(1.0, tk.END)
    for url in url_list:
        log_text_widget.insert(tk.END, url + "\n")
    log_text_widget.insert(tk.END, f"\n총 {len(url_list)}개의 URL이 있습니다.\n")
    log_text_widget.see(tk.END)

def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)

def extract_prdtNo(url):
    # URL에서 prdtNo 값을 추출하는 함수
    if "prdtNo=" in url:
        prdtNo_part = url.split("prdtNo=")[-1]
        prdtNo = prdtNo_part.split("&")[0]  # prdtNo 값 추출
        return prdtNo
    return None

def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def process_author_info(url):
    soup = get_soup(url)
    author_span = soup.find("span", itemprop="author", itemscope=True, itemtype="http://schema.org/Person")
    if author_span:
        author_url = author_span.find("link", itemprop="url")["href"]
        return f"{author_url}/videos"
    return None

def extract_published_time(url):
    soup = get_soup(url)
    scripts = soup.find_all("script")

    for script in scripts:
        if script.string and "ytInitialData" in script.string:
            json_text = re.search(r"var ytInitialData = ({.*?});", script.string, re.DOTALL)
            if json_text:
                try:
                    yt_data = json.loads(json_text.group(1))
                    tabs = yt_data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
                    for tab in tabs:
                        rich_grid_renderer = tab.get("tabRenderer", {}).get("content", {}).get("richGridRenderer", {})
                        for item in rich_grid_renderer.get("contents", []):
                            video_renderer = item.get("richItemRenderer", {}).get("content", {}).get("videoRenderer", {})
                            if video_renderer.get("publishedTimeText"):
                                return video_renderer["publishedTimeText"]["simpleText"]
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    return None
    return None


def start_processing():
    global stop_flag, extracted_data_list, root
    stop_flag = False
    log_text_widget.delete(1.0, tk.END)  # 기존 로그 화면 초기화

    extracted_data_list = []
    total_urls = len(url_list)
    progress["maximum"] = total_urls

    for index, url in enumerate(url_list, start=1):
        if stop_flag:
            break
        new_print(f"Processing URL {index}: {url}")

        if not any(substring in url for substring in ["/c/", "/channel/", "/@"]):
            video_url = process_author_info(url)
        elif "/videos" in url:
            video_url = url
        else:
            video_url = url.rstrip('/') + "/videos"

        print(f"video_url : {video_url}")

        result = ""
        if  video_url:
            result = extract_published_time(video_url)

        new_print(f"Result for URL {index}: {result or 'Not found'}")
        extracted_data_list.append(result)

        # 진행률 업데이트
        progress["value"] = index
        progress_label.config(text=f"진행률: {int((index) / total_urls * 100)}%")

        remaining_time = (total_urls - (index)) * 2.5  # 남은 URL 개수 * 2초
        eta_label.config(text=f"남은 시간: {time.strftime('%H:%M:%S', time.gmtime(remaining_time))}")

        time.sleep(random.uniform(2, 5))

    if not stop_flag:
        save_to_excel(extracted_data_list)
        new_print("작업 완료.", level="SUCCESS")
        flash_window(root)
        messagebox.showinfo("알림", "작업이 완료되었습니다.")
        stop_flash_window(root)  # 메시지박스 확인 후 깜빡임 중지


flashing = True  # 깜빡임 상태를 관리하는 플래그

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

file_path = None

def save_to_excel(data):
    global file_path
    if file_path:
        # 기존 엑셀 파일 불러오기
        df = pd.read_excel(file_path, sheet_name=0)

        # B열에 결과값 추가
        df['최신 업데이트 일'] = data

        # 동일한 파일에 덮어쓰기
        df.to_excel(file_path, index=False)

        new_print(f"Data saved to {file_path}", level="INFO")
    else:
        new_print("No file selected for saving.", level="WARNING")


def on_drop(event):
    global url_list, file_path  # url_list와 file_path 변수를 전역으로 선언
    file_path = event.data.strip('{}')
    url_list = read_excel_file(file_path)
    update_log(url_list)
    check_list_and_toggle_button()  # 리스트 상태 확인 및 버튼 활성화

def browse_file():
    global url_list, file_path  # url_list와 file_path 변수를 전역으로 선언
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if file_path:
        url_list = read_excel_file(file_path)
        update_log(url_list)
        check_list_and_toggle_button()  # 리스트 상태 확인 및 버튼 활성화

def toggle_start_stop():
    if not url_list:
        messagebox.showwarning("경고", "목록을 찾을 수 없습니다.")
        return

    if start_button.config('text')[-1] == '시작':
        start_button.config(text="중지", bg="red", fg="white")
        threading.Thread(target=start_processing).start()
    else:
        stop_processing()

def stop_processing():
    global stop_flag, url_list
    stop_flag = True
    url_list = []  # 배열 초기화
    start_button.config(text="시작", bg="#d0f0c0", fg="black", state=tk.DISABLED)

def check_list_and_toggle_button():
    if url_list:
        start_button.config(state=tk.NORMAL)
    else:
        start_button.config(state=tk.DISABLED)


def main():
    global log_text_widget, start_button, progress, progress_label, eta_label, root


    root = TkinterDnD.Tk()
    root.title("유튜브 데이터 수집 프로그램")
    root.geometry("600x600")

    font_large = font.Font(size=10)

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



if __name__ == "__main__":
    main()
