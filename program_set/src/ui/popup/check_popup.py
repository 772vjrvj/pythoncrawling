from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
                             QMessageBox, QSpinBox,
                             QCheckBox, QDesktopWidget, QDialog)


# 개별등록 팝업창 클래스 (URL 입력)
class CheckPopup(QDialog):

    # 로그 메시지를 전달하는 시그널 정의
    check_list_signal = pyqtSignal(list)

    # 초기화
    def __init__(self, site, check_list):
        super().__init__()

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

        self.select_check_list = []
        self.site = site
        self.check_list = check_list
        self.setWindowTitle("크롤링 항목")
        self.setGeometry(200, 200, 500, 300)  # 팝업 창 크기 설정
        self.setStyleSheet("background-color: white;")

        # 제목과 밑줄
        title_layout = QHBoxLayout()
        title_label = QLabel(f"{site} 크롤링 항목 선택하기")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px;")
        title_layout.addWidget(title_label)
        title_layout.setAlignment(Qt.AlignCenter)

        # 체크박스 레이아웃 생성
        checkbox_layout = QVBoxLayout()

        site_layout = QHBoxLayout()

        self.checkboxes = []
        for name in check_list:
            # 가로로 배치할 레이아웃 생성
            row_layout = QHBoxLayout()

            # 체크박스 추가
            checkbox = QCheckBox(name)
            checkbox.setStyleSheet("margin-left: 20px;")  # 좌측 마진 20px 설정
            row_layout.addWidget(checkbox)

            # "시작" 라벨과 입력 박스 추가
            # start_label = QLabel("시작")
            # start_label.setAlignment(Qt.AlignRight)  # 텍스트 우측 정렬
            # row_layout.addWidget(start_label)
            # start_input = QSpinBox()
            # start_input.setFixedWidth(80)
            # start_input.setRange(1, 100000)  # 범위 설정
            # start_input.setValue(1)  # 기본값
            # row_layout.addWidget(start_input)

            # "종료" 라벨과 입력 박스 추가
            # end_label = QLabel("종료")
            # end_label.setAlignment(Qt.AlignRight)  # 텍스트 우측 정렬
            # row_layout.addWidget(end_label)
            # end_input = QSpinBox()
            # end_input.setFixedWidth(80)
            # end_input.setRange(1, 100000)  # 범위 설정
            # end_input.setValue(1000)  # 기본값
            # row_layout.addWidget(end_input)

            # 체크박스와 입력 박스 저장
            self.checkboxes.append({
                "checkbox": checkbox,
                # "start_input": start_input,
                # "end_input": end_input,
            })

            # 메인 레이아웃에 가로 레이아웃 추가
            checkbox_layout.addLayout(row_layout)


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
        popup_layout.addLayout(checkbox_layout)
        popup_layout.addLayout(button_layout)

        self.center_window()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 확인버튼
    def on_confirm(self):
        # 체크된 항목 수집
        self.select_check_list = []

        for item in self.checkboxes:
            checkbox = item["checkbox"]
            # start_input = item["start_input"]
            # end_input = item["end_input"]

            if checkbox.isChecked():
                # 입력값 가져오기
                # try:
                #     start_page = int(start_input.text())
                #     end_page = int(end_input.text())
                # except ValueError:
                #     self.show_error_message(f"'{checkbox.text()}'의 시작값과 종료값은 숫자여야 합니다.")
                #     return

                # 유효성 검사
                # if start_page <= 0 or end_page <= 0:
                #     self.show_error_message(f"'{checkbox.text()}'의 시작값과 종료값은 양수여야 합니다.")
                #     return
                #
                # if start_page > end_page:
                #     self.show_error_message(f"'{checkbox.text()}'의 시작값은 종료값보다 클 수 없습니다.")
                #     return

                # 결과 리스트에 추가
                self.select_check_list.append({
                    "name": checkbox.text(),
                    # "start_page": start_page,
                    # "end_page": end_page,
                })
        # 시그널로 체크된 항목 전달
        self.check_list_signal.emit(self.select_check_list)
        self.accept()  # 팝업 닫기


    def show_error_message(self, message):
        """에러 메시지 박스 표시"""
        QMessageBox.critical(self, "입력 오류", message)
