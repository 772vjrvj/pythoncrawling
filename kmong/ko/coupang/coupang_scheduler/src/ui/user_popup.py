from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
                             QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QDialog, QSizePolicy)


# 개별등록 팝업창 클래스 (URL 입력)
class UserPopup(QDialog):

    # 로그 메시지를 전달하는 시그널 정의
    # 생성된 객체에 속하는게 아니라 어떤 객체든 쓸수 있음 - 구성요소
    user_signal = pyqtSignal(str, str)

    # 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("계정등록")
        self.setGeometry(200, 200, 400, 200)  # 팝업 창 크기 설정 (X좌표, Y좌표, 너비, 높이
        self.setStyleSheet("background-color: white;")

        # 제목과 밑줄
        title_layout = QHBoxLayout()
        title_label = QLabel("쿠팡가격추적 계정등록하기")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.setAlignment(Qt.AlignCenter)

        # ID 입력
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("ID를 입력하세요")
        self.id_input.setStyleSheet("""
            border-radius: 10%;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.id_input.setFixedHeight(40)
        self.id_input.setText(self.parent.user_id)

        # PW 입력
        self.pw_input = QLineEdit(self)
        self.pw_input.setPlaceholderText("PASSWORD를 입력하세요")
        self.pw_input.setStyleSheet("""
            border-radius: 10%;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.pw_input.setFixedHeight(40)
        self.pw_input.setText(self.parent.user_pw)

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
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)

        # 팝업 레이아웃
        popup_layout = QVBoxLayout(self)
        popup_layout.addLayout(title_layout)
        popup_layout.addWidget(self.id_input)
        popup_layout.addWidget(self.pw_input)
        popup_layout.addLayout(button_layout)

        self.center_window()

    # 화면 중앙
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


    # 확인버튼
    def on_confirm(self):
        # URL 값을 전역 변수에 저장
        id = self.id_input.text()
        pw = self.pw_input.text()
        self.user_signal.emit(id, pw)
        self.accept()  # 팝업 닫기

