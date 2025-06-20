from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDesktopWidget, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from src.utils.singleton import GlobalState

# 로그인 창
class SelectWindow(QWidget):
    
    # 초기화
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.set_layout()

    def set_layout(self):
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

        self.setWindowTitle("사이트")
        self.setGeometry(100, 100, 500, 500)  # 화면 크기 설정
        self.setStyleSheet("background-color: #ffffff;")  # 배경색 흰색

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)  # 레이아웃의 외부 마진을 설정
        layout.setSpacing(20)  # 위젯 간 간격 설정

        # 알바몬
        site_button_first = QPushButton("알바몬", self)
        site_button_first.setStyleSheet("""
            background-color: #FF6600;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        site_button_first.setFixedHeight(40)
        site_button_first.setFixedWidth(300)  # 버튼 너비 설정
        site_button_first.setCursor(Qt.PointingHandCursor)
        site_button_first.clicked.connect(lambda: self.select_site("albamon"))


        # 알바천국
        site_button_second = QPushButton("알바천국", self)
        site_button_second.setStyleSheet("""
            background-color: #3D3D3D;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        site_button_second.setFixedHeight(40)
        site_button_second.setFixedWidth(300)  # 버튼 너비 설정
        site_button_second.setCursor(Qt.PointingHandCursor)
        site_button_second.clicked.connect(lambda: self.select_site("alba"))


        # 레이아웃에 요소 추가
        layout.addWidget(site_button_first)
        layout.addWidget(site_button_second)

        self.center_window()



    # 화면 중앙배치
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 메시지 박스
    def show_message(self, title, message):
        """일반 메시지 박스"""
        QMessageBox.information(self, title, message)


    # 메인 화면 실행
    def select_site(self, site):

        if site == "alba":
            self.show_message("접속실패", "해당 사이트는 준비중 입니다...")
            return None
        else:

            if site == "albamon":
                color = "#FF6600"
                check_list = []
            elif site == "alba":
                color = "#3D3D3D"
                check_list = []
            else:
                color = ""
                check_list = []

            state = GlobalState()
            state.set("site", site)
            state.set("color", color)
            state.set("check_list", check_list)

            # 로그인 성공 시 메인 화면을 새롭게 생성
            self.close()  # 로그인 화면 종료
            self.app_manager.go_to_main()
