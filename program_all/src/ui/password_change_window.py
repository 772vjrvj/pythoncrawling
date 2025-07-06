from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDesktopWidget, QMessageBox)
from src.workers.change_password_woker import ChangePasswordWorker
from src.ui.style.style import main_style, create_line_edit, create_common_button
import requests


class PasswordChangeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 창 저장 (로그인 창)

        self.setWindowTitle("비밀번호 변경")
        self.setGeometry(100, 100, 500, 300)
        self.setStyleSheet("background-color: #ffffff;")

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 아이디 입력
        self.id_input = create_line_edit("ID를 입력하세요", False, "#888888", 300)

        # 현재 비밀번호 입력
        self.current_password_input = create_line_edit("현재 비밀번호를 입력하세요", True, "#888888", 300)


        # 새 비밀번호 입력
        self.new_password_input = create_line_edit("새 비밀번호를 입력하세요", True, "#888888", 300)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 비밀번호 변경 버튼
        self.change_button = create_common_button("비밀번호 변경", self.change_password, "#4682B4", 140)

        # 취소 버튼
        self.cancel_button = create_common_button("취소", self.cancel_change, "#4682B4", 140)

        button_layout.addWidget(self.change_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.setSpacing(20)

        # 레이아웃에 요소 추가
        layout.addWidget(self.id_input)
        layout.addWidget(self.current_password_input)
        layout.addWidget(self.new_password_input)
        layout.addLayout(button_layout)
        self.center_window()

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def change_password(self):
        """비밀번호 변경 요청"""
        user_id = self.id_input.text()
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()

        if not user_id or not current_password or not new_password:
            QMessageBox.warning(self, "입력 오류", "모든 필드를 입력해주세요.")
            return

        session = requests.Session()

        # ChangePasswordWorker 인스턴스 생성
        self.change_password_worker = ChangePasswordWorker(session, user_id, current_password, new_password)

        # 성공 및 실패 시그널 연결
        self.change_password_worker.password_change_success.connect(self.on_password_change_success)
        self.change_password_worker.password_change_failed.connect(self.on_password_change_failed)

        # 스레드 시작
        self.change_password_worker.start()

    def on_password_change_success(self):
        """비밀번호 변경 성공 콜백"""
        QMessageBox.information(self, "성공", "비밀번호가 성공적으로 변경되었습니다.")
        self.cancel_change()  # 비밀번호 변경 후 로그인 창으로 이동

    def on_password_change_failed(self, message):
        """비밀번호 변경 실패 콜백"""
        QMessageBox.critical(self, "실패", f"비밀번호 변경에 실패했습니다: {message}")


    def cancel_change(self):
        """취소 버튼을 눌렀을 때 로그인 창으로 이동"""
        self.close()  # 비밀번호 변경 창 닫기
        if self.parent:
            self.parent.show()  # 부모 창(로그인 창) 다시 표시
