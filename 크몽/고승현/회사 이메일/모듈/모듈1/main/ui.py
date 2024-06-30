from tkinter import ttk, scrolledtext
from datetime import timedelta
import threading
import tkinter as tk
from tkinter import messagebox
from .common import setup_driver, get_current_time, fetch_excel
from .company.ti import fetch_product_ids as ti_ids, fetch_product_detail as ti_detail
from .company.el import fetch_product_ids as el_ids, fetch_product_detail as el_detail
from .company.gm import fetch_product_ids as gm_ids, fetch_product_detail as gm_detail
from .company.cp import fetch_product_ids as cp_ids, fetch_product_detail as cp_detail
from .company.oh import fetch_product_ids as oh_ids, fetch_product_detail as oh_detail
from .company.we import fetch_product_ids as we_ids, fetch_product_detail as we_detail
import pandas as pd


stop_flag = threading.Event()


def start_crawling():
    if start_button["text"] == "시작":
        keyword = get_keyword()
        email_count = get_email_count()
        init_page = get_init_page()  # 추가된 부분
        end_page = get_end_page()  # 추가된 부분
        if keyword and email_count and init_page is not None and end_page is not None:
            new_print(f"키워드 : {keyword}")
            new_print(f"이메일 수 : {email_count}")
            new_print(f"시작 페이지 : {init_page}")  # 추가된 부분
            new_print(f"마지막 페이지 : {end_page}")  # 추가된 부분
            stop_flag.clear()  # 중지 플래그 초기화
            threading.Thread(target=actual_crawling_function, args=(keyword, email_count, init_page, end_page)).start()
            start_button.config(text="중지", fg="green")
        else:
            new_print("Please enter both keyword and company count.")
    else:
        stop_flag.set()  # 중지 플래그 설정
        # 중지 로직 구현
        new_print("크롤링 중지")
        start_button.config(text="시작", fg="black")


def get_init_page():
    try:
        return int(init_page_text.get().strip())
    except ValueError:
        return None


def get_end_page():
    try:
        return int(end_page_text.get().strip())
    except ValueError:
        return None



# 동적으로 함수 호출
def call_company_function(company_name, add_name, driver, kwd, page, product_id):
    # 함수 이름 생성
    function_name = f"{company_name}_{add_name}"

    # 현재 모듈에서 해당 함수 가져오기
    function = globals().get(function_name)

    # 함수가 존재하면 호출, 아니면 에러 메시지 반환
    if function and callable(function):
        return function(driver, kwd, page, product_id)
    else:
        new_print(f"Function {function_name} does not exist")
        return []


def is_stop():
    if stop_flag.is_set():
        new_print("작업 중지됨")
        messagebox.showinfo("작업 중지", "작업이 중지되었습니다.")
        return True
    return False


def unique_seller_list(all_seller_info):

    # pandas DataFrame으로 변환
    df = pd.DataFrame(all_seller_info)

    # '이메일' 컬럼을 기준으로 중복 제거
    df_unique = df.drop_duplicates(subset='이메일')

    # 중복 제거된 데이터를 다시 리스트로 변환
    return df_unique.to_dict(orient='records')


def update_company_label(company_name):
    for company, label in company_labels.items():
        if company == company_name:
            label.config(bg="red", fg="white")
        else:
            label.config(bg="SystemButtonFace", fg="black")


# 실제 크롤링
def actual_crawling_function(kwd, email_count, init_page=1, end_page=10):

    driver = setup_driver()

    all_seller_info = []

    excel_len = 0

    # companies_ids = ["ti", "el", "gm", "cp", "oh", "we"]
    companies_ids = ["oh", "cp"]
    companies_names = {"ti": "티몬", "el": "11번가", "gm": "G마켓", "cp": "쿠팡", "oh": "오늘의집", "we": "위메프"}

    for page in range(init_page, end_page + 1):

        # 중지 플래그 확인
        if is_stop():
            fetch_excel(all_seller_info, kwd)
            return

        # companies에 값이 없으면 중단.
        if len(companies_ids) == 0:
            break

        # 티몬 -> 11번가 -> G마켓 -> 쿠팡 -> 오늘의집 -> 위메프
        for company in companies_ids:

            if is_stop():
                fetch_excel(all_seller_info, kwd)
                return

            update_company_label(company)

            new_print(f"{companies_names[company]} 시작 Page {page}")

            pr_ids = call_company_function(company, "ids", driver, kwd, page, "")
            new_print(f"{companies_names[company]} Page [{page}] 조회한 품목수 : {len(pr_ids)} 개")
            new_print(f"{companies_names[company]} Page [{page}] 조회한 품목 : {pr_ids}")

            # 데이터가 없으므로 회사 배열에서 삭제
            if len(pr_ids) == 0:
                companies_ids.remove(company)

            for index, product_id in enumerate(pr_ids):
                if is_stop():
                    fetch_excel(all_seller_info, kwd)
                    return

                # 상세조회
                seller_info = call_company_function(company, "detail", driver, kwd, page, product_id)

                if seller_info['이메일']:

                    new_print(f"{companies_names[company]} Page [{page}], 번호: {index + 1}, 상호명 : {seller_info['상호명']}, 이메일 : {seller_info['이메일']}")

                    all_seller_info.append(seller_info)
                    # 전체 중복 제거
                    all_seller_info = unique_seller_list(all_seller_info)

                    new_print(f"중복 제거 후 전체 진행된 갯수 : {len(all_seller_info)}")

                    # 현재까지 합이 100인지 체크
                    if(len(all_seller_info) % 100 == 0 and excel_len != len(all_seller_info)):
                        excel_len = len(all_seller_info)
                        new_print(f"100의 배수 {len(all_seller_info)} 입니다. 현재 까지 데이터를 엑셀에 저장 하겠습니다.")
                        fetch_excel(all_seller_info, kwd)

                    # 게이지 변경
                    update_progress(len(all_seller_info), email_count, page, end_page)

                    # 현재까지 합이 company_count 보다 큰지 체크
                    if len(all_seller_info) >= email_count:
                        new_print("엑셀 시작...")
                        fetch_excel(all_seller_info, kwd)
                        new_print("끝...")
                        start_button.config(text="시작", fg="black")
                        messagebox.showinfo("작업 완료", "작업이 종료되었습니다.")
                        return


def get_keyword():
    return keyword_text.get().strip()


def get_email_count():
    return int(email_count_text.get().strip())


def update_progress(current_value, max_value, page, end_page):
    progress_percentage = (current_value / max_value) * 100
    progress['value'] = progress_percentage
    progress_label.config(text=f"진행률: {progress_percentage:.2f}%")
    index_label.config(text=f"{current_value}/{max_value}")
    current_page_label.config(text=f"현재 페이지: {page}/{end_page}")
    remaining_time = (max_value - current_value) * 10
    eta = str(timedelta(seconds=remaining_time))
    # eta_label.config(text=f"남은 시간: {eta}")


def update_time():
    current_time_label.config(text=f"현재시간 : {get_current_time()}")
    root.after(1000, update_time)


def new_print(text):
    print(f"{get_current_time()} - {text}")
    current_time = get_current_time()
    log_text_widget.insert(tk.END, f"{current_time} - {text}\n")
    log_text_widget.see(tk.END)


def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return "break"


def start_button_click(event=None):
    start_button.invoke()


def start_app():
    global root, keyword_text, email_count_text, current_time_label, log_text_widget
    global progress_label, index_label, eta_label, progress, start_button, init_page_text, end_page_text, current_page_label
    global company_labels

    root = tk.Tk()

    # ========== 프로그램 이름 ==========
    root.title("크롤링 프로그램")
    root.geometry("800x600")

    # ========== 현재시간 맨 위 라벨 ==========
    current_time_label = tk.Label(root, text=f"현재시간 : {get_current_time()}", anchor="w")
    current_time_label.pack(fill=tk.X, padx=10, pady=5)
    update_time()

    # ========== 입력 frame [시작] ==========
    # 입력 frame 키워드입력, 회사 갯수 입력, 시작 버튼
    input_frame = tk.Frame(root)
    input_frame.pack(fill=tk.X, padx=10, pady=5)

    # 키워드 입력 Label
    keyword_label = tk.Label(input_frame, text="키워드:", anchor="w")
    # w: 서쪽 (왼쪽) 텍스트 방향
    keyword_label.grid(row=0, column=0, padx=5)

    # 키워드 입력 Input
    keyword_text = tk.Entry(input_frame, width=20)
    keyword_text.grid(row=0, column=1, padx=5)
    keyword_text.bind("<Return>", start_button_click)

    # 회사 갯수 입력
    company_count_label = tk.Label(input_frame, text="이메일 수:", anchor="w")
    company_count_label.grid(row=0, column=2, padx=5)

    # 이메일 갯수 입력 input
    email_count_text = tk.Entry(input_frame, width=10)
    email_count_text.grid(row=0, column=3, padx=5)
    email_count_text.insert(0, "500")  # 초기값 설정
    email_count_text.bind("<Return>", start_button_click)

    # 시작 페이지
    init_page_label = tk.Label(input_frame, text="시작 페이지:", anchor="w")
    init_page_label.grid(row=0, column=4, padx=5)

    # 시작 페이지 input
    init_page_text = tk.Entry(input_frame, width=6)
    init_page_text.grid(row=0, column=5, padx=5)
    init_page_text.insert(0, "1")  # 초기값 설정
    init_page_text.bind("<Return>", start_button_click)

    # 마지막 페이지
    end_page_label = tk.Label(input_frame, text="마지막 페이지:", anchor="w")
    end_page_label.grid(row=0, column=6, padx=5)

    # 마지막 페이지 input
    end_page_text = tk.Entry(input_frame, width=6)
    end_page_text.grid(row=0, column=7, padx=5)
    end_page_text.insert(0, "10")  # 초기값 설정
    end_page_text.bind("<Return>", start_button_click)

    # 시작 버튼
    start_button = tk.Button(input_frame, text="시작", command=start_crawling)
    start_button.grid(row=0, column=8, padx=5)
    start_button.bind("<Return>", start_button_click)
    # ========== 입력 frame [끝] ==========


    # ========== 회사 순서 레이블 [시작] ==========
    order_frame = tk.Frame(root)
    order_frame.pack(fill=tk.X, padx=10, pady=5)

    tk.Label(order_frame, text="순서:").pack(side=tk.LEFT, padx=5)

    companies = {"ti": "티몬", "el": "11번가", "gm": "G마켓", "cp": "쿠팡", "oh": "오늘의집", "we": "위메프"}
    company_labels = {}

    for company, name in companies.items():
        label = tk.Label(order_frame, text=name, padx=5, pady=2, borderwidth=2, relief="groove")
        label.config(bg="green", fg="white")
        label.pack(side=tk.LEFT, padx=5)
        company_labels[company] = label
    # ========== 회사 순서 레이블 [끝] ==========


    # ========== 로그 [시작] ==========
    # 로그 라벨
    log_label = tk.Label(root, text="로그:", anchor="w")
    log_label.pack(fill=tk.X, padx=15, pady=5)

    # 로그 화면 창
    log_text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
    #wrap=tk.WORD는 텍스트가 창의 너비를 초과할 경우 단어 단위로 줄 바꿈을 한다는 의미입니다. 이는 텍스트가 중간 단어에서 잘리지 않고, 전체 단어가 다음 줄로 넘어가도록 합니다.
    log_text_widget.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
    # fill=tk.BOTH는 위젯이 부모 컨테이너의 가로 및 세로 방향으로 모두 확장되도록 합니다.
    # expand=True는 부모 컨테이너가 크기를 조정할 때 위젯이 추가 공간을 차지하도록 합니다. 이 설정을 통해 윈도우가 확장되면 텍스트 위젯도 함께 확장됩니다.
    # ========== 로그 [끝] ==========


    # ========== 진행률 [시작] ==========
    current_page_label = tk.Label(root, text="페이지: 0/0")
    current_page_label.pack(fill=tk.X, padx=10)

    progress_label = tk.Label(root, text="진행률: 0%")
    progress_label.pack(fill=tk.X, padx=10)

    index_label = tk.Label(root, text="0/0")
    index_label.pack(fill=tk.X, padx=10)

    # eta_label = tk.Label(root, text="남은 시간: 00:00:00")
    # eta_label.pack(fill=tk.X, padx=10)

    progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100)
    progress.pack(fill=tk.X, padx=10, pady=10)
    # ========== 진행률 [끝] ==========

    root.mainloop()