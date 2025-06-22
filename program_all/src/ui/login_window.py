from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDesktopWidget, QMessageBox,
                             QCheckBox)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor

from src.ui.style.style import create_line_edit, create_common_button
from src.workers.login_worker import LoginWorker
from src.ui.password_change_window import PasswordChangeWindow
from src.core.global_state import GlobalState

import keyring
from src.utils.config import server_name  # 서버 URL 및 설정 정보


class LoginWindow(QWidget):
    # 초기화
    def __init__(self, app_manager):
        super().__init__()

        self.app_manager = app_manager
        self.login_worker = None
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

        self.id_input       = create_line_edit("ID를 입력하세요", False, "#888888", 300)
        self.password_input = create_line_edit("비밀번호를 입력하세요", True, "#888888", 300)


        # 자동 로그인 체크박스 (init 내부에서)
        self.auto_login_checkbox = QCheckBox("자동 로그인", self)
        self.auto_login_checkbox.setCursor(Qt.PointingHandCursor)  # 손가락 모양
        self.auto_login_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #444;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #888;
                background-color: #f0f0f0;
            }
            QCheckBox::indicator:checked {
                background-color: #4682B4;
                image: url();
            }
        """)
        self.auto_login_checkbox.setChecked(False)


        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        self.login_button = create_common_button("로그인", self.login, "#4682B4", 140)
        self.change_password_button = create_common_button("비밀번호 변경", self.change_password, "#4682B4", 140)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.change_password_button)
        button_layout.setSpacing(20)  # 버튼 간의 간격을 설정

        # 레이아웃에 요소 추가
        layout.addWidget(self.id_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.auto_login_checkbox)
        layout.addLayout(button_layout)
        self.center_window()

        # ✅ 자동 로그인 시도
        self.try_auto_login()

    def try_auto_login(self):
        try:
            username = keyring.get_password(server_name, "username")
            password = keyring.get_password(server_name, "password")
            if username and password:
                self.id_input.setText(username)
                self.password_input.setText(password)
                self.auto_login_checkbox.setChecked(True)
                self.login()  # 자동 로그인 실행
        except Exception:
            pass

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

        self.login_worker = LoginWorker(username, password)
        self.login_worker.login_success.connect(self.main_window)
        self.login_worker.login_failed.connect(self.show_error_message)
        self.login_worker.start()

    # 에러 메시지
    def show_error_message(self, message):
        QMessageBox.critical(self, "로그인 실패", message)

    # 메시지 박스
    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

    # 비밀번호 변경
    def change_password(self):
        popup = PasswordChangeWindow(parent=self)
        popup.exec_()

    # 메인 화면 실행
    def main_window(self, cookies):
        state = GlobalState()
        state.set("cookies", cookies)

        # 자동 로그인 체크 시 저장
        if self.auto_login_checkbox.isChecked():
            username = self.id_input.text()
            password = self.password_input.text()
            keyring.set_password(server_name, "username", username)
            keyring.set_password(server_name, "password", password)
        else:
            # 체크 해제된 경우 저장된 정보 제거
            try:
                keyring.delete_password(server_name, "username")
                keyring.delete_password(server_name, "password")
            except keyring.errors.PasswordDeleteError:
                pass

        self.close()  # 로그인 화면 종료
        self.app_manager.go_to_select()
