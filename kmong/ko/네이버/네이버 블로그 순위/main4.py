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

class MainWindow(QWidget):
    total_pages = 0
    page_group_size = 10

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["작성일", "제목", "순위 (키워드)", "PC", "MO", "SUM"])

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(self.pagination_layout)

        self.setLayout(main_layout)

        webbrowser.register('edge', None, webbrowser.BackgroundBrowser("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"))

    def create_page_buttons(self):
        # 기존 페이지 버튼 제거
        for i in reversed(range(self.pagination_layout.count())):
            widget = self.pagination_layout.itemAt(i).widget()
            if widget is not None:
                self.pagination_layout.removeWidget(widget)
                widget.deleteLater()

        total_page_groups = math.ceil(self.total_pages / self.page_group_size)
        start_page = self.current_page_group * self.page_group_size
        end_page = min(start_page + self.page_group_size, self.total_pages)

        # 버튼 생성
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

        # 페이지 버튼 생성
        for page_number in range(start_page, end_page):
            page_button = QPushButton(str(page_number + 1))  # 버튼 텍스트 설정
            page_button.setFixedSize(40, 30)

            # 각 버튼의 고유 클릭 이벤트 설정
            page_button.clicked.connect(lambda checked, btn=page_button, page=page_number: self.on_page_button_clicked(page, btn))
            self.pagination_layout.addWidget(page_button)

        self.pagination_layout.addWidget(next_button)
        self.pagination_layout.addWidget(last_button)
        self.pagination_layout.setAlignment(Qt.AlignCenter)


    def change_button_color(self, button):
        """버튼 색상을 변경하는 메서드입니다."""
        for i in range(self.pagination_layout.count()):
            widget = self.pagination_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setStyleSheet("background-color: #4CAF50; color: white;")  # 초록색으로 초기화
        button.setStyleSheet("background-color: blue; color: white;")  # 클릭된 버튼을 파란색으로 변경


    def set_column_widths(self):
        total_width = self.table.width()
        self.table.setColumnWidth(0, total_width * 150 // 1000)
        self.table.setColumnWidth(1, total_width * 477 // 1000)
        self.table.setColumnWidth(2, total_width * 200 // 1000)
        self.table.setColumnWidth(3, total_width * 50 // 1000)
        self.table.setColumnWidth(4, total_width * 50 // 1000)
        self.table.setColumnWidth(5, total_width * 50 // 1000)

    def load_table_data(self):
        start_row = self.current_page * self.rows_per_page
        end_row = start_row + self.rows_per_page
        page_data = self.data[start_row:end_row]

        self.table.setRowCount(len(page_data))

        for row_idx, row_data in enumerate(page_data):
            for col_idx, item in enumerate(row_data):
                if col_idx == 1:
                    title_item = QTableWidgetItem(item)
                    title_item.setTextAlignment(Qt.AlignCenter)
                    title_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    self.table.setItem(row_idx, col_idx, title_item)
                    self.table.item(row_idx, col_idx).setData(Qt.UserRole, "https://www.naver.com")
                    title_item.setBackground(Qt.transparent)
                    title_item.setForeground(Qt.blue)
                elif col_idx == 2:
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

        self.table.cellClicked.connect(self.on_cell_clicked)

    def on_cell_clicked(self, row, column):
        if column == 1:
            url = self.table.item(row, column).data(Qt.UserRole)
            if url:
                webbrowser.get('edge').open(url)

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
            posts = self.start_blog(blog_id)
            result_list = []
            for item in posts:
                row = [
                    item['addDate'],
                    item['title'],
                    '-',
                    '-',
                    '-',
                    '-'
                ]
                result_list.append(row)
            self.data = result_list
            self.load_table_data()
            self.create_page_buttons()
        else:
            self.show_alert("사용자 ID를 찾을 수 없습니다.")

    def extract_user_id(self, url):
        match = re.search(r'https?://blog\.naver\.com/([^/]+)/?', url)
        if match:
            return match.group(1)
        return None

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
        self.change_page(page_number)
        self.change_button_color(button)  # 클릭된 버튼 색상 변경
        print(f"{blog_id} ")
        print(f"{page_number + 1} 페이지 버튼 클릭")

    def on_keyword_search_clicked(self, keyword):
        sender = self.sender()
        sender.setText("찾는중")
        print(f"키워드 검색 버튼 클릭: {keyword}")
        QTimer.singleShot(2000, lambda: sender.setText("검색"))

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
                posts.append(post_data)
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
