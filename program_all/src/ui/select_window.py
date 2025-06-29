from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QDesktopWidget, QMessageBox)
from src.core.global_state import GlobalState
from src.ui.style.style import create_common_button

from src.vo.site import Site


# 로그인 창
class SelectWindow(QWidget):

    # 초기화
    def __init__(self, app_manager, site_list):
        super().__init__()
        self.app_manager = app_manager
        self.sites = site_list
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

        for site in self.sites:
            button = create_common_button(
                site.label,
                partial(self.select_site, site),  # ✅ 함수 실행하지 않고 지연 실행 보장
                site.color,
                300
            )
            layout.addWidget(button)

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
        if not site.is_enabled():
            self.show_message("접속실패", f"{site.label}은(는) 준비 중입니다.")
            return

        state = GlobalState()
        state.set(GlobalState.NAME, site.label)
        state.set(GlobalState.SITE, site.key)
        state.set(GlobalState.COLOR, site.color)
        state.set(GlobalState.USER, site.user)
        state.set(GlobalState.SETTING, site.setting)
        state.set(GlobalState.COLUMNS, site.columns)
        state.set(GlobalState.REGION, site.region)

        self.close()
        self.app_manager.go_to_main()