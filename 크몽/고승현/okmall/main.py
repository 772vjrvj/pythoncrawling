import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
from tkinter import filedialog, font, messagebox
import time
import random
import threading
import requests
from tkinter import ttk  # 진행률 표시를 위한 모듈 추가
import ctypes
from bs4 import BeautifulSoup

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


def fetch_product(url, headers):
    # 요청 헤더 설정
    # headers = {
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "Accept-Encoding": "gzip, deflate, br, zstd",
    #     "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    #     "Cache-Control": "max-age=0",
    #     "Connection": "keep-alive",
    #     "Host": "www.okmall.com",
    #     "Sec-CH-UA": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    #     "Sec-CH-UA-Mobile": "?0",
    #     "Sec-CH-UA-Platform": "\"Windows\"",
    #     "Sec-Fetch-Dest": "document",
    #     "Sec-Fetch-Mode": "navigate",
    #     "Sec-Fetch-Site": "cross-site",
    #     "Sec-Fetch-User": "?1",
    #     "Upgrade-Insecure-Requests": "1",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    # }

    try:
        # GET 요청 보내기
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
    except requests.RequestException as e:
        print(f"요청 오류 발생: {e}")
        return None

    # 기본 객체 초기화
    obj = {
        '상품링크': url,
        '브랜드': '',
        '상품명': '',
        '가격': '',
        '택 사이즈': []
    }

    # BeautifulSoup을 사용해 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # 상품명 가져오기
    product_name_element = soup.find(id="ProductNameArea")
    if product_name_element:
        product_name = product_name_element.find(class_="prd_name")
        if product_name:
            obj['상품명'] = product_name.get_text(strip=True)

    # 브랜드 정보 가져오기
    brand_img_box = soup.find(class_="brand_img_box")
    if brand_img_box:
        brand_tit = brand_img_box.find(class_="brand_tit")
        if brand_tit:
            obj['브랜드'] = brand_tit.get_text(strip=True)

    # 가격 정보 가져오기
    real_price = soup.find(class_="real_price")
    if real_price:
        price = real_price.find(class_="price")
        if price:
            obj['가격'] = ''.join(price.find_all(string=True)).strip()

    # 택 사이즈 정보 가져오기
    product_opt_list = soup.find(id="ProductOPTList")
    if product_opt_list:
        table = product_opt_list.find("table", class_="shoes_size")
        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) > 1:  # 두 번째 <td>가 있는지 확인
                        size_text = cols[1].get_text(strip=True)
                        obj['택 사이즈'].append(size_text)

    # obj를 반환
    return obj


def start_processing():
    global stop_flag, extracted_data_list, root
    stop_flag = False
    log_text_widget.delete(1.0, tk.END)  # 기존 로그 화면 초기화
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    extracted_data_list = []
    total_urls = len(url_list)
    progress["maximum"] = total_urls

    for index, url in enumerate(url_list):
        if stop_flag:
            break
        try:
            extracted_data = fetch_product(url, headers)
            extracted_data_list.append(extracted_data)

            new_print(extracted_data, level="DATA")
        except Exception as e:
            new_print(f"WARN processing {url}: {str(e)}", level="WARN")
            extracted_data = {
                '상품링크': url,
                '브랜드': '',
                '상품명': '',
                '가격': '',
                '택 사이즈': []
            }
            extracted_data_list.append(extracted_data)
            new_print(extracted_data, level="WARN")

        # 진행률 업데이트
        progress["value"] = index + 1
        progress_label.config(text=f"진행률: {int((index + 1) / total_urls * 100)}%")

        remaining_time = (total_urls - (index + 1)) * 2.5  # 남은 URL 개수 * 2초
        eta_label.config(text=f"남은 시간: {time.strftime('%H:%M:%S', time.gmtime(remaining_time))}")

        time.sleep(random.uniform(2, 3))

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


def save_to_excel(data):
    df = pd.DataFrame(data)

    # 현재 시간 가져오기
    current_time = time.strftime("%Y%m%d_%H%M%S")
    filename = f"OKMall 데이터_{current_time}.xlsx"

    df.to_excel(filename, index=False)
    new_print(f"Data saved to {filename}", level="INFO")


def on_drop(event):
    global url_list  # url_list 변수를 전역으로 선언
    filepath = event.data.strip('{}')
    url_list = read_excel_file(filepath)
    update_log(url_list)
    check_list_and_toggle_button()  # 리스트 상태 확인 및 버튼 활성화


def browse_file():
    global url_list  # url_list 변수를 전역으로 선언
    filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if filepath:
        url_list = read_excel_file(filepath)
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
    root.title("OKmall 데이터 수집 프로그램")
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
