from tkinter import ttk, scrolledtext
from datetime import timedelta
import threading
import tkinter as tk
from .common import setup_driver, get_current_time, fetch_excel
from .tmon import fetch_total_pages, fetch_product_ids, fetch_product_detail

def start_crawling():
    keyword = get_keyword()
    company_count = get_company_count()
    if keyword and company_count:
        new_print(f"Keyword entered: {keyword}")
        new_print(f"Company count entered: {company_count}")
        threading.Thread(target=actual_crawling_function, args=(keyword, company_count)).start()
    else:
        new_print("Please enter both keyword and company count.")

def actual_crawling_function(kwd, company_count):
    new_print(f"Started crawling for keyword: {kwd}")
    initial_page = 1
    company = "티몬"
    new_print("티몬 시작...")
    driver = setup_driver()
    total_pages = fetch_total_pages(driver, kwd, initial_page)
    new_print(f"total_page : {total_pages}")
    product_ids = set()
    new_print("페이지 수집...")
    for page in range(1, total_pages + 1):
        new_print(f"현재 페이지 : {page} / 전체 페이지 {total_pages} ")
        ids = fetch_product_ids(driver, kwd, page)
        product_ids.update(ids)
        update_page_progress(page, total_pages)
    new_print(f"product_ids len : {len(product_ids)}")
    all_seller_info = []
    new_print("크롤링 시작...")
    max_value = min(len(product_ids), int(company_count))
    for index, product_id in enumerate(list(product_ids)[:max_value]):
        seller_info = fetch_product_detail(driver, product_id)
        seller_info["키워드"] = kwd
        seller_info["플랫폼"] = company
        new_print(f"seller_info : {seller_info}")
        all_seller_info.append(seller_info)
        update_progress(index + 1, max_value)
    new_print("엑셀 시작...")
    fetch_excel(all_seller_info)
    new_print("끝...")

def get_keyword():
    return keyword_text.get("1.0", tk.END).strip()

def get_company_count():
    return company_count_text.get("1.0", tk.END).strip()

def update_page_progress(current_page, total_pages):
    page_progress_percentage = (current_page / total_pages) * 100
    page_progress['value'] = page_progress_percentage
    page_progress_label.config(text=f"페이지 진행률: {page_progress_percentage:.2f}%")
    page_index_label.config(text=f"{current_page}/{total_pages}")
    remaining_time = (total_pages - current_page) * 3
    eta = str(timedelta(seconds=remaining_time))
    page_eta_label.config(text=f"남은 시간: {eta}")

def update_progress(current_value, max_value):
    progress_percentage = (current_value / max_value) * 100
    progress['value'] = progress_percentage
    progress_label.config(text=f"진행률: {progress_percentage:.2f}%")
    index_label.config(text=f"{current_value}/{max_value}")
    remaining_time = (max_value - current_value) * 10
    eta = str(timedelta(seconds=remaining_time))
    eta_label.config(text=f"남은 시간: {eta}")

def update_time():
    current_time_label.config(text=f"현재시간: {get_current_time()}")
    root.after(1000, update_time)

def new_print(text):
    print(f"{get_current_time()} - {text}")
    current_time = get_current_time()
    log_text_widget.insert(tk.END, f"{current_time} - {text}\n")
    log_text_widget.see(tk.END)

def start_app():
    global root, keyword_text, company_count_text, current_time_label, log_text_widget
    global page_progress_label, page_index_label, page_eta_label, page_progress
    global progress_label, index_label, eta_label, progress

    root = tk.Tk()
    root.title("크롤링 프로그램")
    root.geometry("800x600")

    current_time_label = tk.Label(root, text=f"현재시간: {get_current_time()}", anchor="w")
    current_time_label.pack(fill=tk.X, padx=10, pady=5)
    update_time()

    keyword_label = tk.Label(root, text="키워드 입력:", anchor="w")
    keyword_label.pack(fill=tk.X, padx=10, pady=5)

    keyword_text = tk.Text(root, height=1, width=50)
    keyword_text.pack(fill=tk.X, padx=10, pady=5)

    company_count_label = tk.Label(root, text="회사 갯수 입력:", anchor="w")
    company_count_label.pack(fill=tk.X, padx=10, pady=5)

    company_count_text = tk.Text(root, height=1, width=50)
    company_count_text.pack(fill=tk.X, padx=10, pady=5)

    start_button = tk.Button(root, text="시작", command=start_crawling)
    start_button.pack(padx=10, pady=10)

    log_label = tk.Label(root, text="로그:", anchor="w")
    log_label.pack(fill=tk.X, padx=10, pady=5)
    log_text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
    log_text_widget.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

    page_progress_label = tk.Label(root, text="페이지 진행률: 0%")
    page_progress_label.pack(fill=tk.X, padx=10)

    page_index_label = tk.Label(root, text="0/0")
    page_index_label.pack(fill=tk.X, padx=10)

    page_eta_label = tk.Label(root, text="남은 시간: 00:00:00")
    page_eta_label.pack(fill=tk.X, padx=10)

    page_progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100)
    page_progress.pack(fill=tk.X, padx=10, pady=10)

    progress_label = tk.Label(root, text="진행률: 0%")
    progress_label.pack(fill=tk.X, padx=10)

    index_label = tk.Label(root, text="0/0")
    index_label.pack(fill=tk.X, padx=10)

    eta_label = tk.Label(root, text="남은 시간: 00:00:00")
    eta_label.pack(fill=tk.X, padx=10)

    progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100)
    progress.pack(fill=tk.X, padx=10, pady=10)

    root.mainloop()
