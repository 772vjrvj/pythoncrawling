from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QLabel, QMessageBox
)

import math
import json
from urllib.parse import quote

import sys
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import time
import requests
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


# 전역 변수로 쿠키 저장
global_cookies = {}

# 셀레니움 드라이버 설정 함수
def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")

    # 사용자 에이전트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 탐지 방지 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 크롬 드라이버 실행 및 자동화 방지 우회
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

# 네이버 로그인 스레드
class LoginThread(QThread):
    # 로그인 완료 시 쿠키와 메시지를 전달하는 시그널
    login_complete = pyqtSignal(dict, str)

    def run(self):
        """
        네이버 로그인 과정을 처리하고, 완료 시 쿠키와 메시지를 emit하는 함수입니다.
        """
        global global_cookies
        try:
            driver = setup_driver()
            driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

            time.sleep(2)
            # 로그인 화면의 ID 입력란이 로드될 때까지 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "id"))
            )

            # 로그인 여부를 주기적으로 체크
            logged_in = False
            max_wait_time = 300  # 최대 대기 시간 (초)
            start_time = time.time()

            while not logged_in:
                time.sleep(1)
                elapsed_time = time.time() - start_time

                if elapsed_time > max_wait_time:
                    warning_message = "로그인 실패: 300초 내에 로그인하지 않았습니다."
                    self.login_complete.emit({}, warning_message)
                    break

                # 쿠키 가져오기
                cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

                # 네이버 로그인 완료 확인
                if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                    success_message = "로그인 성공: 정상 로그인 되었습니다."
                    global_cookies = cookies
                    self.login_complete.emit(cookies, success_message)
                    logged_in = True
                    break

        except Exception as e:
            error_message = f"로그인 중 오류가 발생했습니다: {str(e)}"
            self.login_complete.emit({}, error_message)
        finally:
            driver.quit()




class MainWindow(QWidget):
    total_pages = 100
    page_group_size = 10
    userID = ''

    def __init__(self):
        super().__init__()
        self.setWindowTitle("카페 게시글 검색기")
        self.setGeometry(100, 100, 1000, 720)
        self.setStyleSheet(""" 
            QWidget { 
                background-color: #ffffff; 
                font-family: Arial, sans-serif; 
            } 
            QLineEdit { 
                padding: 5px; 
                border: 1px solid #ccc; 
                border-radius: 5px; 
            } 
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                padding: 5px 10px; 
                border: none; 
                border-radius: 5px; 
            } 
            QPushButton:hover { 
                background-color: #45a049; 
            } 
            QPushButton:disabled { 
                background-color: #cccccc; 
                color: #666666; 
            } 
            QTableWidget { 
                border: 1px solid #ccc; 
                gridline-color: #ccc; 
            } 
            QTableWidget::item { 
                padding: 5px; 
            } 
            .link { 
                color: blue; 
                text-decoration: underline; 
            }
        """)

        self.current_page = 0
        self.rows_per_page = 10
        self.current_page_group = 0
        self.data = []

        main_layout = QVBoxLayout()
        self.pagination_layout = QHBoxLayout()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("블로그 주소를 입력하세요")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.on_search_clicked)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        self.loading_label = QLabel()
        self.loading_label.setFixedSize(50, 50)
        self.loading_label.setVisible(False)
        search_layout.addWidget(self.loading_label)

        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["작성일", "제목", "순위 (키워드)"])

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(self.pagination_layout)
        self.setLayout(main_layout)

        # 검색 레이아웃에 로그인 버튼 추가
        login_button = QPushButton("로그인")
        login_button.clicked.connect(self.on_login_clicked)

        search_layout.addWidget(login_button)  # 로그인 버튼을 검색 레이아웃에 추가


    def on_login_clicked(self):
        """로그인 버튼 클릭 시 호출되는 함수입니다."""
        self.login_thread = LoginThread()
        self.login_thread.login_complete.connect(self.handle_login_complete)  # 로그인 완료 시 시그널 연결
        self.login_thread.start()  # 로그인 스레드 시작

    def handle_login_complete(self, cookies, message):
        """로그인 완료 시 호출되는 함수입니다."""
        if cookies:
            QMessageBox.information(self, "로그인 성공", message)
            global_cookies.update(cookies)  # 전역 쿠키 업데이트
        else:
            QMessageBox.warning(self, "로그인 실패", message)

    def update_userID(self, text):
        MainWindow.userID = text  # 전역 변수 userID 업데이트

    def create_page_buttons(self):
        for i in reversed(range(self.pagination_layout.count())):
            widget = self.pagination_layout.itemAt(i).widget()
            if widget is not None:
                self.pagination_layout.removeWidget(widget)
                widget.deleteLater()

        total_page_groups = math.ceil(self.total_pages / self.page_group_size)
        start_page = self.current_page_group * self.page_group_size
        end_page = min(start_page + self.page_group_size, self.total_pages)

        first_button = QPushButton("처음")
        first_button.clicked.connect(self.on_first_clicked)
        prev_button = QPushButton("이전")
        prev_button.clicked.connect(self.on_prev_clicked)
        next_button = QPushButton("다음")
        next_button.clicked.connect(self.on_next_clicked)
        last_button = QPushButton("마지막")
        last_button.clicked.connect(self.on_last_clicked)

        first_button.setFixedSize(80, 30)
        prev_button.setFixedSize(80, 30)
        next_button.setFixedSize(80, 30)
        last_button.setFixedSize(80, 30)

        self.pagination_layout.addWidget(first_button)
        self.pagination_layout.addWidget(prev_button)

        for page_number in range(start_page, end_page):
            page_button = QPushButton(str(page_number + 1))
            page_button.setFixedSize(40, 30)

            page_button.clicked.connect(lambda checked, btn=page_button, page=page_number: self.on_page_button_clicked(page, btn))
            self.pagination_layout.addWidget(page_button)

        self.pagination_layout.addWidget(next_button)
        self.pagination_layout.addWidget(last_button)
        self.pagination_layout.setAlignment(Qt.AlignCenter)

    def change_button_color(self, button):
        for i in range(self.pagination_layout.count()):
            widget = self.pagination_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setStyleSheet("background-color: #4CAF50; color: white;")
        button.setStyleSheet("background-color: blue; color: white;")

    def set_column_widths(self):
        total_width = self.table.width()
        self.table.setColumnWidth(0, total_width * 200 // 1000)
        self.table.setColumnWidth(1, total_width * 527 // 1000)
        self.table.setColumnWidth(2, total_width * 220 // 1000)

    def load_table_data(self):
        """현재 페이지의 데이터를 테이블에 로드합니다."""
        self.table.setRowCount(len(self.data))  # 현재 데이터의 개수만큼 행 설정

        # 각 행의 높이를 기본 높이의 1.5배로 설정
        for row_idx, row_data in enumerate(self.data):  # self.data의 모든 데이터 표시
            self.table.setRowHeight(row_idx, 55)

            for col_idx, item in enumerate(row_data):
                if col_idx == 0 or col_idx == 1:  # "작성일"과 "제목" 열에 QLineEdit 추가
                    input_field = QLineEdit()
                    input_field.setText(item)
                    input_field.setAlignment(Qt.AlignCenter)
                    self.table.setCellWidget(row_idx, col_idx, input_field)
                elif col_idx == 2:  # "순위 (키워드)" 열에 입력 필드와 버튼 추가
                    layout = QHBoxLayout()
                    input_field = QLineEdit()
                    input_field.setPlaceholderText("")
                    search_button = QPushButton("조회")
                    search_button.clicked.connect(lambda _, idx=row_idx, field=input_field, button=search_button: self.on_keyword_search_clicked(field.text(), self.data[idx][3], button))

                    # 높이를 셀 높이에 맞게 조정
                    input_field.setFixedHeight(self.table.rowHeight(row_idx) - 12)  # 약간의 여백을 줄여서 조정
                    search_button.setFixedHeight(self.table.rowHeight(row_idx) - 12)  # 버튼도 동일하게 조정

                    # 여백 조정 (위쪽 여백을 절반으로 설정)
                    layout.setContentsMargins(0, 0, 0, 0)

                    layout.addWidget(input_field)
                    layout.addWidget(search_button)

                    # 새로운 QWidget을 생성하여 레이아웃에 추가
                    widget = QWidget()
                    widget.setLayout(layout)
                    self.table.setCellWidget(row_idx, col_idx, widget)  # cell에 위젯 추가

    def show_alert(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("경고")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def on_search_clicked(self):
        global blog_id
        search_text = self.search_input.text()
        blog_id = self.extract_user_id(search_text)

        if blog_id:
            posts = self.start_blog(blog_id)  # 초기 데이터 가져오기
            if posts:  # 게시글이 있을 경우
                result_list = []
                for item in posts:
                    row = [
                        item['addDate'],
                        item['title'],
                        '-',  # 순위 (키워드)
                        item['logNo'],  # logNo 추가
                    ]
                    result_list.append(row)
                self.data = result_list  # 데이터 설정
                self.load_table_data()  # 테이블에 데이터 로드
                self.create_page_buttons()  # 페이지 버튼 생성
            else:
                self.show_alert("게시글을 불러오는 중 오류가 발생했습니다.")
        else:
            self.show_alert("사용자 ID를 찾을 수 없습니다.")

    def extract_user_id(self, url):
        # 마지막 '/'가 있는지 확인하고, 있으면 그 뒤의 문자열을 리턴
        if '/' in url:
            return url.rsplit('/', 1)[-1]  # 마지막 '/' 뒤의 문자열 반환
        return url  # '/'가 없으면 원래 문자열 반환

    def on_first_clicked(self):
        self.current_page_group = 0
        self.change_page(0)
        self.create_page_buttons()

    def on_prev_clicked(self):
        if self.current_page_group > 0:
            self.current_page_group -= 1
            self.change_page(self.current_page_group * self.page_group_size)
            self.create_page_buttons()

    def on_next_clicked(self):
        total_page_groups = math.ceil(self.total_pages / self.page_group_size)
        if self.current_page_group < total_page_groups - 1:
            self.current_page_group += 1
            self.change_page(self.current_page_group * self.page_group_size)
            self.create_page_buttons()

    def on_last_clicked(self):
        self.current_page_group = math.ceil(self.total_pages / self.page_group_size) - 1
        self.change_page(self.current_page_group * self.page_group_size)
        self.create_page_buttons()

    def on_page_button_clicked(self, page_number, button):
        """페이지 버튼 클릭 시 호출되어 해당 페이지로 이동하고 데이터를 로드합니다."""
        self.current_page = page_number
        self.change_button_color(button)  # 클릭된 버튼 색상 변경

        # 새로운 데이터 가져오기
        posts = self.fetch_post_titles(blog_id, page_number + 1)

        if posts:  # 게시글이 있을 경우
            self.data = []  # 기존 데이터 지우기
            for item in posts:
                row = [
                    item['addDate'],
                    item['title'],
                    '-',  # 순위 (키워드)
                    item['logNo'],  # logNo 추가
                ]
                self.data.append(row)
            self.load_table_data()  # 테이블에 새 데이터 로드
        else:
            self.show_alert("게시글을 불러오는 중 오류가 발생했습니다.")

    def on_keyword_search_clicked(self, keyword, log_no, button):
        """키워드 검색 버튼 클릭 시 호출되어 입력값과 logNo 출력."""
        result_number = self.find_log_no_index(keyword, log_no)
        # "조회" 버튼의 텍스트를 result_number로 변경
        button.setText(str(result_number))  # result_number는 문자열로 변환하여 설정

    def fetch_naver_blog_list(self, query, page):
        url = "https://s.search.naver.com/p/review/48/search.naver"

        # 페이로드를 딕셔너리 형태로 정의
        payload = {
            "ssc": "tab.blog.all",
            "api_type": 8,
            "query": f"{query}",
            "start": f"{page + 1}",
            "sm": "tab_hty.top",
            "prank": f'{page}',
            "ngn_country": "KR"
        }
        query_encoding = quote(query)

        # 헤더 설정
        headers = {
            "authority": "s.search.naver.com",
            "method": "GET",
            "path": "/p/review/48/search.naver",
            "scheme": "https",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            # "cookie": "",
            "origin": "https://search.naver.com",
            "referer": f"https://search.naver.com/search.naver?sm=tab_hty.top&ssc=tab.blog.all&query={query_encoding}&oquery={query_encoding}&tqi=iyLxLlqo1awssNDx7HsssssstkG-146063",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }

        # GET 요청 보내기
        response = requests.get(url, headers=headers, params=payload)
        if response.status_code == 200:
            # JSON 응답 파싱
            json_data = response.json()
            contents = json_data.get("contents", "")

            # HTML 파싱
            soup = BeautifulSoup(contents, 'html.parser')

            # class="detail_box" 안에 있는 title_area의 a 태그 찾기
            detail_boxes = soup.find_all(class_="detail_box")
            results = []  # 제목과 LogNo를 담을 리스트

            for box in detail_boxes:
                title_area = box.find(class_="title_area")
                if title_area:
                    a_tag = title_area.find('a')
                    if a_tag:
                        # 제목 텍스트 추출
                        title_text = a_tag.get_text(separator=' ', strip=True)  # 띄어쓰기를 유지
                        # href 속성에서 LogNo 추출
                        href = a_tag['href']
                        log_no = href.split('/')[-1]  # URL의 마지막 부분이 LogNo
                        results.append({"title": title_text, "log_no": log_no})

            return results  # 제목과 LogNo의 딕셔너리 리스트를 반환
        else:
            print(f"Error: {response.status_code}")

    def find_log_no_index(self, query, main_log_no):
        page = 0  # 초기 페이지 설정 (0부터 시작)
        attempts = 0  # 시도 횟수 초기화
        print(f'query : {query}')
        print(f'main_log_no : {main_log_no}')

        while True:
            titles = self.fetch_naver_blog_list(query, page)
            print(titles)  # 디버깅을 위한 출력

            if titles:
                for index, title in enumerate(titles):
                    if str(title['log_no']) == str(main_log_no):
                        return (30 * page) + (index + 1)  # (30 * page) + index + 1 반환
                page += 1  # 일치하지 않으면 페이지를 1 증가 (30씩 증가시키기 위해)
                attempts += 1  # 시도 횟수 증가
                if attempts > 10:  # 시도 횟수가 10을 넘으면 None 반환
                    return None
            else:
                break  # 결과가 없으면 종료
            time.sleep(0.5)

    def get_naver_blog_search(self, count_per_page, current_page, keyword):
        # URL과 파라미터 설정
        url = "https://section.blog.naver.com/ajax/SearchList.naver"
        params = {
            "countPerPage": count_per_page,
            "currentPage": current_page,
            "endDate": "",
            "keyword": keyword,
            "orderBy": "sim",
            "startDate": "",
            "type": "post"
        }

        # 헤더 설정 (쿠키 제외)
        headers = {
            "authority": "section.blog.naver.com",
            "method": "GET",
            "path": "/ajax/SearchList.naver",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "priority": "u=1, i",
            "referer": f"https://section.blog.naver.com/BlogHome.naver?directoryNo=0&currentPage={current_page}&groupId=0",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }

        # GET 요청 보내기
        response = requests.get(url, headers=headers, params=params)

        # 응답 상태 코드 확인
        if response.status_code == 200:
            try:
                # 응답을 텍스트로 읽고, 앞의 불필요한 문자열을 제거
                text_data = response.text
                if text_data.startswith(")]}',"):
                    text_data = text_data[5:]  # 불필요한 문자열 제거

                # JSON 파싱
                data = json.loads(text_data)

                return {
                    "pagePerCount": data.get("result", {}).get("pagePerCount"),
                    "totalCount": data.get("result", {}).get("totalCount"),
                    "searchList": data.get("result", {}).get("searchList")
                }
            except json.JSONDecodeError:
                e = response.text
        else:
            rs1 = response.status_code
            rs2 = response.text

        return None

    def change_page(self, page_number):
        if page_number < 0:
            page_number = 0
        elif page_number >= math.ceil(len(self.data) / self.rows_per_page):
            page_number = math.ceil(len(self.data) / self.rows_per_page) - 1

        self.current_page = page_number
        self.load_table_data()

    def resizeEvent(self, event):
        self.set_column_widths()
        super().resizeEvent(event)

    def fetch_blog_page(self, blog_id):
        url = f"https://blog.naver.com/PostList.naver?blogId={blog_id}&widgetTypeCall=true&noTrackingCode=true&directAccess=true"
        headers = {
            "authority": "blog.naver.com",
            "method": "GET",
            "path": f"/PostList.naver?blogId={blog_id}&widgetTypeCall=true&noTrackingCode=true&directAccess=true",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"https://blog.naver.com/{blog_id}",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "iframe",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, cookies=global_cookies)
            print(f'global_cookies : {global_cookies}')

            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            return response.content
        except requests.RequestException as e:
            self.show_alert("블로그 페이지를 불러오는 중 오류가 발생했습니다.")
            return None

    def extract_numbers_from_elements(self, content, class_name):
        if content is None:  # content가 None인 경우 처리
            return []
        soup = BeautifulSoup(content, 'html.parser')
        elements = soup.find_all(class_=class_name)
        numbers = []
        for element in elements:
            text = element.get_text()
            numbers.extend(re.findall(r'\d+', text))
        return numbers

    def fetch_post_titles(self, blog_id, current_page):
        """주어진 블로그 ID와 현재 페이지를 사용하여 게시글 제목을 가져옵니다."""
        url = f"https://m.blog.naver.com/api/blogs/{blog_id}/post-list?categoryNo=0&itemCount=10&page={current_page}&userId="
        headers = {
            "authority": "m.blog.naver.com",
            "method": "GET",
            "path": "/api/blogs/roketmissile/post-list?categoryNo=0&itemCount=10&page=1&userId=",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            # "cookie": "NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; BA_DEVICE=09b5d283-4430-4f3b-a39c-dcbb342cd55e; ASID=da9384ec00000191d00facf700000072; NFS=2; NACT=1; _naver_usersession_=1kkjBJG0A5lqAOgUfZgzWA==; page_uid=iyLxXlqVN8Vss46UhIKssssssPR-460363; BUC=cLGqDz5RgLP3gchg-PMoxv6flF9GBRPtd_quVv-ApwM=",
            "priority": "u=1, i",
            "referer": "https://m.blog.naver.com/roketmissile?tab=1",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, cookies=global_cookies)
            print(f' cookies=global_cookies : {global_cookies}')
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("isSuccess"):
                    items = json_data['result']['items']
                    new_items = []
                    for item in items:
                        mapped_item = {
                            "logNo": item.get("logNo"),
                            "title": item.get("titleWithInspectMessage"),
                            "addDate": self.convert_timestamp(item.get("addDate"))
                        }
                        print(mapped_item)
                        new_items.append(mapped_item)
                    return new_items
        except requests.RequestException as e:
            self.show_alert("게시글 제목을 불러오는 중 오류가 발생했습니다.")
            return []
        except json.JSONDecodeError as e:
            self.show_alert("게시글 제목을 처리하는 중 오류가 발생했습니다.")
            return []

    def convert_timestamp(self, timestamp):
        return datetime.fromtimestamp(timestamp / 1000).strftime('%Y.%m.%d')

    def start_blog(self, blog_id):
        posts = self.fetch_post_titles(blog_id, 1)
        return posts


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
