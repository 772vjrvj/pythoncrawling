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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import pyautogui
import time
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException


url_list = []
extracted_data_list = []  # 모든 데이터 저장용
stop_flag = False  # 중지를 위한 플래그

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



class PlaceData:
    def __init__(self, 아이디, 이름, 블로그제목, 블로그게시글, 주소, 이미지, 정보URL, 지도URL):
        self.아이디 = 아이디
        self.이름 = 이름
        self.블로그제목 = 블로그제목
        self.블로그게시글 = 블로그게시글
        self.주소 = 주소
        self.이미지 = 이미지
        self.정보URL = 정보URL
        self.지도URL = 지도URL

    def __repr__(self):
        return (f"PlaceData(아이디: {self.아이디}, 이름: {self.이름}, 블로그제목: {self.블로그제목}, "
                f"블로그게시글: {self.블로그게시글}, 주소: {self.주소}, 이미지: {self.이미지}, "
                f"정보URL: {self.정보URL}, 지도URL: {self.지도URL})")



def read_excel_file(filepath):
    df = pd.read_excel(filepath, sheet_name=0)

    place_data_list = []

    # 각 열을 객체에 담아 리스트로 변환
    for index, row in df.iterrows():
        place_data = PlaceData(
            아이디=row['아이디'],
            이름=row['이름'],
            블로그제목=row['블로그 제목'],
            블로그게시글=row['블로그 게시글'],
            주소=row['주소'],
            이미지=row['이미지'],
            정보URL=row['정보 URL'],
            지도URL=row['지도 URL']
        )
        place_data_list.append(place_data)

    return place_data_list


def update_log(url_list):
    log_text_widget.delete(1.0, tk.END)
    for url in url_list:
        log_text_widget.insert(tk.END, str(url.아이디) + "\n")  # 아이디 속성에 직접 접근
    log_text_widget.insert(tk.END, f"\n총 {len(url_list)}개의 URL이 있습니다.\n")
    log_text_widget.see(tk.END)


def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)


def get_soup(url, timeout=10, retries=3):
    while retries > 0:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # 요청에 실패할 경우 예외를 발생시킴
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.InvalidURL as e:
            print(f"Invalid URL: {url}. Skipping.")
            break  # Invalid URL이면 바로 다음으로 넘어감
        except requests.exceptions.HTTPError as e:
            # 404나 400 범주의 에러는 재시도 없이 바로 종료
            if response.status_code == 404 or response.status_code == 400:
                print(f"Request error: {e}. Status code: {response.status_code}. Skipping URL.")
                break
            print(f"Request error: {e}. Retrying... ({retries} retries left)")
            retries -= 1
            time.sleep(2)  # 재시도 전 잠시 대기
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}. Retrying... ({retries} retries left)")
            retries -= 1
            time.sleep(2)  # 재시도 전 잠시 대기
    return None


def process_author_info(url):
    soup = get_soup(url)
    if not soup:  # soup이 None이면 다음으로 넘어감
        new_print(f"Skipping URL due to failed request or parsing: {url}", level="WARNING")
        return None

    author_span = soup.find("span", itemprop="author", itemscope=True, itemtype="http://schema.org/Person")
    if author_span:
        author_url = author_span.find("link", itemprop="url")["href"]
        return f"{author_url}/videos"
    return None


def extract_published_time(url):
    soup = get_soup(url)
    if not soup:
        print("Failed to retrieve the page or parse HTML.")
        return ""

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
                    return ""
    print("Failed to find published time.")
    return ""


def process_address(address):
    # 공백으로 쪼갠다
    parts = address.split()

    # 마지막 단어가 '층' 또는 '호'를 포함하는지 확인
    if parts[-1].endswith('층') or parts[-1].endswith('호'):
        # 마지막 전까지의 값을 공백으로 이어서 만듦
        temp_text = ' '.join(parts[:-1])

        # 다시 공백으로 쪼개서 처리
        temp_parts = temp_text.split()
        if temp_parts[-1].endswith('층') or temp_parts[-1].endswith('호'):
            # 마지막 전까지의 값을 공백으로 이어서 만듦
            a = ' '.join(temp_parts[:-1])
        else:
            a = temp_text
    else:
        # 마지막 단어가 '층' 또는 '호'를 포함하지 않으면 전체 텍스트 사용
        a = address

    return a


def start_processing():
    global stop_flag, extracted_data_list, root, global_cookies
    stop_flag = False
    log_text_widget.delete(1.0, tk.END)  # 기존 로그 화면 초기화

    extracted_data_list = []
    total_urls = len(url_list)
    progress["maximum"] = total_urls

    input_value = login_input.get()  # 입력창에서 값 읽어오기

    driver = setup_driver()
    driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

    logged_in = False
    max_wait_time = 300  # 최대 대기 시간 (초)
    start_time = time.time()

    while not logged_in:
        print('진행중...')
        time.sleep(1)
        elapsed_time = time.time() - start_time

        if elapsed_time > max_wait_time:
            messagebox.showwarning("경고", "로그인 실패: 300초 내에 로그인하지 않았습니다.")
            break

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

        if 'NID_AUT' in cookies and 'NID_SES' in cookies:
            logged_in = True
            global_cookies = cookies
            messagebox.showinfo("로그인 성공", "정상 로그인 되었습니다.")

            for index, url in enumerate(url_list, start=1):
                if stop_flag:
                    break

                new_print(f"Processing ID {index}: {url.아이디}")

                time.sleep(1)
                driver.get(input_value + "?Redirect=Write&")

                try:
                    time.sleep(5)  # 페이지 로드 시간 추가

                    # iframe으로 전환
                    iframe = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'mainFrame'))  # iframe의 ID로 전환
                    )
                    driver.switch_to.frame(iframe)

                    if index == 1:

                        try:
                            # 작성중인글 확인
                            time.sleep(2)
                            # 이제 iframe 내에서 요소를 찾음
                            popup_button = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-cancel'))
                            )
                            popup_button.click()

                        except TimeoutException:
                            # close_button이 없을 경우에 실행될 코드 (필요에 따라 생략 가능)
                            print("close_button이 존재하지 않습니다.")


                        time.sleep(2)
                        # 이제 iframe 내에서 요소를 찾음
                        close_button = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'se-help-panel-close-button'))
                        )
                        close_button.click()

                    # 3초 후 텍스트 입력 (클래스 이름 'se-ff-nanumgothic se-fs32 __se-node' 내부에 텍스트 '1234' 입력)
                    time.sleep(2)

                    # 요소 찾기

                    # 더 세밀하게 특정 요소를 클릭하고 텍스트 입력
                    bb = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"제목")]'))
                    )
                    # 클릭 후 텍스트 삽입
                    bb.click()
                    actions = ActionChains(driver)
                    actions.send_keys(url.블로그제목).perform()


                    time.sleep(2)
                    # 이제 iframe 내에서 요소를 찾음
                    image_upload_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'se-image-toolbar-button'))
                    )
                    image_upload_button.click()


                    # 현재 프로그램이 실행되는 경로
                    current_dir = os.getcwd()

                    # 'images' 폴더의 경로
                    images_dir = os.path.join(current_dir, 'images')

                    # 'images' 폴더 내 첫 번째 폴더 이름을 가져옴
                    base_folder_name = next(os.walk(images_dir))[1][0]

                    # 폴더 이름을 구성
                    folder_name = f"{index}. {url.이름}"

                    # 전체 경로 생성
                    full_path = os.path.join(images_dir, base_folder_name, folder_name)

                    # Windows 파일 선택 창에서 경로를 입력하고 '열기' 버튼을 누름
                    time.sleep(2)  # 파일 선택 창이 열릴 때까지 대기

                    # 경로가 정확한지 확인
                    if not os.path.exists(full_path):
                        messagebox.showerror("경로 오류", f"경로가 존재하지 않습니다: {full_path}")
                        return

                    # 상단 경로 입력창에 포커스 맞추기 (탐색기 창에서 경로 입력)
                    pyautogui.hotkey('alt', 'd')  # 상단 경로창 선택
                    time.sleep(1)

                    # 클립보드를 사용해 경로 입력
                    pyperclip.copy(full_path)  # 경로를 클립보드에 복사
                    pyautogui.hotkey('ctrl', 'v')  # 클립보드에서 붙여넣기 (Ctrl + V)
                    pyautogui.press('enter')  # 엔터키로 폴더 열기

                    time.sleep(2)  # 폴더 열리는 시간 대기

                    # 파일 목록에 포커스 맞추기 (탐색기 창에서 파일 선택으로 이동)
                    pyautogui.press('tab')  # 경로창에서 파일 목록으로 이동하기 위해 탭 누르기
                    pyautogui.press('tab')  # 두 번째 탭을 누르면 파일 목록에 포커스가 맞춰짐
                    pyautogui.press('tab')  # 세 번째 탭을 누르면 포커스가 맞춰짐
                    pyautogui.press('tab')  # 네 번째 탭을 누르면 포커스가 맞춰짐
                    pyautogui.press('down')  # 파일 목록의 첫 번째 파일로 이동

                    # 전체 파일 선택 (Ctrl + A)
                    pyautogui.hotkey('ctrl', 'a')  # 모든 파일 선택
                    time.sleep(1)

                    # 파일 열기(확인) 버튼 클릭 (Windows 기준)
                    pyautogui.press('enter')  # 열기 버튼을 눌러 파일 업로드

                    time.sleep(2)

                    # 스크롤을 맨 위로 올리기
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)

                    # 이제 iframe 내에서 요소를 찾음 (이미지 업로드 후 추가 작업)
                    image_upload_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'se-image-type-label'))
                    )

                    driver.execute_script("arguments[0].click();", image_upload_button)

                    time.sleep(10)
                    # 활성화된 요소 가져오기
                    active_element = driver.switch_to.active_element

                    # ActionChains로 클릭 후 텍스트 입력 시도
                    actions = ActionChains(driver)
                    actions.move_to_element(active_element).click().send_keys(url.블로그게시글).perform()

                    a = process_address(url.주소)

                    time.sleep(2)
                    # 이제 iframe 내에서 요소를 찾음
                    image_map_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'se-map-toolbar-button'))
                    )
                    image_map_button.click()

                    time.sleep(2)
                    # input 필드 찾기
                    input_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "react-autosuggest__input"))
                    )

                    # input 필드에 'a' 입력
                    input_field.send_keys(a)

                    # 검색 버튼 찾기
                    search_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "se-place-search-button"))
                    )

                    # 검색 버튼 클릭
                    search_button.click()

                    time.sleep(2)

                    try:
                        # class가 'se-place-map-search-result-list'인 첫 번째 li 내의 'se-place-add-button' 찾기
                        search_result_list = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'se-place-map-search-result-list'))
                        )
                        time.sleep(2)

                        # 'se-place-map-search-result-list' 안에서 첫 번째 'li' 요소를 기다리며 찾음
                        first_li = WebDriverWait(search_result_list, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, 'li'))
                        )

                        # 마우스를 'first_li' 위로 오버
                        actions = ActionChains(driver)
                        actions.move_to_element(first_li).perform()  # 마우스를 해당 요소 위로 이동

                        time.sleep(2)
                        # li 내부의 'se-place-add-button'이 로드될 때까지 기다림
                        add_button = WebDriverWait(first_li, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'se-place-add-button'))
                        )
                        add_button.click()

                        time.sleep(2)
                        # li 내부의 'se-place-add-button'이 로드될 때까지 기다림
                        confirm_map_button = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-confirm'))
                        )
                        confirm_map_button.click()

                    except (NoSuchElementException, TimeoutException):
                        # 'se-place-add-button'이 없으면 'se-popup-close-button'을 찾아 클릭
                        try:
                            close_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, 'se-popup-close-button'))
                            )
                            close_button.click()
                        except (NoSuchElementException, TimeoutException):
                            print("close_button을 찾을 수 없습니다.")



                    # 3초 후 'publish_btn__m9KHH' 클래스 버튼 클릭
                    time.sleep(3)
                    publish_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'publish_btn__m9KHH'))
                    )
                    driver.execute_script("arguments[0].click();", publish_button)

                    # 3초 후 'confirm_btn__WEaBq' 클래스 버튼 클릭
                    time.sleep(3)
                    confirm_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'confirm_btn__WEaBq'))
                    )
                    driver.execute_script("arguments[0].click();", confirm_button)

                except Exception as e:
                    print(f"에러 발생: {e}")

                # 진행률 업데이트
                progress["value"] = index
                progress_label.config(text=f"진행률: {int((index) / total_urls * 100)}%")

                remaining_time = (total_urls - (index)) * 60  # 남은 URL 개수 * 2초
                eta_label.config(text=f"남은 시간: {time.strftime('%H:%M:%S', time.gmtime(remaining_time))}")

                time.sleep(random.uniform(2, 5))

            if not stop_flag:
                driver.quit()  # 작업이 끝난 후 드라이버 종료
                new_print("작업 완료.", level="SUCCESS")
                flash_window(root)
                messagebox.showinfo("알림", "작업이 완료되었습니다.")
                stop_flash_window(root)  # 메시지박스 확인 후 깜빡임 중지


def upload_images(driver, folder_path):
    # Windows 파일 선택 창에서 경로를 입력하고 '열기' 버튼을 누름
    time.sleep(2)  # 파일 선택 창이 열릴 때까지 대기

    # 경로가 정확한지 확인
    if not os.path.exists(folder_path):
        messagebox.showerror("경로 오류", f"경로가 존재하지 않습니다: {folder_path}")
        return

    # 상단 경로 입력창에 포커스 맞추기 (탐색기 창에서 경로 입력)
    pyautogui.hotkey('alt', 'd')  # 상단 경로창 선택
    time.sleep(1)

    # 클립보드를 사용해 경로 입력
    pyperclip.copy(folder_path)  # 경로를 클립보드에 복사
    pyautogui.hotkey('ctrl', 'v')  # 클립보드에서 붙여넣기 (Ctrl + V)
    pyautogui.press('enter')  # 엔터키로 폴더 열기

    time.sleep(2)  # 폴더 열리는 시간 대기

    # 파일 목록에 포커스 맞추기 (탐색기 창에서 파일 선택으로 이동)
    pyautogui.press('tab')  # 경로창에서 파일 목록으로 이동하기 위해 탭 누르기
    pyautogui.press('tab')  # 두 번째 탭을 누르면 파일 목록에 포커스가 맞춰짐
    pyautogui.press('tab')  # 세 번째 탭을 누르면 포커스가 맞춰짐
    pyautogui.press('tab')  # 네 번째 탭을 누르면 포커스가 맞춰짐
    pyautogui.press('down')  # 파일 목록의 첫 번째 파일로 이동

    # 전체 파일 선택 (Ctrl + A)
    pyautogui.hotkey('ctrl', 'a')  # 모든 파일 선택
    time.sleep(1)

    # 파일 열기(확인) 버튼 클릭 (Windows 기준)
    pyautogui.press('enter')  # 열기 버튼을 눌러 파일 업로드

    time.sleep(3)

    # 스크롤을 맨 위로 올리기
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


    # 이제 iframe 내에서 요소를 찾음 (이미지 업로드 후 추가 작업)
    image_upload_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'se-image-type-label'))
    )

    # JavaScript로 강제 클릭
    driver.execute_script("arguments[0].click();", image_upload_button)

    # 활성화된 요소 가져오기
    active_element = driver.switch_to.active_element

    # ActionChains로 클릭 후 텍스트 입력 시도
    actions = ActionChains(driver)
    actions.move_to_element(active_element).click().send_keys("여기에 입력할 텍스트").perform()

    # 3초 후 'publish_btn__m9KHH' 클래스 버튼 클릭
    time.sleep(3)
    publish_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'publish_btn__m9KHH'))
    )
    driver.execute_script("arguments[0].click();", publish_button)

    # 3초 후 'confirm_btn__WEaBq' 클래스 버튼 클릭
    time.sleep(3)
    confirm_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'confirm_btn__WEaBq'))
    )
    driver.execute_script("arguments[0].click();", confirm_button)



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
    global log_text_widget, start_button, progress, progress_label, eta_label, login_input, root

    root = TkinterDnD.Tk()
    root.title("네이버 블로그 자동 등록 프로그램")
    root.geometry("600x800")

    font_large = font.Font(size=10)

    # blog 주소 입력창과 라벨 추가
    input_frame = tk.Frame(root)
    input_frame.pack(pady=10)

    blog_label = tk.Label(input_frame, text="blog 주소 (https포함) :", font=font_large)
    blog_label.pack(side=tk.LEFT)

    # input_frame_2 = tk.Frame(root)
    # input_frame_2.pack(pady=10)
    #
    # blog_label_2 = tk.Label(input_frame_2, text="예시 https://blog.naver.com/1234", font=font_large, bg="green", fg="white")
    # blog_label_2.pack(side=tk.LEFT)

    # 로그인 입력창 추가
    login_input = tk.Entry(root, font=font_large, width=25)
    login_input.pack(pady=10)  # 패딩으로 적절한 간격 추가

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