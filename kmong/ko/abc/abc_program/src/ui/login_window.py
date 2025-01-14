from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDesktopWidget, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor

from src.ui.select_window import SelectWindow
from src.workers.login_thread import LoginThread
from src.ui.password_change_window import PasswordChangeWindow

# 로그인 창
class LoginWindow(QWidget):
    
    # 초기화
    def __init__(self):
        super().__init__()

        self.setWindowTitle("로그인")

        # 동그란 파란색 원을 그린 아이콘 생성
        icon_pixmap = QPixmap(32, 32)  # 아이콘 크기 (64x64 픽셀)
        icon_pixmap.fill(QColor("transparent"))  # 투명 배경
        painter = QPainter(icon_pixmap)
        painter.setBrush(QColor("#e0e0e0"))  # 파란색 브러시
        painter.setPen(QColor("#e0e0e0"))  # 테두리 색상
        painter.drawRect(0, 0, 32, 32)  # 동그란 원 그리기 (좌상단 0,0에서 64x64 크기)
        painter.end()
        # 윈도우 아이콘 설정
        self.setWindowIcon(QIcon(icon_pixmap))

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
            background-color: #4682B4;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.login_button.setFixedHeight(40)
        self.login_button.setFixedWidth(140)  # 버튼 너비 설정
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)

        # 비밀번호 변경 버튼
        self.change_password_button = QPushButton("비밀번호 변경", self)
        self.change_password_button.setStyleSheet("""
            background-color: #4682B4;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.change_password_button.setFixedHeight(40)
        self.change_password_button.setFixedWidth(140)  # 버튼 너비 설정
        self.change_password_button.setCursor(Qt.PointingHandCursor)
        self.change_password_button.clicked.connect(self.change_password)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.change_password_button)
        button_layout.setSpacing(20)  # 버튼 간의 간격을 설정

        # 레이아웃에 요소 추가
        layout.addWidget(self.id_input)
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)
        self.center_window()

    # 화면 중앙배치
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 로그인
    def login(self):
        # ID와 비밀번호를 가져옴
        username = self.id_input.text()
        password = self.password_input.text()

        if not username or not password:
            self.show_message("로그인 실패", "아이디와 비밀번호를 입력해주세요.")
            return

        # 로그인 요청을 비동기적으로 처리하는 스레드 생성
        self.login_thread = LoginThread(username, password)
        self.login_thread.login_success.connect(self.main_window)  # 로그인 성공 시 메인 화면으로 전환
        self.login_thread.login_failed.connect(self.show_error_message)  # 로그인 실패 시 메시지 표시
        self.login_thread.start()  # 스레드 실행

    # 에러 메시지
    def show_error_message(self, message):
        """로그인 실패 메시지를 표시"""
        QMessageBox.critical(self, "로그인 실패", message)

    # 메시지 박스
    def show_message(self, title, message):
        """일반 메시지 박스"""
        QMessageBox.information(self, title, message)
    
    # 비밀번호 변경
    def change_password(self):
        popup = PasswordChangeWindow(parent=self)
        popup.exec_()

    # 메인 화면 실행
    def main_window(self, cookies):
        # 로그인 성공 시 메인 화면을 새롭게 생성
        self.close()  # 로그인 화면 종료
        self.select_screen = SelectWindow(cookies)
        self.select_screen.show()
