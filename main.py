import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt, QSize
import webbrowser
from PyQt5.QtCore import QTimer
import requests
from bs4 import BeautifulSoup
import re
import math
import urllib.parse
import json
from PyQt5.QtWidgets import QMessageBox


class MainWindow(QWidget):

    total_pages = 0  # 클래스 변수로 total_pages 선언

    def __init__(self):
        super().__init__()

        # 기본 설정
        self.setWindowTitle("카페 게시글 검색기")
        self.setGeometry(100, 100, 1000, 720)

        # 스타일 설정
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

        # 데이터 및 페이징 설정
        self.current_page = 0
        self.rows_per_page = 10
        self.data = []
        self.now_page = 1  # now_page 인스턴스 변수 초기화

        # 메인 레이아웃 설정
        main_layout = QVBoxLayout()
        self.pagination_layout = QHBoxLayout()  # pagination_layout 초기화

        # 검색 레이아웃 설정
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("블로그 주소를 입력하세요")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.on_search_clicked)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # 로딩 애니메이션 및 결과 텍스트
        self.loading_label = QLabel()
        self.loading_label.setFixedSize(50, 50)
        self.loading_label.setVisible(False)
        search_layout.addWidget(self.loading_label)

        # 테이블 설정
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)  # 컬럼 수를 6으로 수정
        self.table.setHorizontalHeaderLabels(["작성일", "제목", "순위 (키워드)", "PC", "MO", "SUM"])  # 헤더 수정

        # 메인 레이아웃에 검색 창과 테이블 추가
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(self.pagination_layout)  # 페이지 레이아웃 추가

        main_layout.addLayout(self.pagination_layout)  # 페이지 레이아웃 추가

        self.setLayout(main_layout)

        # 엣지 웹 브라우저 등록
        webbrowser.register('edge', None, webbrowser.BackgroundBrowser("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"))

    def create_page_buttons(self):
        """페이지 버튼을 동적으로 생성하여 레이아웃에 추가합니다."""
        self.page_buttons = []  # 페이지 버튼 초기화

        # 최대 10개의 페이지 버튼 생성
        num_buttons = min(self.total_pages, 10)  # total_pages와 10 중 작은 값 선택

        """페이지 탐색 버튼을 생성하여 레이아웃에 추가합니다."""
        first_button = QPushButton("처음")
        first_button.clicked.connect(self.on_first_clicked)
        prev_button = QPushButton("이전")
        prev_button.clicked.connect(self.on_prev_clicked)
        next_button = QPushButton("다음")
        next_button.clicked.connect(self.on_next_clicked)
        last_button = QPushButton("마지막")
        last_button.clicked.connect(self.on_last_clicked)

        # 버튼 크기 조정
        first_button.setFixedSize(80, 30)
        prev_button.setFixedSize(80, 30)
        next_button.setFixedSize(80, 30)
        last_button.setFixedSize(80, 30)

        self.pagination_layout.addWidget(first_button)
        self.pagination_layout.addWidget(prev_button)

        for i in range(num_buttons):
            page_button = QPushButton(str(i + 1))
            page_button.setFixedSize(40, 30)  # 페이지 버튼 크기 설정
            page_button.clicked.connect(lambda _, x=i: self.on_page_button_clicked(x))
            self.page_buttons.append(page_button)  # 생성한 버튼을 리스트에 추가
            self.pagination_layout.addWidget(page_button)  # 버튼을 레이아웃에 추가

        self.pagination_layout.addWidget(next_button)
        self.pagination_layout.addWidget(last_button)


    # 컬럼의 너비를 설정하여 테이블이 적절하게 보이도록 합니다.
    def set_column_widths(self):
        total_width = self.table.width()

        # 최소한의 너비를 설정하여 모든 컬럼이 적절히 보이도록 합니다.
        self.table.setColumnWidth(0, total_width * 150 // 1000)   # 작성일: 약 100px (1)
        self.table.setColumnWidth(1, total_width * 477 // 1000)  # 제목: 약 400px (4)
        self.table.setColumnWidth(2, total_width * 200 // 1000)  # 순위 (키워드): 약 200px (2)
        self.table.setColumnWidth(3, total_width * 50 // 1000)   # PC: 약 100px (1)
        self.table.setColumnWidth(4, total_width * 50 // 1000)   # MO: 약 100px (1)
        self.table.setColumnWidth(5, total_width * 50 // 1000)   # SUM: 약 100px (1)

    # 현재 페이지에 해당하는 데이터를 테이블에 로드합니다.
    def load_table_data(self):
        start_row = self.current_page * self.rows_per_page
        end_row = start_row + self.rows_per_page
        page_data = self.data[start_row:end_row]

        self.table.setRowCount(len(page_data))

        for row_idx, row_data in enumerate(page_data):
            for col_idx, item in enumerate(row_data):
                if col_idx == 1:  # 제목 클릭 시 브라우저 열기
                    title_item = QTableWidgetItem(item)
                    title_item.setTextAlignment(Qt.AlignCenter)
                    title_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 클릭 가능하도록 설정
                    self.table.setItem(row_idx, col_idx, title_item)
                    self.table.item(row_idx, col_idx).setData(Qt.UserRole, "https://www.naver.com")  # URL 저장
                    # 스타일링: 파란색 글자에 아래줄 추가
                    title_item.setBackground(Qt.transparent)  # 배경을 투명하게 설정
                    title_item.setForeground(Qt.blue)  # 글자색을 파란색으로 설정
                elif col_idx == 2:  # '검색' 버튼 추가
                    keyword_layout = QHBoxLayout()
                    keyword_input = QLineEdit()
                    keyword_button = QPushButton("검색")
                    keyword_button.clicked.connect(lambda: self.on_keyword_search_clicked(keyword_input.text()))
                    keyword_layout.addWidget(keyword_input)
                    keyword_layout.addWidget(keyword_button)
                    keyword_layout.setContentsMargins(0, 0, 0, 0)
                    widget = QWidget()
                    widget.setLayout(keyword_layout)
                    self.table.setCellWidget(row_idx, col_idx, widget)
                else:
                    table_item = QTableWidgetItem(item)
                    table_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, table_item)

        # 제목 클릭 이벤트 연결
        self.table.cellClicked.connect(self.on_cell_clicked)

    # 셀 클릭 이벤트 핸들러로, 제목 열 클릭 시 URL을 엣지 브라우저로 엽니다.
    def on_cell_clicked(self, row, column):
        if column == 1:  # 제목 열 클릭
            url = self.table.item(row, column).data(Qt.UserRole)  # 저장된 URL 가져오기
            if url:
                webbrowser.get('edge').open(url)  # 웹브라우저에서 URL 열기

    def show_alert(self, message):
        """알림창을 띄우는 메서드입니다."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)  # 경고 아이콘 설정
        msg_box.setText(message)  # 메시지 설정
        msg_box.setWindowTitle("경고")  # 창 제목 설정
        msg_box.setStandardButtons(QMessageBox.Ok)  # 확인 버튼 추가
        msg_box.exec_()  # 알림창 실행

    # 검색 버튼 클릭 시 호출되는 메서드입니다.
    def on_search_clicked(self):
        search_text = self.search_input.text()
        print(f"입력된 URL: {search_text}")

        # 정규 표현식을 사용하여 사용자 ID를 추출합니다.
        user_id = self.extract_user_id(search_text)

        # 데이터 세팅
        if user_id:
            posts = self.start_blog(user_id)
            # ["작성일", "제목", "순위 (키워드)", "PC", "MO", "SUM"]
            result_list = []
            for item in posts:
                row = [
                    item['addDate'],              # 작성일
                    item['title'],                # 제목
                    '-',                          # 순위 (키워드) (여기서는 '-')
                    '-',                          # PC (여기서는 '-')
                    '-',                          # MO (여기서는 '-')
                    '-'                           # SUM (여기서는 '-')
                ]
                result_list.append(row)
            self.data = result_list
            self.load_table_data()

            self.create_page_buttons()  # 페이지 버튼 생성 함수 호출


        else:
            # 사용자 ID를 찾을 수 없을 경우 알림창 띄우기
            self.show_alert("사용자 ID를 찾을 수 없습니다.")

    def extract_user_id(self, url):
        """URL에서 사용자 ID를 추출합니다."""
        match = re.search(r'https?://blog\.naver\.com/([^/]+)/?', url)
        if match:
            return match.group(1)  # 그룹 1의 값을 반환
        return None  # 일치하는 값이 없을 경우 None 반환

    # 처음 버튼 클릭 시 호출되어 첫 페이지로 이동합니다.
    def on_first_clicked(self):
        self.change_page(0)
        print("처음 버튼 클릭")

    # 이전 버튼 클릭 시 호출되어 이전 페이지로 이동합니다.
    def on_prev_clicked(self):
        self.change_page(self.current_page - 1)
        print("이전 버튼 클릭")

    # 다음 버튼 클릭 시 호출되어 다음 페이지로 이동합니다.
    def on_next_clicked(self):
        self.change_page(self.current_page + 1)
        print("다음 버튼 클릭")

    # 마지막 버튼 클릭 시 호출되어 마지막 페이지로 이동합니다.
    def on_last_clicked(self):
        self.change_page(len(self.data) // self.rows_per_page)
        print("마지막 버튼 클릭")

    # 페이지 버튼 클릭 시 호출되어 해당 페이지로 이동합니다.
    def on_page_button_clicked(self, page_number):
        self.change_page(page_number)
        print(f"{page_number + 1} 페이지 버튼 클릭")

    # 키워드 검색 버튼 클릭 시 호출되어 검색 동작을 수행합니다.
    def on_keyword_search_clicked(self, keyword):
        sender = self.sender()  # 클릭된 버튼 가져오기
        sender.setText("찾는중")  # 버튼 텍스트를 '찾는중'으로 변경
        print(f"키워드 검색 버튼 클릭: {keyword}")

        # 타이머 설정하여 2초 후 다시 "검색"으로 텍스트 변경
        QTimer.singleShot(2000, lambda: sender.setText("검색"))

    # 페이지 번호를 변경하고 데이터를 로드합니다.
    def change_page(self, page_number):
        if page_number < 0:
            page_number = 0
        elif page_number > len(self.data) // self.rows_per_page:
            page_number = len(self.data) // self.rows_per_page

        self.current_page = page_number
        self.load_table_data()

    # 윈도우 리사이즈 시 호출되어 컬럼 너비를 조정합니다.
    def resizeEvent(self, event):
        self.set_column_widths()
        super().resizeEvent(event)

    # ========== 블로그 게시글 조회 [시작] ==========
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
        response = requests.get(url, headers=headers)
        return response.content

    # 전체 게시글 수
    def extract_numbers_from_elements(self, content, class_name):
        soup = BeautifulSoup(content, 'html.parser')
        elements = soup.find_all(class_=class_name)
        numbers = []
        for element in elements:
            text = element.get_text()
            numbers.extend(re.findall(r'\d+', text))
        return numbers


    def fetch_post_titles(self, blog_id, current_page):
        url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={blog_id}&viewdate=&currentPage={current_page}&categoryNo=&parentCategoryNo=&countPerPage=10"
        headers = {
            "authority": "blog.naver.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            try:
                # JSON 데이터를 올바르게 파싱하기 위해 불필요한 백슬래시를 제거
                cleaned_text = re.sub(r'\\(?!["\\/bfnrt])', "", response.text)  # 잘못된 백슬래시 패턴 제거
                data = json.loads(cleaned_text)  # JSON 파싱

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
                    posts.append(post_data)
                return posts

            except json.JSONDecodeError as e:
                print("JSONDecodeError 발생:", e)
                print("응답 텍스트:", response.text)
                return []
        else:
            print("Error: 요청이 실패했습니다.")
            return []

    # 블로그 조회 최초 시작 전체 페이지수 가져오기 첫 페이지 가져오기
    def start_blog(self, blog_id):
        self.total_pages = 0  # 클래스 변수 초기화
        posts = []
        content = self.fetch_blog_page(blog_id)

        # 전체 페이지 및 1페이지 글

        # 전체 개수글 수
        numbers = self.extract_numbers_from_elements(content, "category_title pcol2")


        # 전체 페이지
        if numbers:  # numbers 리스트가 비어있지 않을 경우
            self.total_pages = math.ceil(int(numbers[0]) / 10)  # 클래스 변수에 저장

        if self.total_pages > 1:
            posts = self.fetch_post_titles(blog_id, 1)

        return posts  # 클래스 변수를 포함하여 반환

    # ========== 블로그 게시글 조회 [시작] ==========

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
