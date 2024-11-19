import sys
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QDialog, QTableWidget, QSizePolicy, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer



# 전역 변수
url = ""

# 로그인 API 요청을 처리하는 스레드 클래스
class LoginThread(QThread):
    # 로그인 성공 시 메인 화면을 띄우기 위한 시그널
    login_success = pyqtSignal()

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        # 여기서 로그인 API 호출 시뮬레이션
        print(f"로그인 시도: {self.username}, {self.password}")
        time.sleep(3)  # 실제 API 요청 시에는 time.sleep()을 API 호출로 대체

        # 로그인 성공 후 메인 화면 전환 시그널 발생
        self.login_success.emit()

# 로그인 화면 클래스
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("로그인 화면")
        self.setGeometry(100, 100, 500, 300)  # 화면 크기 설정
        self.setStyleSheet("background-color: #ffffff;")  # 배경색 흰색

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)  # 레이아웃의 외부 마진을 설정
        layout.setSpacing(20)  # 위젯 간 간격 설정

        # ID 입력
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("ID를 입력하세요")
        self.id_input.setStyleSheet("""
            border-radius: 20px; 
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.id_input.setFixedHeight(40)
        self.id_input.setFixedWidth(300)  # 너비를 화면의 절반 정도로 설정

        # 비밀번호 입력
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("비밀번호를 입력하세요")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            border-radius: 20px; 
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.password_input.setFixedHeight(40)
        self.password_input.setFixedWidth(300)  # 너비를 화면의 절반 정도로 설정

        # 로그인 버튼
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("로그인", self)
        self.login_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.login_button.setFixedHeight(40)
        self.login_button.setFixedWidth(140)  # 버튼 너비 설정
        self.login_button.clicked.connect(self.login)

        # 비밀번호 변경 버튼
        self.change_password_button = QPushButton("비밀번호 변경", self)
        self.change_password_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.change_password_button.setFixedHeight(40)
        self.change_password_button.setFixedWidth(140)  # 버튼 너비 설정
        self.change_password_button.clicked.connect(self.change_password)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.change_password_button)
        button_layout.setSpacing(20)  # 버튼 간의 간격을 설정

        # 레이아웃에 요소 추가
        layout.addWidget(self.id_input)
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)
        self.center_window()

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def login(self):
        # ID와 비밀번호를 가져옴
        username = self.id_input.text()
        password = self.password_input.text()

        # 로그인 요청을 비동기적으로 처리하는 스레드 생성
        self.login_thread = LoginThread(username, password)
        self.login_thread.login_success.connect(self.main_window)  # 로그인 성공 시 메인 화면으로 전환
        self.login_thread.start()  # 스레드 실행

    def change_password(self):
        # 비밀번호 변경 함수 (비워두기)
        print("비밀번호 변경 시도")

    def main_window(self):
        # 로그인 성공 시 메인 화면을 새롭게 생성
        self.close()  # 로그인 화면 종료
        self.main_screen = MainWindow()
        self.main_screen.show()


# 메인 화면 클래스
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("메인 화면")
        self.setGeometry(100, 100, 1000, 600)  # 메인 화면 크기 설정
        self.setStyleSheet("background-color: white;")  # 배경색 흰색

        # 메인 레이아웃
        main_layout = QVBoxLayout()

        # 상단 버튼들 레이아웃
        header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬

        # 버튼 설정
        self.register_button = QPushButton("등록하기")
        self.register_button.setStyleSheet("""
            background-color: black;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.register_button.setFixedWidth(150)  # 고정된 너비
        self.register_button.setFixedHeight(40)  # 고정된 높이
        self.register_button.clicked.connect(self.open_register_popup)


        self.collect_button = QPushButton("수집하기")
        self.collect_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.collect_button.setFixedWidth(150)  # 고정된 너비
        self.collect_button.setFixedHeight(40)  # 고정된 높이

        self.delete_button = QPushButton("삭제하기")
        self.delete_button.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.delete_button.setFixedWidth(150)  # 고정된 너비
        self.delete_button.setFixedHeight(40)  # 고정된 높이

        left_button_layout.addWidget(self.register_button)
        left_button_layout.addWidget(self.collect_button)
        left_button_layout.addWidget(self.delete_button)

        # 오른쪽 엑셀 다운로드 버튼 레이아웃
        right_button_layout = QHBoxLayout()
        right_button_layout.setAlignment(Qt.AlignRight)  # 오른쪽 정렬

        # 엑셀 다운로드 버튼
        self.excel_button = QPushButton("엑셀 다운로드")
        self.excel_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;;
            font-size: 16px;
            padding: 10px;
        """)
        self.excel_button.setFixedWidth(150)  # 고정된 너비
        self.excel_button.setFixedHeight(40)  # 고정된 높이

        right_button_layout.addWidget(self.excel_button)

        # 헤더에 "쿠팡(추적상품)" 텍스트 추가
        header_label = QLabel("쿠팡(추적상품)")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; background-color: white; color: black; padding: 10px;")

        # 테이블 만들기
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["선택", "URL", "상품명", "판매가", "배송비", "합계", "최근실행시간"])


        # 테이블을 부모 위젯 크기에 맞게 늘어나게 설정
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 열 크기 균등하게 설정
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)  # 모든 열을 균등하게 늘리기

        # URL 표시 레이블
        self.url_label = QLabel("URL : ")
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setStyleSheet("font-size: 16px; color: black; padding: 10px;")


        # 레이아웃에 요소 추가
        header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가
        header_layout.addLayout(right_button_layout)  # 오른쪽 엑셀 다운로드 버튼 추가

        main_layout.addLayout(header_layout)
        main_layout.addWidget(header_label)
        main_layout.addWidget(self.url_label)  # URL을 표시할 레이블 추가


        main_layout.addWidget(self.table)

        # 레이아웃 설정
        self.setLayout(main_layout)

        self.center_window()

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def open_register_popup(self):
        # 등록 팝업창 열기
        popup = RegisterPopup()
        popup.exec_()

        # 팝업창에서 URL을 입력 후 확인 버튼을 누르면 URL을 메인 화면에 표시
        self.update_url_label()

    def update_url_label(self):
        # URL을 레이블에 표시
        global url
        if url:  # URL이 존재하면
            self.url_label.setText(f"URL : {url}")
            print(f'{url}')
            # 타이머 생성
            self.timer = QTimer(self)
            # 1일마다 get_api 호출하도록 설정 (lambda로 지연 호출)
            self.timer.timeout.connect(lambda: self.get_api(url))
            # 타이머 시작: 1일 (86400000ms)
            # self.timer.start(86400000)  # 1일 = 86400000ms (1000 * 60 * 60 * 24)
            self.timer.start(2000)  # 1일 = 86400000ms (1000 * 60 * 60 * 24)
        else:
            self.url_label.setText("URL : ")

    def get_api(self, url):
        print(f'api 호출 : {url}')

        row_position = self.table.rowCount()  # 현재 테이블의 마지막 행 위치를 얻음
        self.table.insertRow(row_position)  # 새로운 행을 추가

        # 체크박스 추가 (삭제 시 사용)
        check_box = QCheckBox()
        self.table.setCellWidget(row_position, 0, check_box)

        # 데이터 추가
        for column, data in enumerate(["www.naver.com", "상품1", "10000", "2000", "12000", "2024-11-19"]):
            self.table.setItem(row_position, column + 1, QTableWidgetItem(data))  # 첫 번째 열은 체크박스라 1부터 시작


# 팝업창 클래스 (URL 입력)
class RegisterPopup(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("쿠팡가격추적 등록하기")
        self.setGeometry(200, 200, 400, 200)  # 팝업 창 크기 설정
        self.setStyleSheet("background-color: white;")

        # 팝업 레이아웃
        popup_layout = QVBoxLayout(self)

        # 제목과 밑줄
        title_layout = QHBoxLayout()
        title_label = QLabel("쿠팡가격추적 등록하기")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.setAlignment(Qt.AlignCenter)
        popup_layout.addLayout(title_layout)


        # URL 입력
        url_label = QLabel("이름 : URL")
        url_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("URL을 입력하세요")
        self.url_input.setStyleSheet("""
            border-radius: 10%;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.url_input.setFixedHeight(40)



        # 버튼
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("확인", self)
        self.confirm_button.setStyleSheet("""
            background-color: black;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.confirm_button.setFixedHeight(40)
        self.confirm_button.setFixedWidth(140)  # 버튼 너비 설정
        self.confirm_button.clicked.connect(self.on_confirm)

        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)
        popup_layout.addWidget(self.url_input)
        popup_layout.addLayout(button_layout)

        self.center_window()

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


    def on_confirm(self):
        # URL 값을 전역 변수에 저장
        global url
        url = self.url_input.text()
        print(f"입력한 URL: {url}")  # 콘솔에 출력 (디버그용)
        self.accept()  # 팝업 닫기


# 프로그램 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
