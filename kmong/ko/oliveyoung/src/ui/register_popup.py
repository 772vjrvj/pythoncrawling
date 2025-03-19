from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
                             QDesktopWidget, QDialog)


# 개별등록 팝업창 클래스 (ID & PASSWORD 입력)
class RegisterPopup(QDialog):

    # 로그 메시지를 전달하는 시그널 정의
    update_obj = pyqtSignal(dict)  # dict 타입으로 변경

    # 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.setWindowTitle("계정등록")
        self.setGeometry(200, 200, 400, 200)  # 팝업 창 크기 설정 (X좌표, Y좌표, 너비, 높이)
        self.setStyleSheet("background-color: white;")

        # 팝업 레이아웃
        popup_layout = QVBoxLayout(self)

        # 제목과 밑줄
        title_layout = QHBoxLayout()
        title_label = QLabel("계정등록하기")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.setAlignment(Qt.AlignCenter)
        popup_layout.addLayout(title_layout)

        # ID 입력
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("ID를 입력하세요")
        self.id_input.setStyleSheet("""
            border-radius: 10px;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.id_input.setFixedHeight(40)

        # PASSWORD 입력
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("PASSWORD를 입력하세요")
        self.password_input.setEchoMode(QLineEdit.Password)  # 비밀번호 입력 필드로 설정
        self.password_input.setStyleSheet("""
            border-radius: 10px;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.password_input.setFixedHeight(40)

        # 버튼 레이아웃
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
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)

        popup_layout.addWidget(self.id_input)
        popup_layout.addWidget(self.password_input)
        popup_layout.addLayout(button_layout)

        self.center_window()

    # 화면 중앙 배치
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 확인 버튼 클릭 이벤트
    def on_confirm(self):
        """ID와 PASSWORD를 받아서 시그널로 전송"""
        id_input = self.id_input.text().strip()
        password_input = self.password_input.text().strip()

        user_data = {
            'ID': id_input,
            'PASSWORD': password_input
        }

        self.update_obj.emit(user_data)  # dict 타입으로 시그널 전달
        self.accept()  # 팝업 닫기
