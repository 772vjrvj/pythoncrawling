from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDesktopWidget, QMessageBox)
import requests
from src.workers.change_password_woker import ChangePasswordWorker

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
        self.id_input.setFixedWidth(300)

        # 현재 비밀번호 입력
        self.current_password_input = QLineEdit(self)
        self.current_password_input.setPlaceholderText("현재 비밀번호를 입력하세요")
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setStyleSheet("""
            border-radius: 20px;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.current_password_input.setFixedHeight(40)
        self.current_password_input.setFixedWidth(300)

        # 새 비밀번호 입력
        self.new_password_input = QLineEdit(self)
        self.new_password_input.setPlaceholderText("새 비밀번호를 입력하세요")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setStyleSheet("""
            border-radius: 20px;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.new_password_input.setFixedHeight(40)
        self.new_password_input.setFixedWidth(300)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 비밀번호 변경 버튼
        self.change_button = QPushButton("비밀번호 변경", self)
        self.change_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.change_button.setFixedHeight(40)
        self.change_button.setFixedWidth(140)
        self.change_button.setCursor(Qt.PointingHandCursor)
        self.change_button.clicked.connect(self.change_password)

        # 취소 버튼
        self.cancel_button = QPushButton("취소", self)
        self.cancel_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setFixedWidth(140)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.cancel_change)

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
