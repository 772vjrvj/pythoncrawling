import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from tkinter import ttk, scrolledtext
from datetime import datetime, timedelta
import threading
import pandas as pd
import tkinter as tk


def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def new_print(text):
    print(f"{get_current_time()} - {text}")
    current_time = get_current_time()
    log_text_widget.insert(tk.END, f"{current_time} - {text}\n")
    log_text_widget.see(tk.END)  # 자동 스크롤


# 드라이버 세팅
def setup_driver():

    chrome_options = Options()  # 크롬 옵션 설정

    # 헤드리스 모드로 실행
    chrome_options.add_argument("--headless")

    # GPU 비활성화
    chrome_options.add_argument("--disable-gpu")

    # 샌드박스 보안 모드를 비활성화합니다.
    chrome_options.add_argument("--no-sandbox")

    # /dev/shm 사용 비활성화
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 시크릿 모드로 실행
    chrome_options.add_argument("--incognito")

    # 사용자 에이전트를 설정하여 브라우저의 기본값 대신 특정 값을 사용하게 합니다.
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 웹 드라이버를 사용한 자동화임을 나타내는 Chrome의 플래그를 비활성화하여 자동화 도구의 사용을 숨깁니다.
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # 자동화 확장 기능의 사용을 비활성화합니다.
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 사용하여 호환되는 크롬 드라이버를 자동으로 다운로드하고 설치합니다.
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 크롬 개발자 프로토콜 명령을 실행하여 브라우저의 navigator.webdriver 속성을 수정함으로써, 자동화 도구 사용을 감지하고 차단하는 스크립트를 우회합니다.
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    return driver


# 크몽 전체 페이지 가져오기
def fetch_total_pages(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    try:
        driver.get(url)
        time.sleep(5)
        total_pages_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'c-page__total'))
        )

        # 텍스트가 숫자인지 확인
        total_pages_text = total_pages_element.text.strip()
        if total_pages_text.isdigit():
            total_pages = int(total_pages_text)
            print(f"Total pages text: {total_pages}")
            return total_pages
        else:
            print("No valid total pages number found.")
            return 0
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Element not found or timed out: {e}")
        return 0
    except ValueError:
        print("Conversion error: Text is not a number.")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0


# 모든 제품 id들을 가져온다.
def fetch_product_ids(driver, keyword, page):
    url = f"https://search.tmon.co.kr/search/?keyword={keyword}&thr=hs&page={page}"
    try:
        driver.get(url)
        time.sleep(2)  # 페이지 로딩을 위한 대기 시간

        # 'deallist_wrap' 클래스를 가진 요소를 찾고, 내부에서 'list' 클래스를 가진 ul 요소를 추출
        deallist_wrap = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'deallist_wrap'))
        )
        ul_element = deallist_wrap.find_element(By.CLASS_NAME, 'list')
        li_elements = ul_element.find_elements(By.CLASS_NAME, 'item')

        # 각 'item' 클래스를 가진 li 요소 내의 a 태그에서 'data-deal-srl' 속성 추출
        ids = []
        for li in li_elements:
            try:
                a_tag = li.find_element(By.TAG_NAME, 'a')
                deal_srl = a_tag.get_attribute('data-deal-srl')
                if deal_srl:
                    new_print(f"page : {page}, id {deal_srl}")
                    ids.append(deal_srl)
            except Exception as e:
                print(f"Error retrieving data-deal-srl for an item: {e}")

        return ids

    except Exception as e:
        print(f"An error occurred while fetching the product list: {e}")
        return []


# 제품 상세정보 가져오기
def fetch_product_detail(driver, product_id):
    url = f"https://www.tmon.co.kr/deal/{product_id}"
    driver.get(url)

    print(f"product_id : {product_id}")
    print(f"url : {url}")

    seller_info = {"상호명": "", "이메일": ""}

    try:
        time.sleep(3)  # 페이지가 완전히 로드될 때까지 대기
        tab_inner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab-inner._fixedUIItem'))
        )

        tab_navigation = tab_inner.find_element(By.CLASS_NAME, 'tab-navigation')
        li_elements = tab_navigation.find_elements(By.TAG_NAME, 'li')

        # "환불/교환" 탭 클릭
        for li in li_elements:
            if "환불" in li.text or "교환" in li.text or "취소" in li.text:
                li.click()
                new_print("Clicked on '환불/교환'")
                break

        time.sleep(2)  # 탭 전환 후 로딩 시간
        seller_info_button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//button[h4[text()='판매자 정보']]"))
        )
        seller_info_button.click()
        new_print("Clicked on '판매자 정보'")

        time.sleep(2)  # 판매자 정보 토글 후 로딩 시간
        tables = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'tbl_info'))
        )

        new_print(f"tables len {len(tables)}")

        # 판매자 정보 추출
        found_all_info = False
        for table in tables:
            try:
                company_name_td = table.find_element(By.XPATH, ".//th[contains(text(), '상호명')]/following-sibling::td")
                seller_info["상호명"] = company_name_td.text if not seller_info["상호명"] else seller_info["상호명"]
                email_td = table.find_element(By.XPATH, ".//th[contains(text(), '이메일')]/following-sibling::td")
                seller_info["이메일"] = email_td.text if not seller_info["이메일"] else seller_info["이메일"]

                if seller_info["상호명"] and seller_info["이메일"]:
                    found_all_info = True
                    break
            except (NoSuchElementException, ElementNotInteractableException):
                continue  # 요소가 없거나 상호작용할 수 없을 경우 다음 테이블로 넘어갑니다.

        if not found_all_info:
            print("Not all information could be found.")

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

    return seller_info


# 엑셀 얻기
def fetch_excel(all_seller_info):
    # Define the columns
    columns = ['키워드', '상호명', '이메일', '플랫폼']

    # Create a DataFrame
    df = pd.DataFrame(all_seller_info, columns=columns)

    # Save the DataFrame to an Excel file
    df.to_excel('seller_info.xlsx', index=False)


def get_keyword():
    return keyword_text.get("1.0", tk.END).strip()

# 크롤링 시작 버튼 클릭 이벤트 처리 함수
def start_crawling():
    keyword = get_keyword()
    if keyword:
        new_print(f"Keyword entered: {keyword}")
        threading.Thread(target=actual_crawling_function, args=(keyword,)).start()
    else:
        new_print("Please enter a keyword.")


def actual_crawling_function(kwd):
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

        # 페이지 진행률 업데이트
        update_page_progress(page, total_pages)

    new_print(f"product_ids len : {len(product_ids)}")

    all_seller_info = []

    new_print("크롤링 시작...")

    max_value = len(product_ids)

    for index, product_id in enumerate(product_ids):
        seller_info = fetch_product_detail(driver, product_id)
        seller_info["키워드"] = kwd
        seller_info["플랫폼"] = company

        new_print(f"seller_info : {seller_info}")

        all_seller_info.append(seller_info)

        # 진행률 게이지 바를 서서히 업데이트
        update_progress(index + 1, max_value)  # 수정: index + 1로 변경하여 표시

    new_print("엑셀 시작...")
    fetch_excel(all_seller_info)
    new_print("끝...")


def update_page_progress(current_page, total_pages):
    page_progress_percentage = (current_page / total_pages) * 100
    page_progress['value'] = page_progress_percentage
    page_progress_label.config(text=f"페이지 진행률: {page_progress_percentage:.2f}%")
    page_index_label.config(text=f"{current_page}/{total_pages}")

    remaining_time = (total_pages - current_page) * 3  # 각 페이지 당 3초 소요
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
    root.after(1000, update_time)  # 1초마다 업데이트


# 메인 윈도우 설정
root = tk.Tk()
root.title("크롤링 프로그램")
root.geometry("800x600")

# 현재 시간 라벨
current_time_label = tk.Label(root, text=f"현재시간: {get_current_time()}", anchor="w")
current_time_label.pack(fill=tk.X, padx=10, pady=5)
update_time()  # 현재 시간 업데이트 시작

# 키워드 입력
keyword_label = tk.Label(root, text="키워드 입력:", anchor="w")
keyword_label.pack(fill=tk.X, padx=10, pady=5)

keyword_text = tk.Text(root, height=1, width=50)
keyword_text.pack(fill=tk.X, padx=10, pady=5)

# 시작 버튼
start_button = tk.Button(root, text="시작", command=start_crawling)
start_button.pack(padx=10, pady=10)

# 로그 창
log_label = tk.Label(root, text="로그:", anchor="w")
log_label.pack(fill=tk.X, padx=10, pady=5)
log_text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
log_text_widget.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

# 페이지 진행률 및 예상 소요 시간 라벨
page_progress_label = tk.Label(root, text="페이지 진행률: 0%")
page_progress_label.pack(fill=tk.X, padx=10)

page_index_label = tk.Label(root, text="0/0")
page_index_label.pack(fill=tk.X, padx=10)

page_eta_label = tk.Label(root, text="남은 시간: 00:00:00")  # 추가된 라벨
page_eta_label.pack(fill=tk.X, padx=10)

# 페이지 진행률 게이지 바
page_progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100)
page_progress.pack(fill=tk.X, padx=10, pady=10)

# 진행률 및 예상 소요 시간 라벨
progress_label = tk.Label(root, text="진행률: 0%")
progress_label.pack(fill=tk.X, padx=10)

index_label = tk.Label(root, text="0/0")  # 추가된 라벨
index_label.pack(fill=tk.X, padx=10)

eta_label = tk.Label(root, text="남은 시간: 00:00:00")
eta_label.pack(fill=tk.X, padx=10)

# 진행률 게이지 바
progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100)
progress.pack(fill=tk.X, padx=10, pady=10)

# 메인 루프 시작
root.mainloop()
