import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import pandas as pd
import random

stop_flag = threading.Event()

# 매물유형과 구이름 설정
property_types = {
    "아파트": "APT",
    "오피스텔": "OPST",
    "빌라": "VL",
    "아파트분양권": "ABYG",
    "오피스텔분양권": "OBYG",
    "재건축": "JGC",
    "상가": "SG",
    "사무실": "SMS"
}

districts = {
    "강남구": "https://m.land.naver.com/map/37.517408:127.047313:12:1168000000/{property_type}/A1:B1:B2",
    "송파구": "https://m.land.naver.com/map/37.514592:127.105863:12:1171000000/{property_type}/A1:B1:B2",
    "서초구": "https://m.land.naver.com/map/37.483564:127.032594:12:1165000000/{property_type}/A1:B1:B2",
    "용산구": "https://m.land.naver.com/map/37.538825:126.96535:12:1117000000/{property_type}/A1:B1:B2",
    "성동구": "https://m.land.naver.com/map/37.563475:127.036838:12:1120000000/{property_type}/A1:B1:B2",
    "영등포구": "https://m.land.naver.com/map/37.526367:126.896213:12:1156000000/{property_type}/A1:B1:B2",
}

# 각 구별 URL 템플릿
district_url_templates = {
    "강남구": "https://m.land.naver.com/cluster/ajax/articleList?rletTpCd={rletTpCd}&tradTpCd=A1%3AB1%3AB2&z=12&lat=37.517408&lon=127.047313&btm=37.4257185&lft=126.7865594&top=37.608985&rgt=127.3080666&showR0=&cortarNo=1168000000&sort=rank&page={page}",
    "송파구": "https://m.land.naver.com/cluster/ajax/articleList?rletTpCd={rletTpCd}&tradTpCd=A1%3AB1%3AB2&z=12&lat=37.514592&lon=127.105863&btm=37.4228991&lft=126.8451094&top=37.6061724&rgt=127.3666166&showR0=&cortarNo=1171000000&sort=rank&page={page}",
    "서초구": "https://m.land.naver.com/cluster/ajax/articleList?rletTpCd={rletTpCd}&tradTpCd=A1%3AB1%3AB2&z=12&lat=37.483564&lon=127.032594&btm=37.391833&lft=126.7718404&top=37.5751825&rgt=127.2933476&showR0=&cortarNo=1165000000&sort=rank&page={page}",
    "용산구": "https://m.land.naver.com/cluster/ajax/articleList?rletTpCd={rletTpCd}&tradTpCd=A1%3AB1%3AB2&z=12&lat=37.538825&lon=126.96535&btm=37.4471618&lft=126.7045964&top=37.6303756&rgt=127.2261036&showR0=&cortarNo=1117000000&sort=rank&page={page}",
    "성동구": "https://m.land.naver.com/cluster/ajax/articleList?rletTpCd={rletTpCd}&tradTpCd=A1%3AB1%3AB2&z=12&lat=37.563475&lon=127.036838&btm=37.4718421&lft=126.7760844&top=37.6549953&rgt=127.2975916&showR0=&cortarNo=1120000000&sort=rank&page={page}",
    "영등포구": "https://m.land.naver.com/cluster/ajax/articleList?rletTpCd={rletTpCd}&tradTpCd=A1%3AB1%3AB2&z=12&lat=37.526367&lon=126.896213&btm=37.4346885&lft=126.6354594&top=37.617933&rgt=127.1569666&showR0=&cortarNo=1156000000&sort=rank&page={page}"
}

# 웹드라이버 설정 함수
def setup_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Uncomment if you want to run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--incognito")  # Use incognito mode

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

        driver.maximize_window()  # Maximize the window

        return driver
    except WebDriverException as e:
        new_print(f"Error setting up the WebDriver: {e}")
        return None


def print_article_count(driver, gu_urls):
    total_count = 0
    for gu_url in gu_urls:
        url = gu_url.format(property_type=get_selected_property_types())
        try:
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            btn_option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "btn_option._article"))
            )
            txt_number = WebDriverWait(btn_option, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "txt_number._count"))
            )
            count_str = txt_number.text.replace('+', '').replace(',', '')
            total_count += int(count_str)
        except Exception as e:
            new_print(f"Error while fetching article count for {gu_url}: {e}")
    return total_count


def fetch_article_list(gu, page):
    rletTpCd = get_selected_property_types()
    url_template = district_url_templates[gu].format(rletTpCd=rletTpCd, page=page)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url_template, headers=headers)
    if response.status_code != 200:
        return []

    data = response.json()
    articles = data.get('body', [])
    if not articles:
        return []

    article_numbers = [article['atclNo'] for article in articles]
    new_print(f"구 : {gu}, 페이지 : {page}, 대표목록: {article_numbers}")
    details = fetch_article_details(article_numbers, gu, page)

    return details, article_numbers


def save_to_excel(details, mode='w'):
    file_name = 'real_estate_data.xlsx'
    try:
        if mode == 'a':
            existing_df = pd.read_excel(file_name)
            new_df = pd.DataFrame(details)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(details)
        df.to_excel(file_name, index=False)
    except FileNotFoundError:
        df = pd.DataFrame(details)
        df.to_excel(file_name, index=False)
    new_print(f"엑셀 저장 {file_name}")


def fetch_article_details(article_numbers, gu, page):
    details = []
    url_template = "https://m.land.naver.com/article/getSameAddrArticle?articleNo={}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    new_print(f"구 : {gu}, 페이지 : {page}, 전체목록 수집중 ...")

    for atclNo in article_numbers:
        time.sleep(random.uniform(2, 3))
        response = requests.get(url_template.format(atclNo), headers=headers)
        if response.status_code == 200:
            datas = response.json()
            for data in datas:
                details.append(data['atclNo'])

    new_print(f"구 : {gu}, 페이지 : {page}, 전체목록: {details}")

    return fetch_additional_info(details, gu)


def remove_duplicates(details):
    seen = set()
    unique_details = []
    for detail in details:
        # 물건번호와 URL을 제외한 키들의 튜플 생성
        detail_key = tuple((k, v) for k, v in detail.items() if k not in ("물건번호", "URL"))
        if detail_key not in seen:
            seen.add(detail_key)
            unique_details.append(detail)
    return unique_details


def fetch_additional_info(details, gu):
    base_url = "https://fin.land.naver.com/articles/{}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    results = []

    for idx, atclNo in enumerate(details, start=1):
        if stop_flag.is_set():
            break
        time.sleep(random.uniform(2, 3))
        response = requests.get(base_url.format(atclNo), headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            item = soup.select_one('.ArticleSummary_info-complex__uti3v').text if soup.select_one('.ArticleSummary_info-complex__uti3v') else ""
            item_type = soup.select_one('.ArticleSummary_highlight__zEvdA').text if soup.select_one('.ArticleSummary_highlight__zEvdA') else ""
            representative = soup.select_one('.ArticleAgent_broker-name__IrVqj').text if soup.select_one('.ArticleAgent_broker-name__IrVqj') else ""
            agency = soup.select_one('.ArticleAgent_info-agent__tWe2j').text.replace(representative, '').strip() if soup.select_one('.ArticleAgent_info-agent__tWe2j') else ""
            phone_elements = soup.select('.ArticleAgent_link-telephone__RPK6B')
            phone_numbers = [phone.text for phone in phone_elements]

            # 위치 추출
            location = ""
            location_area = soup.select_one('.ArticleComplexInfo_list-data__mMqCQ')
            if location_area:
                first_li = location_area.find('li')
                if first_li:
                    location_element = first_li.select_one('.DataList_definition__d9KY1 .ArticleComplexInfo_area-data__EAsta')
                    if location_element and location_element.contents:
                        location = location_element.contents[0].strip()

            # 중개소 위치 추출
            agency_location = ""
            agent_area = soup.select_one('.ArticleAgent_area-agent__DV2Nc')
            if agent_area:
                lis = agent_area.find_all('li')
                for li in lis:
                    term_element = li.select_one('.DataList_term__Tks7l')
                    if term_element and term_element.text.strip() == "위치":
                        location_element = li.select_one('.DataList_definition__d9KY1')
                        if location_element:
                            agency_location = location_element.text.strip()
                            break

            # 동 추출
            dong = location.split()[2] if location != "" else ""

            result = {
                "물건번호": atclNo,
                "구": gu,
                "동": dong,
                "물건종류": item_type,
                "물건": item,
                "위치": location,
                "대표자": representative,
                "중개소이름": agency,
                "중개소위치": agency_location
            }

            # Add phone numbers as separate fields
            for i, phone_number in enumerate(phone_numbers, start=1):
                result[f"전화번호 {i}"] = phone_number

            result["URL"] = f"https://fin.land.naver.com/articles/{atclNo}"

            log_message = f"{result}"
            new_print(log_message)

            results.append(result)

    return remove_duplicates(results)


def start_crawling():
    if not any(property_vars[prop].get() for prop in property_vars):
        messagebox.showwarning("경고", "매물 유형을 선택하세요.")
        return

    if not any(district_vars[district].get() for district in district_vars):
        messagebox.showwarning("경고", "구 이름을 선택하세요.")
        return

    if start_button["text"] == "시작":
        start_button.config(text="중지", fg="white", bg="red")
        stop_flag.clear()  # 중지 플래그 초기화
        log_text_widget.delete('1.0', tk.END)  # 로그 초기화
        progress['value'] = 0  # 진행률 초기화
        progress_label.config(text="진행률: 0%")
        eta_label.config(text="예상 소요 시간: 00:00:00")
        threading.Thread(target=actual_crawling_function).start()
    else:
        stop_flag.set()  # 중지 플래그 설정
        new_print("크롤링 중지")
        start_button.config(text="시작", fg="black", bg="lightgreen")


def actual_crawling_function():
    try:
        new_print(f"크롤링 시작")
        selected_gus = get_selected_districts()
        if not selected_gus:
            new_print("구이름을 선택해주세요.")
            return

        driver = setup_driver()
        if not driver:
            return

        new_print(f"전체 매물 수 계산중 ...")
        gu_urls = [districts[gu] for gu in selected_gus]
        total_count = print_article_count(driver, gu_urls)
        new_print(f"전체 매물 수 : {total_count}")

        # 전체 매물 수를 계산한 후 진행률 및 예상 소요 시간 초기화
        progress['maximum'] = total_count
        progress['value'] = 0
        progress_label.config(text=f"진행률: 0% (0/{total_count})")
        remaining_time = total_count * 10
        eta = str(timedelta(seconds=remaining_time)).split(".")[0]  # 소수점 제거
        eta_label.config(text=f"예상 소요 시간: {eta}")
        progress.update_idletasks()

        driver.quit()

        all_details = []

        for gu in selected_gus:
            page = 1
            while True:
                if stop_flag.is_set():
                    break

                new_print(f"구 : {gu} , 페이지 : {page}")
                details, article_numbers = fetch_article_list(gu, page)

                if not details:
                    break

                all_details.extend(details)

                progress['value'] += len(article_numbers)
                progress_label.config(text=f"진행률: {progress['value'] / progress['maximum'] * 100:.2f}% ({progress['value']}/{progress['maximum']})")
                remaining_time = (progress['maximum'] - progress['value']) * 2.5
                eta = str(timedelta(seconds=remaining_time)).split(".")[0]  # 소수점 제거
                eta_label.config(text=f"예상 소요 시간: {eta}")
                progress.update_idletasks()

                if page % 2 == 0:
                    save_to_excel(all_details, mode='a')  # 2페이지마다 저장
                    all_details = []

                page += 1

            if stop_flag.is_set():
                break

        new_print("엑셀 저장중...")

        # 남아있는 데이터를 엑셀에 저장
        if all_details:
            save_to_excel(all_details, mode='a')
            new_print("최종 데이터 저장 완료")

        new_print("크롤링이 완료 되었습니다.")
        messagebox.showinfo("알림", "크롤링이 완료 되었습니다.")
    except Exception as e:
        new_print(f"Error during crawling: {e}")
        messagebox.showerror("에러", f"크롤링 중 에러가 발생했습니다: {e}")


def get_selected_districts():
    return [district for district in districts if district_vars[district].get() == 1]


def get_selected_property_types():
    selected_types = [property_types[prop] for prop in property_types if property_vars[prop].get() == 1]
    if not selected_types:
        return "APT:OPST:VL:ABYG:OBYG:JGC:SG:SMS"  # 기본값은 전체 선택
    return ":".join(selected_types)


def new_print(text):
    print(text)
    log_text_widget.insert(tk.END, f"{text}\n")
    log_text_widget.see(tk.END)


def start_app():
    global root, property_vars, district_vars, progress, start_button, log_text_widget, progress_label, eta_label

    root = tk.Tk()
    root.title("네이버 부동산 리스트")
    root.geometry("700x700")  # 화면 너비를 현재 크기의 2/3로 조정

    font_large = ('Helvetica', 10)

    # 옵션 프레임
    option_frame = tk.Frame(root)
    option_frame.pack(fill=tk.X, padx=10, pady=10)

    # 매물유형
    type_label = tk.Label(option_frame, text="매물유형:", font=font_large)
    type_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

    all_properties_var = tk.IntVar(value=1)  # 전체 선택 기본값을 선택으로 설정
    property_vars = {prop: tk.IntVar(value=1) for prop in property_types}  # 기본값을 전체 선택으로 설정
    chk_all_properties = tk.Checkbutton(option_frame, text="전체 선택", variable=all_properties_var,
                                        command=lambda: select_all(property_vars, all_properties_var), font=font_large)
    chk_all_properties.grid(row=0, column=1, padx=5, pady=5, sticky='w')

    # 매물유형 체크박스 배치
    props = list(property_types.keys())
    for i, prop in enumerate(props):
        row = (i // 4) + 1
        col = (i % 4) + 1
        chk = tk.Checkbutton(option_frame, text=prop, variable=property_vars[prop], font=font_large,
                             command=lambda: update_all_var(all_properties_var, property_vars))
        chk.grid(row=row, column=col, padx=5, pady=5, sticky='w')

    # 구이름
    gu_label = tk.Label(option_frame, text="구이름:", font=font_large)
    gu_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')

    all_districts_var = tk.IntVar(value=1)  # 전체 선택 기본값을 선택으로 설정
    district_vars = {district: tk.IntVar(value=1) for district in districts}  # 기본값을 전체 선택으로 설정
    chk_all_districts = tk.Checkbutton(option_frame, text="전체 선택", variable=all_districts_var,
                                       command=lambda: select_all(district_vars, all_districts_var), font=font_large)
    chk_all_districts.grid(row=3, column=1, padx=5, pady=5, sticky='w')

    col = 2
    for i, district in enumerate(districts.keys()):  # .keys()를 추가하여 dictionary의 key를 사용
        row = 4 + (i // 4)  # 행을 4열씩 정렬하도록 변경
        col = (i % 4) + 1
        chk = tk.Checkbutton(option_frame, text=district, variable=district_vars[district], font=font_large,
                             command=lambda: update_all_var(all_districts_var, district_vars))
        chk.grid(row=row, column=col, padx=5, pady=5, sticky='w')

    # 버튼 프레임
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    # 시작 및 중지 버튼
    start_button = tk.Button(button_frame, text="시작", command=start_crawling, fg="black", bg="lightgreen", font=font_large, width=20)
    start_button.pack()

    # 버튼 프레임을 중앙에 배치
    button_frame.pack(anchor=tk.CENTER)


    # 로그 화면
    log_label = tk.Label(root, text="로그 화면:", font=font_large)
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
    eta_label = tk.Label(progress_frame, text="예상 소요 시간: 00:00:00", font=font_large)

    progress_label.pack(side=tk.TOP, padx=5)
    eta_label.pack(side=tk.TOP, padx=5)

    style = ttk.Style()
    style.configure("TProgressbar", thickness=30, troughcolor='white', background='green')
    progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    progress.pack(fill=tk.X, padx=10, pady=10, expand=True)

    root.mainloop()


def select_all(vars_dict, all_var):
    value = all_var.get()
    for var in vars_dict.values():
        var.set(value)


def update_all_var(all_var, vars_dict):
    if all(v.get() for v in vars_dict.values()):
        all_var.set(1)
    else:
        all_var.set(0)


if __name__ == "__main__":
    start_app()
