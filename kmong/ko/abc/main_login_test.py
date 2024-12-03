import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
from tkinter import filedialog, font, messagebox
import time
import random
import threading
import requests
from datetime import datetime
import os
from tkinter import ttk  # 진행률 표시를 위한 모듈 추가

url_list = []
extracted_data_list = []  # 모든 데이터 저장용
stop_flag = False  # 중지를 위한 플래그
# 세션 ID를 저장할 전역 변수
session_id = None

# 전역 변수에 로그인된 사용자 정보 저장
logged_in_user_id = None
logged_in_user_pw = None

def renew_session(saved_session_id):
    url = 'http://localhost:8080/user/renew-session'
    headers = {
        'Content-Type': 'application/json',
        'Cookie': 'JSESSIONID=' + saved_session_id  # 기존 세션 ID를 쿠키로 전송

    }
    data = {
        'sessionId': saved_session_id  # 현재 세션 ID를 JSON으로 전송
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        json_data = response.json()
        if json_data and json_data["status"] == 'SUCCESS':
            print("Session successfully renewed. New session ID:", json_data["sessionId"])
            return json_data["sessionId"]  # 새로운 세션 ID 저장
        else:
            print("Failed to renew session.")
            return None
    except Exception as e:
        print("Error renewing session:", str(e))
        return None


def attempt_login():
    global logged_in_user_id, logged_in_user_pw, session_id

    usrId = usrId_entry.get()
    usrPw = usrPw_entry.get()

    # 로그인 성공 시 전역 변수에 아이디와 비밀번호 저장
    url = 'http://localhost:8080/user/login'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'usrId': usrId,
        'usrPw': usrPw,
        'isProgram': 'true'
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        json_data = response.json()
        if json_data and json_data["status"] == 'SUCCESS':
            logged_in_user_id = usrId
            logged_in_user_pw = usrPw
            # 로그인 성공 시 메인 애플리케이션 실행
            session_id = response.cookies.get('JSESSIONID')
            if session_id:
                login_window.destroy()
                print("로그인 성공")
                print(f"session_id : {session_id}")
                main_application()
            else:
                messagebox.showerror("로그인 실패", "세션 ID를 가져오지 못했습니다.")
        else:
            messagebox.showerror("로그인 실패", "로그인 정보가 잘못되었습니다.")
    except Exception as e:
        log = f"session_id {session_id}"
        messagebox.showerror(log)


def login():
    global usrId_entry, usrPw_entry, login_window

    login_window = tk.Tk()
    login_window.title("로그인")
    login_window.geometry("300x200")

    tk.Label(login_window, text="아이디").pack(pady=10)
    usrId_entry = tk.Entry(login_window)
    usrId_entry.pack(pady=5)

    tk.Label(login_window, text="비밀번호").pack(pady=10)
    usrPw_entry = tk.Entry(login_window, show="*")
    usrPw_entry.pack(pady=5)

    login_button = tk.Button(login_window, text="로그인", command=attempt_login)
    login_button.pack(pady=20)

    login_window.mainloop()


def attempt_password_update():
    global session_id
    print(f"session_id : {session_id}")
    if not session_id:
        messagebox.showerror("오류", "로그인이 필요합니다.")
        return

    usrId = usrId_entry.get()
    currentPassword = current_pw_entry.get()
    newPassword = new_pw_entry.get()
    newPasswordConfirm = confirm_pw_entry.get()

    if newPassword != newPasswordConfirm:
        messagebox.showerror("오류", "새 비밀번호가 일치하지 않습니다.")
        return

    url = 'http://localhost:8080/user/update/password'
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'usrId': usrId,
        'currentPassword': currentPassword,
        'newPassword': newPassword
    }

    try:
        response = requests.post(url, headers=headers, json=data, cookies={'JSESSIONID': session_id})
        response.raise_for_status()
        json_data = response.json()
        if json_data.get("result") == "success":
            messagebox.showinfo("성공", "비밀번호가 성공적으로 변경되었습니다.")
            password_window.destroy()
        else:
            messagebox.showerror("오류", json_data.get("msg"))
    except Exception as e:
        messagebox.showerror("오류", str(e))


def update_password():
    global usrId_entry, current_pw_entry, new_pw_entry, confirm_pw_entry, password_window, session_id

    password_window = tk.Tk()
    password_window.title("비밀번호 변경")
    password_window.geometry("300x400")

    # 아이디와 현재 비밀번호를 자동으로 채워줌
    tk.Label(password_window, text="아이디").pack(pady=10)
    usrId_entry = tk.Entry(password_window)
    usrId_entry.pack(pady=5)
    usrId_entry.insert(0, logged_in_user_id)  # 아이디 자동 입력

    tk.Label(password_window, text="현재 비밀번호").pack(pady=10)
    current_pw_entry = tk.Entry(password_window, show="*")
    current_pw_entry.pack(pady=5)
    current_pw_entry.insert(0, logged_in_user_pw)  # 현재 비밀번호 자동 입력

    tk.Label(password_window, text="새 비밀번호").pack(pady=10)
    new_pw_entry = tk.Entry(password_window, show="*")
    new_pw_entry.pack(pady=5)

    tk.Label(password_window, text="새 비밀번호 확인").pack(pady=10)
    confirm_pw_entry = tk.Entry(password_window, show="*")
    confirm_pw_entry.pack(pady=5)

    update_button = tk.Button(password_window, text="비밀번호 변경", command=attempt_password_update)
    update_button.pack(pady=20)

    password_window.mainloop()


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


def start_processing():
    global stop_flag, extracted_data_list, session_id
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

    current_date = datetime.now().strftime("%Y-%m-%d")  # 현재 날짜 가져오기
    extracted_data_list = []
    total_urls = len(url_list)
    progress["maximum"] = total_urls
    start_time = time.time()

    for index, url in enumerate(url_list):
        if stop_flag:
            break

        # 세션 갱신 처리
        if index % 10 == 0:
            new_session_id = renew_session(session_id)
            if new_session_id is None:
                stop_flag = True
                messagebox.showerror("중복 로그인", "중복 로그인이 발생하여 작업이 중지되었습니다.")
                break
            else:
                session_id = new_session_id

        try:
            # prdtNo 값을 추출
            prdtNo = extract_prdtNo(url)
            if prdtNo:
                # URL에 따라 request_url 분기
                if "abcmart" in url:
                    request_url = f"https://abcmart.a-rt.com/product/info?prdtNo={prdtNo}"
                    Retailer = "ABC-MART"
                elif "grandstage" in url:
                    request_url = f"https://grandstage.a-rt.com/product/info?prdtNo={prdtNo}"
                    Retailer = "GRAND STAGE"
                else:
                    new_print(f"Unsupported URL: {url}", level="ERROR")
                    continue

                new_print(f"Requesting URL: {request_url}")

                # 요청을 보내고 JSON 응답 받기
                response = requests.get(request_url, headers=headers)
                response.raise_for_status()  # 요청 오류가 있으면 예외 발생
                json_data = response.json()

                # 품절된 옵션과 구매 가능한 옵션을 분리
                sold_out_options = []
                available_options = []
                total_stock_qty = 0

                for option in json_data.get("productOption", []):
                    optnName = option.get("optnName")
                    totalStockQty = option.get("totalStockQty", 0)
                    if totalStockQty == 0:
                        sold_out_options.append(optnName)
                    else:
                        available_options.append(optnName)
                    total_stock_qty += totalStockQty

                # 상품상태 결정
                product_status = "품절" if total_stock_qty == 0 else "정상"

                # 판매가 포맷 설정
                sellAmt = json_data.get("productPrice", {}).get("sellAmt")
                if sellAmt is not None:
                    sellAmt = f"{sellAmt:,}"

                # 빈 배열일 경우 공백으로 설정
                if not sold_out_options:
                    sold_out_options = ""
                if not available_options:
                    available_options = ""

                # 원하는 값을 추출하여 객체로 구성
                extracted_data = {
                    "상품명": json_data.get("prdtName"),
                    "상품 상태": product_status,
                    "브랜드": json_data.get("brand", {}).get("brandName"),
                    "상품상세url": url,
                    "구매 가능한 옵션": available_options,
                    "품절된 옵션": sold_out_options,
                    "최초수집일": current_date,
                    "스타일코드": json_data.get("styleInfo"),
                    "판매가": sellAmt,
                    "색상코드": json_data.get("prdtColorInfo"),
                    "판매처": Retailer
                }

                extracted_data_list.append(extracted_data)

                new_print(extracted_data, level="DATA")
            else:
                new_print(f"Invalid URL or prdtNo not found: {url}", level="ERROR")
        except Exception as e:
            new_print(f"WARN processing {url}: {str(e)}", level="WARN")
            extracted_data = {
                "상품명": "",
                "상품 상태": "판매 종료",
                "브랜드": "",
                "상품상세url": url,
                "구매 가능한 옵션": "",
                "품절된 옵션": "",
                "수집일": current_date,
                "스타일코드": "",
                "판매가": "",
                "색상코드": "",
                "판매처": ""
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


def save_to_excel(data):
    df = pd.DataFrame(data)
    filename = "ABC마트 데이터.xlsx"
    if os.path.exists(filename):
        i = 1
        while os.path.exists(f"ABC마트 데이터 ({i}).xlsx"):
            i += 1
        filename = f"ABC마트 데이터 ({i}).xlsx"

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


def main_application():
    global log_text_widget, start_button, progress, progress_label, eta_label

    root = TkinterDnD.Tk()
    root.title("ABC마트 데이터 수집 프로그램")
    root.geometry("600x600")

    font_large = font.Font(size=10)

    # 비밀번호 변경 버튼 추가
    password_change_button = tk.Button(root, text="비밀번호 변경", command=update_password, font=font_large, width=15)
    password_change_button.pack(pady=10, anchor='ne')

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
    login()
