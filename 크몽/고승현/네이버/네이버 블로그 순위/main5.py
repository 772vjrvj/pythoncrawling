import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QLabel, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import webbrowser
import requests
from bs4 import BeautifulSoup
import re
import math
import urllib.parse
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from datetime import datetime
import os
import pandas as pd


class MainWindow(QWidget):
    total_pages = 0
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

        # 새로운 입력 창 생성 (userID_input)
        self.userID_input = QLineEdit(self)
        self.userID_input.setPlaceholderText("UserID")
        self.userID_input.setFixedWidth(200)  # 검색 버튼의 2배 크기 설정

        # 입력 값 변경 시 userID 업데이트
        self.userID_input.textChanged.connect(self.update_userID)

        # 레이아웃에 userID_input 추가
        search_layout.addWidget(self.userID_input)


        self.loading_label = QLabel()
        self.loading_label.setFixedSize(50, 50)
        self.loading_label.setVisible(False)
        search_layout.addWidget(self.loading_label)

        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["작성일", "제목", "순위 (키워드)", "PC", "MO", "SUM"])

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(self.pagination_layout)

        self.setLayout(main_layout)

        self.table.cellClicked.connect(self.on_cell_clicked)

        webbrowser.register('edge', None, webbrowser.BackgroundBrowser("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"))

    def update_userID(self, text):
        MainWindow.userID = text  # 전역 변수 userID 업데이트
        print(f"Updated userID: {MainWindow.userID}")


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
        self.table.setColumnWidth(0, total_width * 150 // 1000)
        self.table.setColumnWidth(1, total_width * 477 // 1000)
        self.table.setColumnWidth(2, total_width * 200 // 1000)
        self.table.setColumnWidth(3, total_width * 50 // 1000)
        self.table.setColumnWidth(4, total_width * 50 // 1000)
        self.table.setColumnWidth(5, total_width * 50 // 1000)


    def load_table_data(self):
        """현재 페이지의 데이터를 테이블에 로드합니다."""
        self.table.setRowCount(len(self.data))  # 현재 데이터의 개수만큼 행 설정

        for row_idx, row_data in enumerate(self.data):  # self.data의 모든 데이터 표시
            for col_idx, item in enumerate(row_data):
                if col_idx == 2:  # "순위 (키워드)" 열에 입력 필드와 버튼 추가
                    layout = QHBoxLayout()
                    input_field = QLineEdit()
                    input_field.setPlaceholderText("")
                    search_button = QPushButton("조회")
                    # search_button.clicked.connect(lambda _, idx=row_idx, field=input_field: self.on_keyword_search_clicked(field.text(), self.data[idx][6]))
                    search_button.clicked.connect(lambda _, idx=row_idx, field=input_field, button=search_button: self.on_keyword_search_clicked(field.text(), self.data[idx][6], button))


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
                elif col_idx == 1:  # "제목" 열 클릭 시 새로운 함수 호출
                    title_item = QTableWidgetItem(item)
                    title_item.setTextAlignment(Qt.AlignCenter)
                    title_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    title_item.setData(Qt.UserRole, self.data[row_idx][6])  # URL 저장
                    self.table.setItem(row_idx, col_idx, title_item)
                else:
                    table_item = QTableWidgetItem(item)
                    table_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, table_item)


    def on_cell_clicked(self, row, column):
        if column == 1:  # 제목 클릭 시 logNo 출력
            log_no = self.data[row][6]  # logNo를 self.data에서 가져오기
            url = f"https://blog.naver.com/{blog_id}/{log_no}"  # URL 형식으로 설정
            print(f"Log No: {log_no}")
            if url:
                webbrowser.get('edge').open(url)  # Edge 브라우저로 URL 열기


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
        print(f"입력된 URL: {search_text}")
        blog_id = self.extract_user_id(search_text)

        if blog_id:
            posts = self.start_blog(blog_id)  # 초기 데이터 가져오기
            print(f"가져온 게시글 수: {len(posts)}")  # 가져온 게시글 수 확인
            if posts:  # 게시글이 있을 경우
                result_list = []
                for item in posts:
                    row = [
                        item['addDate'],
                        item['title'],
                        '-',  # 순위 (키워드)
                        '-',  # PC
                        '-',  # MO
                        '-',  # SUM
                        item['logNo'],  # logNo 추가
                    ]
                    result_list.append(row)
                self.data = result_list  # 데이터 설정
                print(f"로드된 데이터: {self.data}")  # 데이터 확인
                self.load_table_data()  # 테이블에 데이터 로드
                self.create_page_buttons()  # 페이지 버튼 생성
            else:
                self.show_alert("게시글을 불러오는 중 오류가 발생했습니다.")
        else:
            self.show_alert("사용자 ID를 찾을 수 없습니다.")


    def extract_user_id(self, url):
        if not url.startswith("https://"):
            return url  # https가 없으면 URL을 그대로 반환

        match = re.search(r'https?://blog\.naver\.com/([^/]+)/?', url)
        if match:
            return match.group(1)
        return None  # 매칭이 없으면 None 반환

    def on_first_clicked(self):
        self.current_page_group = 0
        self.change_page(0)
        self.create_page_buttons()
        print("처음 버튼 클릭")

    def on_prev_clicked(self):
        if self.current_page_group > 0:
            self.current_page_group -= 1
            self.change_page(self.current_page_group * self.page_group_size)
            self.create_page_buttons()
        print("이전 버튼 클릭")

    def on_next_clicked(self):
        total_page_groups = math.ceil(self.total_pages / self.page_group_size)
        if self.current_page_group < total_page_groups - 1:
            self.current_page_group += 1
            self.change_page(self.current_page_group * self.page_group_size)
            self.create_page_buttons()
        print("다음 버튼 클릭")

    def on_last_clicked(self):
        self.current_page_group = math.ceil(self.total_pages / self.page_group_size) - 1
        self.change_page(self.current_page_group * self.page_group_size)
        self.create_page_buttons()
        print("마지막 버튼 클릭")

    def on_page_button_clicked(self, page_number, button):
        """페이지 버튼 클릭 시 호출되어 해당 페이지로 이동하고 데이터를 로드합니다."""
        self.current_page = page_number
        self.change_button_color(button)  # 클릭된 버튼 색상 변경

        print(f'page_number : {page_number}')
        print(f'blog_id : {blog_id}')

        # 새로운 데이터 가져오기
        posts = self.fetch_post_titles(blog_id, page_number + 1)

        if posts:  # 게시글이 있을 경우
            self.data = []  # 기존 데이터 지우기
            for item in posts:
                row = [
                    item['addDate'],
                    item['title'],
                    '-',  # 순위 (키워드)
                    '-',  # PC
                    '-',  # MO
                    '-',  # SUM
                    item['logNo'],  # logNo 추가
                ]
                self.data.append(row)
            self.load_table_data()  # 테이블에 새 데이터 로드
        else:
            self.show_alert("게시글을 불러오는 중 오류가 발생했습니다.")

    def on_keyword_search_clicked(self, keyword, log_no, button):
        """키워드 검색 버튼 클릭 시 호출되어 입력값과 logNo 출력."""
        print(f"입력한 키워드: {keyword}, Log No: {log_no}")
        result_number = self.find_target_log(keyword, log_no)
        # "조회" 버튼의 텍스트를 result_number로 변경
        button.setText(str(result_number))  # result_number는 문자열로 변환하여 설정


        print(f'result_number : {result_number}')
        print(f'self.userID : {self.userID}')


        rs = self.item_scout(self.userID, keyword)

        # rs가 유효한 결과일 때 테이블에 값 설정
        if rs:
            # 현재 row의 MO, PC, SUM 컬럼에 데이터 삽입
            widget_index = self.table.indexAt(button.parentWidget().pos())
            row_idx = widget_index.row()


            mo_item = QTableWidgetItem(str(rs.get("MO", "-")))
            pc_item = QTableWidgetItem(str(rs.get("PC", "-")))
            sum_item = QTableWidgetItem(str(rs.get("SUM", "-")))

            mo_item.setTextAlignment(Qt.AlignCenter)
            pc_item.setTextAlignment(Qt.AlignCenter)
            sum_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_idx, 3, mo_item)  # MO 컬럼 (3번째 인덱스)
            self.table.setItem(row_idx, 4, pc_item)  # PC 컬럼 (4번째 인덱스)
            self.table.setItem(row_idx, 5, sum_item)  # SUM 컬럼 (5번째 인덱스)


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
                print("JSON 디코딩 오류가 발생했습니다. 응답 내용:", response.text)
        else:
            print("요청 실패, 상태 코드:", response.status_code)
            print("응답 내용:", response.text)

        return None


    def find_target_log(self, keyword, target_log_no):
        count_per_page = 20
        current_page = 1

        # 첫 페이지 조회
        result = self.get_naver_blog_search(count_per_page, current_page, keyword)
        print("진행중 페이지:", 1)
        if result:
            total_count = result["totalCount"]
            totalPages = math.ceil(total_count / count_per_page)  # 전체 페이지 수 계산

            # 첫 페이지에서 target_log_no 찾기
            for index, item in enumerate(result["searchList"]):
                if item.get("logNo") == int(target_log_no):
                    result_index = index + 1
                    print("찾은 페이지:", current_page)
                    print("찾은 위치:", result_index)
                    return result_index

            # 첫 페이지에 없다면 다음 페이지부터 탐색
            for page in range(2, totalPages + 1):
                print("진행중 페이지:", page)
                time.sleep(1)
                result = self.get_naver_blog_search(count_per_page, page, keyword)

                if result:
                    for index, item in enumerate(result["searchList"]):
                        if item.get("logNo") == int(target_log_no):
                            # 해당 페이지에서 찾은 경우
                            result_index = count_per_page * (page - 1) + (index + 1)
                            print("찾은 페이지:", page)
                            print("찾은 위치:", result_index)
                            return result_index

        print("logNo를 찾을 수 없습니다.")
        return None


    def setup_driver(self, userID):
        try:
            print(f'userID : {userID}')
            chrome_options = Options()
            user_data_dir = f"C:\\Users\\{userID}\\AppData\\Local\\Google\\Chrome\\User Data"
            profile = "Default"

            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"profile-directory={profile}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--headless")  # Headless 모드 추가

            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            download_dir = os.path.abspath("downloads")
            os.makedirs(download_dir, exist_ok=True)

            chrome_options.add_experimental_option('prefs', {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            script = '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
            '''
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

            return driver
        except WebDriverException as e:
            print(f"Error setting up the WebDriver: {e}")
            return None


    def item_scout(self, userID, keyword):
        driver = self.setup_driver(userID)
        if driver is None:
            return

        try:
            driver.get("https://itemscout.io/")

            # Wait for the input field to be present
            input_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="상품을 검색해보세요."]'))
            )

            # Set the value of the input field to the keyword
            input_element.send_keys(keyword)

            # Find the search button next to the input field and click it
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "검색")]'))
            )
            search_button.click()

            # "검색 비율" div와 그 옆의 버튼 찾기
            stat_title = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "KeywordCountStat_count-title__nq7aO") and text()="검색 비율"]'))
            )
            button = stat_title.find_element(By.XPATH, 'following-sibling::button')

            # 마우스 오버 수행
            actions = ActionChains(driver)
            actions.move_to_element(button).perform()
            time.sleep(1)  # 마우스 오버 후 텍스트 로딩 시간

            # 마우스 오버 후 나타난 div에서 텍스트 가져오기
            hover_text_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "KeywordCountStat_count-title__nq7aO") and text()="검색 비율"]/following-sibling::button/following-sibling::div'))
            )
            hover_text = hover_text_div.text
            print("Hover text:", hover_text)

            # 정규 표현식으로 "모바일 검색수"와 "PC 검색수" 값 추출
            search_counts = {}
            mobile_search = re.search(r"모바일 검색수\s*:\s*([\d,]+)회", hover_text)
            pc_search = re.search(r"PC 검색수\s*:\s*([\d,]+)회", hover_text)

            if mobile_search:
                search_counts["MO"] = int(mobile_search.group(1).replace(",", ""))
            if pc_search:
                search_counts["PC"] = int(pc_search.group(1).replace(",", ""))

            search_counts["SUM"] = search_counts["MO"] + search_counts["PC"]

            return search_counts

        except TimeoutException:
            print("요소를 찾을 수 없습니다.")
        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            print("드라이버 종료")
            driver.quit()

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
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            return response.content
        except requests.RequestException as e:
            print(f"HTTP 요청 중 오류 발생: {e}")
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
        url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={blog_id}&viewdate=&currentPage={current_page}&categoryNo=&parentCategoryNo=&countPerPage=10"
        headers = {
            "authority": "blog.naver.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

            cleaned_text = re.sub(r'\\(?!["\\/bfnrt])', "", response.text)
            data = json.loads(cleaned_text)

            posts = []
            for post in data.get("postList", []):
                title = urllib.parse.unquote(post.get("title", "")).replace("+", " ")
                title = re.sub(r'\s+', ' ', title).strip()
                post_data = {
                    "addDate": post.get("addDate"),
                    "logNo": post.get("logNo"),
                    "title": title,
                    "url": f'https://blog.naver.com/{blog_id}/{post.get("logNo")}'
                }
                print(post_data)  # 디버깅을 위한 출력
                posts.append(post_data)

            print(f"가져온 게시글 수: {len(posts)}")  # 가져온 게시글 수 출력
            return posts

        except requests.RequestException as e:
            print(f"HTTP 요청 중 오류 발생: {e}")
            self.show_alert("게시글 제목을 불러오는 중 오류가 발생했습니다.")
            return []
        except json.JSONDecodeError as e:
            print("JSONDecodeError 발생:", e)
            print("응답 텍스트:", response.text)
            self.show_alert("게시글 제목을 처리하는 중 오류가 발생했습니다.")
            return []

    def start_blog(self, blog_id):
        self.total_pages = 0
        posts = []
        content = self.fetch_blog_page(blog_id)

        if content is None:  # fetch_blog_page에서 오류 발생 시
            return []

        numbers = self.extract_numbers_from_elements(content, "category_title pcol2")

        if numbers:
            self.total_pages = math.ceil(int(numbers[0]) / 10)

        if self.total_pages > 1:
            posts = self.fetch_post_titles(blog_id, 1)

        return posts


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
