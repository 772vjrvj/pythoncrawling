import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt
import webbrowser
from PyQt5.QtCore import QTimer


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 기본 설정
        self.setWindowTitle("카페 게시글 검색기")
        self.setGeometry(100, 100, 800, 720)

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
        """)

        # 데이터 및 페이징 설정
        self.current_page = 0
        self.rows_per_page = 10
        self.data = [
            ["2024-10-13", "광명시호프집 / 두다리 고척스카이돔 3루점 / 운영시간 가격 주차리뷰", "", "검색", "-", "-", "-"],
            ["2024-10-13", "광명시호프집 / 역전할머니맥주 개봉푸르지오점 / 운영시간 가격 주차리뷰", "", "검색", "-", "-", "-"],
        ]

        # 메인 레이아웃 설정
        main_layout = QVBoxLayout()

        # 검색 레이아웃
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("검색어를 입력하세요")
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["작성일", "제목", "링크", "순위 (키워드)", "PC", "MO", "SUM"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_table_data()

        # 페이징 버튼 레이아웃
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch(1)

        # 고정 버튼 추가
        first_button = QPushButton("처음")
        first_button.clicked.connect(self.on_first_clicked)
        prev_button = QPushButton("이전")
        prev_button.clicked.connect(self.on_prev_clicked)
        next_button = QPushButton("다음")
        next_button.clicked.connect(self.on_next_clicked)
        last_button = QPushButton("마지막")
        last_button.clicked.connect(self.on_last_clicked)

        pagination_layout.addWidget(first_button)
        pagination_layout.addWidget(prev_button)

        # 동적 페이지 버튼 최대 10개 추가
        self.page_buttons = []
        for i in range(10):
            page_button = QPushButton(str(i + 1))
            page_button.setFixedSize(40, 30)
            page_button.clicked.connect(lambda _, x=i: self.on_page_button_clicked(x))
            pagination_layout.addWidget(page_button)
            self.page_buttons.append(page_button)

        pagination_layout.addWidget(next_button)
        pagination_layout.addWidget(last_button)
        pagination_layout.addStretch(1)

        # 메인 레이아웃에 검색 창과 테이블 추가
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(pagination_layout)

        self.setLayout(main_layout)

    def load_table_data(self):
        # 현재 페이지에 해당하는 데이터를 테이블에 로드
        start_row = self.current_page * self.rows_per_page
        end_row = start_row + self.rows_per_page
        page_data = self.data[start_row:end_row]

        self.table.setRowCount(len(page_data))

        for row_idx, row_data in enumerate(page_data):
            for col_idx, item in enumerate(row_data):
                if col_idx == 1:
                    table_item = QTableWidgetItem(item)
                    table_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, table_item)

                    link_button = QPushButton("링크")
                    link_button.setFixedSize(40, 25)
                    link_button.clicked.connect(lambda: self.on_link_clicked(item))
                    self.table.setCellWidget(row_idx, col_idx + 1, link_button)
                elif col_idx == 3:
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

    # 버튼 이벤트 핸들러 함수
    def on_search_clicked(self):
        print("검색 버튼 클릭")

    def on_first_clicked(self):
        self.change_page(0)
        print("처음 버튼 클릭")

    def on_prev_clicked(self):
        self.change_page(self.current_page - 1)
        print("이전 버튼 클릭")

    def on_next_clicked(self):
        self.change_page(self.current_page + 1)
        print("다음 버튼 클릭")

    def on_last_clicked(self):
        self.change_page(len(self.data) // self.rows_per_page)
        print("마지막 버튼 클릭")

    def on_page_button_clicked(self, page_number):
        self.change_page(page_number)
        print(f"{page_number + 1} 페이지 버튼 클릭")

    def on_link_clicked(self, item):
        print(f"링크 버튼 클릭: {item}")
        url = "https://www.naver.com"
        edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"  # Edge 브라우저 경로
        webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
        webbrowser.get('edge').open(url)

    def on_keyword_search_clicked(self, keyword):
        sender = self.sender()  # 클릭된 버튼 가져오기
        sender.setText("찾는중")  # 버튼 텍스트를 '찾는중'으로 변경
        print(f"키워드 검색 버튼 클릭: {keyword}")

        # 타이머 설정하여 2초 후 다시 "검색"으로 텍스트 변경
        QTimer.singleShot(2000, lambda: sender.setText("3"))

    def change_page(self, page_number):
        if page_number < 0:
            page_number = 0
        elif page_number > len(self.data) // self.rows_per_page:
            page_number = len(self.data) // self.rows_per_page

        self.current_page = page_number
        self.load_table_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
