from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
                             QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QDialog, QSizePolicy)


# 개별등록 팝업창 클래스 (URL 입력)
class RegisterPopup(QDialog):

    # 로그 메시지를 전달하는 시그널 정의
    # 생성된 객체에 속하는게 아니라 어떤 객체든 쓸수 있음 - 구성요소
    log_signal = pyqtSignal(str)


    # 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.setWindowTitle("개별등록")
        self.setGeometry(200, 200, 400, 200)  # 팝업 창 크기 설정 (X좌표, Y좌표, 너비, 높이
        self.setStyleSheet("background-color: white;")

        # 팝업 레이아웃
        popup_layout = QVBoxLayout(self)

        # 제목과 밑줄
        title_layout = QHBoxLayout()
        title_label = QLabel("쿠팡가격추적 개별등록하기")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.setAlignment(Qt.AlignCenter)
        popup_layout.addLayout(title_layout)

        # URL 입력
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
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)

        popup_layout.addWidget(self.url_input)
        popup_layout.addLayout(button_layout)

        self.center_window()

    # 화면 중앙
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 전역 url 업데이트
    # 사실은 slot signal로 데이터만 보내고 처리는 부모에서 하는게 맞음 이러면 응집도가 너무 높아짐
    # 일단은 그냥 둠
    def update_url_label(self, url):
        # URL을 레이블에 표시
        row_position = self.parent.table.rowCount()  # 현재 테이블의 마지막 행 위치를 얻음
        self.parent.table.insertRow(row_position)  # 새로운 행을 추가

        check_box = QCheckBox()

        # 체크박스를 감싸는 레이아웃
        layout = QHBoxLayout()
        layout.addWidget(check_box)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거

        # 레이아웃과 컨테이너 위젯의 크기 정책 설정
        container_widget = QWidget()
        container_widget.setLayout(layout)
        container_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 정책 설정 수평수직 부모에 맞게


        # 테이블 셀에 추가
        self.parent.table.setCellWidget(row_position, 0, container_widget)

        # URL 열 (1번 열) 업데이트
        self.parent.table.setItem(row_position, 6, QTableWidgetItem(url))

        # 로그 시그널 발생
        self.log_signal.emit('1개의 행이 추가 되었습니다.')

    # 확인버튼
    def on_confirm(self):
        # URL 값을 전역 변수에 저장
        url = self.url_input.text()
        if url:
            self.update_url_label(url)
        self.accept()  # 팝업 닫기

