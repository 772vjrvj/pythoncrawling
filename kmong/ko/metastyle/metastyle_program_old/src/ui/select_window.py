from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDesktopWidget, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from src.utils.singleton import GlobalState
from src.utils.config import SITE_CONFIGS

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

        # 버튼 정보 리스트
        sites = [(site_name, config["color"]) for site_name, config in SITE_CONFIGS.items()]

        for name, color in sites:
            button = self.create_site_button(name, color)
            layout.addWidget(button)

        self.center_window()


    def create_site_button(self, name, color):
        button = QPushButton(name, self)
        button.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        button.setFixedHeight(40)
        button.setFixedWidth(300)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda: self.select_site(name))
        return button



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
        if site == "":
            self.show_message("접속실패", "해당 사이트는 준비중 입니다...")
            return

        config = SITE_CONFIGS.get(site)

        if not config:
            self.show_message("접속실패", "해당 사이트 정보가 없습니다.")
            return

        # 상태 설정
        state = GlobalState()
        state.set("site", site)
        state.set("color", config.get("color", "#000"))
        state.set("check_list", list(config.get("check_list", {}).keys()))
        # 화면 전환
        self.close()
        self.app_manager.go_to_main()
