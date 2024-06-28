import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import threading

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")

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

def newPrint(text):
    print(f"{get_current_time()} - {text}")

def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

def fetch_total_pages(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    driver.get(url)

    try:
        time.sleep(2)
        total_pages_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'c-page__total'))
        )
        total_pages_text = total_pages_element.text
        print(f"Total pages text: {total_pages_text}")
        return total_pages_text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def fetch_deal_srl_values(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    driver.get(url)
    time.sleep(2)
    try:
        deallist_wrap = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'deallist_wrap'))
        )
        ul_element = deallist_wrap.find_element(By.CLASS_NAME, 'list')
        li_elements = ul_element.find_elements(By.CLASS_NAME, 'item')

        deal_srl_values = []
        for li in li_elements:
            try:
                a_tag = WebDriverWait(li, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'a'))
                )
                deal_srl = a_tag.get_attribute('data-deal-srl')
                if deal_srl:
                    deal_srl_values.append(deal_srl)
            except Exception as e:
                print(f"Error retrieving data-deal-srl for an item: {e}")

        return deal_srl_values

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def fetch_product_details(driver, product_id):
    url = f"https://www.tmon.co.kr/deal/{product_id}"
    driver.get(url)

    print(f"product_id : {product_id}")
    print(f"url : {url}")

    seller_info = {"상호": "", "e-mail": ""}

    time.sleep(2)

    try:
        tab_inner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab-inner._fixedUIItem'))
        )

        tab_navigation = tab_inner.find_element(By.CLASS_NAME, 'tab-navigation')
        li_elements = tab_navigation.find_elements(By.TAG_NAME, 'li')
        if len(li_elements) >= 4:
            li_elements[3].click()
        else:
            print("li 태그가 4개 이상 존재하지 않습니다.")
            return

        time.sleep(3)

        toggle_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'toggle.tit_align_top'))
        )

        print(f"len {len(toggle_elements)}")

        toggle_elements_len = len(toggle_elements)

        if toggle_elements_len == 7:
            toggle_elements[4].click()
        elif toggle_elements_len == 4:
            toggle_elements[1].click()
        else:
            print("toggle.tit_align_top 요소가 4개 이상 존재하지 않습니다.")
            return

        time.sleep(3)

        slide_ct_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ct.slide-ct'))
        )

        print(f"len slide_ct_elements : {len(slide_ct_elements)}")

        if len(slide_ct_elements) >= 7:
            slide_ct = slide_ct_elements[4]
        elif len(slide_ct_elements) >= 4:
            slide_ct = slide_ct_elements[1]
        else:
            print("ct.slide-ct 요소가 2개 이상 존재하지 않습니다.")
            return

        table = WebDriverWait(slide_ct, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tbl_info'))
        )
        th_elements = table.find_elements(By.TAG_NAME, 'th')
        for th in th_elements:
            if '상호명' in th.text:
                td = th.find_element(By.XPATH, './following-sibling::td')
                seller_info['상호'] = td.text
            elif '이메일' in th.text:
                td = th.find_element(By.XPATH, './following-sibling::td')
                seller_info['e-mail'] = td.text

    except Exception as e:
        print(f"An error occurred: {e}")

    return seller_info

def start_timon_scraping():

    selected_companies = [company for company, var in company_vars.items() if var.get() == 1]
    log_main.insert(tk.END, f"{get_current_time()} - Selected companies for scraping: {selected_companies}\n")
    log_main.see(tk.END)

    if "티몬" in selected_companies:
        kwd = keyword_entry.get()

        newPrint("티몬 시작...")

        driver = setup_driver()
        total_pages_text = fetch_total_pages(driver, kwd, 1)
        total_page = int(total_pages_text) if total_pages_text else 1

        all_deal_srl_values = set()
        for page in range(1, total_page + 1):
            deal_srl_values = fetch_deal_srl_values(driver, kwd, page)
            all_deal_srl_values.update(deal_srl_values)

        all_seller_info = []

        for product_id in all_deal_srl_values:
            seller_info = fetch_product_details(driver, product_id)
            seller_info["키워드"] = kwd
            seller_info["플랫폼"] = "티몬"
            all_seller_info.append(seller_info)
            update_log("티몬", f"Collected data for product ID {product_id}")

        columns = ['키워드', '상호', 'e-mail', '플랫폼', 'url']
        df = pd.DataFrame(all_seller_info, columns=columns)
        df.to_excel('seller_info.xlsx', index=False)

        driver.quit()

    log_main.insert(tk.END, f"{get_current_time()} - Scraping completed\n")
    log_main.see(tk.END)

def update_log(company, message):
    log_widgets[company].insert(tk.END, message + "\n")
    log_widgets[company].see(tk.END)

def toggle_company_frame(company, state):
    if state:
        company_frames[company].config(bg="darkgray")
        for widget in company_frames[company].winfo_children():
            if isinstance(widget, tk.Text):
                widget.config(state="normal", bg="lightgray")
            elif isinstance(widget, ttk.Progressbar):
                widget.state(['!disabled'])
            else:
                widget.config(state="normal")
    else:
        company_frames[company].config(bg="lightgray")
        for widget in company_frames[company].winfo_children():
            if isinstance(widget, tk.Text):
                widget.config(state="disabled", bg="darkgray")
            elif isinstance(widget, ttk.Progressbar):
                widget.state(['disabled'])
            else:
                widget.config(state="disabled")

def on_checkbox_change():
    for company, var in company_vars.items():
        state = var.get()
        toggle_company_frame(company, state)

def update_time():
    current_time = datetime.now().strftime("현재시각 : %Y-%m-%d %H:%M:%S")
    time_label.config(text=current_time)
    root.after(1000, update_time)

import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime

def toggle_company_frame(company, state):
    if state:
        company_frames[company].config(bg="darkgray")
        for widget in company_frames[company].winfo_children():
            if isinstance(widget, tk.Text):
                widget.config(state="normal", bg="white")
            elif isinstance(widget, ttk.Progressbar):
                widget.state(['!disabled'])
            else:
                widget.config(state="normal")
    else:
        company_frames[company].config(bg="lightgray")
        for widget in company_frames[company].winfo_children():
            if isinstance(widget, tk.Text):
                widget.config(state="normal", bg="white")
            elif isinstance(widget, ttk.Progressbar):
                widget.state(['disabled'])
            else:
                widget.config(state="disabled")

def on_checkbox_change():
    for company, var in company_vars.items():
        state = var.get()
        toggle_company_frame(company, state)

def update_time():
    current_time = datetime.now().strftime("현재시각 : %Y-%m-%d %H:%M:%S")
    time_label.config(text=current_time)
    root.after(1000, update_time)

def start_scraping():
    start_button.config(text="Cancel Scraping", command=cancel_scraping)
    log_frame.config(bg="gray20")

    for log in log_widgets.values():
        log.config(bg="black")
    log_main.config(bg="black", state=tk.NORMAL)

    # 체크된 값들을 수집하고 출력
    checked_companies = [company for company, var in company_vars.items() if var.get() == 1]
    print("Checked companies:", checked_companies)

    # 텍스트를 흰색으로 설정하는 태그 추가
    log_main.tag_configure("white_text", foreground="white")

    log_main.insert(tk.END, f"Checked companies: {checked_companies}\n", "white_text")
    log_main.insert(tk.END, "Scraping started...\n", "white_text")
    log_main.see(tk.END)
    log_main.config(state=tk.DISABLED)

def cancel_scraping():
    log_main.config(state=tk.NORMAL)
    log_main.insert(tk.END, "Scraping cancelled.\n")
    log_main.see(tk.END)
    log_main.config(state=tk.DISABLED)

    print("Scraping cancelled.")
    start_button.config(text="Start Scraping", command=lambda: threading.Thread(target=start_scraping).start())
    log_frame.config(bg="gray80")
    for log in log_widgets.values():
        log.config(bg="white")
    log_main.config(bg="white")

root = tk.Tk()
root.title("Data Scraping GUI")

# 전체 배경색 설정
root.configure(bg="gray80")

# 화면 크기 조정
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 2 / 3) + 200  # 너비를 5cm(약 200 픽셀) 증가
window_height = int(screen_height * 2 / 3) + 100  # 높이를 100픽셀 증가
root.geometry(f"{window_width}x{window_height}")

entry_frame = tk.Frame(root, bg="gray80")
entry_frame.pack(pady=10)
time_label = tk.Label(entry_frame, text="", bg="gray80")
time_label.pack(side=tk.TOP, padx=5)
entry_label = tk.Label(entry_frame, text="Enter Keyword:", bg="gray80")
entry_label.pack(side=tk.LEFT, padx=5)
keyword_entry = tk.Entry(entry_frame)
keyword_entry.pack(side=tk.LEFT, padx=5)

checkbox_frame = tk.Frame(root, bg="gray80")
checkbox_frame.pack(pady=10)
company_names = ["티몬", "11번가", "오늘의집", "위메프", "쿠팡", "G마켓"]
company_vars = {}
for company in company_names:
    var = tk.IntVar(value=1)
    chk = tk.Checkbutton(checkbox_frame, text=company, variable=var, command=on_checkbox_change, bg="gray80")
    chk.pack(side=tk.LEFT, padx=5)
    company_vars[company] = var

# log_frame에 스크롤바 추가
log_frame = tk.Frame(root, bg="gray80")
log_frame.pack(pady=10)

scrollbar = tk.Scrollbar(log_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_main = tk.Text(log_frame, height=4, width=80, state="disabled", bg="white", yscrollcommand=scrollbar.set, padx=5, pady=5)
log_main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=log_main.yview)



start_button = tk.Button(root, text="Start Scraping", command=lambda: threading.Thread(target=start_scraping).start(), bg="white")
start_button.pack(pady=10)

log_widgets = {}
progress_bars = {}
company_frames = {}

# 위젯 배치를 위한 프레임 생성
company_frames_container = tk.Frame(root, bg="gray80")
company_frames_container.pack(pady=10, fill="x")

# 스타일 설정
style = ttk.Style()
style.configure("TProgressbar", troughcolor="white", background="green", thickness=20)

# 박스 배치 함수
def create_box(frame, company):
    box_frame = tk.LabelFrame(frame, text=company, padx=10, pady=10, bg="darkgray", relief=tk.GROOVE)
    company_frames[company] = box_frame

    # 게이지 바
    progress = ttk.Progressbar(box_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    progress.pack(fill="x", pady=5)
    progress_bars[company] = progress

    # 로그 출력
    log_text = tk.Text(box_frame, height=3, width=50, state="disabled", bg="white")
    log_text.pack(fill="both", expand=True)
    log_widgets[company] = log_text

    return box_frame

# 티몬, 11번가, 오늘의집 박스
for i, company in enumerate(company_names[:3]):
    box_frame = create_box(company_frames_container, company)
    box_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

# 위메프, 쿠팡, G마켓 박스
for i, company in enumerate(company_names[3:]):
    box_frame = create_box(company_frames_container, company)
    box_frame.grid(row=1, column=i, padx=10, pady=10, sticky="nsew")

# 통합 박스 (위메프, 쿠팡, G마켓 박스 아래에 위치)
combined_frame = tk.LabelFrame(root, text="전체", padx=10, pady=10, bg="darkgray", relief=tk.GROOVE)
combined_frame.pack(fill="x", padx=10, pady=10)

# 통합 게이지 바
combined_progress = ttk.Progressbar(combined_frame, orient="horizontal", mode="determinate", style="TProgressbar")
combined_progress.pack(fill="x", pady=5)
progress_bars["combined"] = combined_progress

# 통합 로그 출력
combined_log = tk.Text(combined_frame, height=3, width=80, state="disabled", bg="white")
combined_log.pack(fill="both", expand=True)
log_widgets["combined"] = combined_log

# 반응형 그리드 설정
for i in range(3):
    company_frames_container.grid_columnconfigure(i, weight=1)
company_frames_container.grid_rowconfigure(0, weight=1)
company_frames_container.grid_rowconfigure(1, weight=1)

# 현재 시각 업데이트
update_time()

root.mainloop()
