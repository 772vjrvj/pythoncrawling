from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QFrame, QHBoxLayout, QSizePolicy, QWidget, QPushButton, QDesktopWidget, QDialog
)
import requests

from src.ui.login_Info_dialog import LoginInfoDialog
from src.ui.store_Info_dialog import StoreInfoDialog
from src.workers.api_golfzonpark_set_worker import ApiGolfzonparkSetLoadWorker
from src.utils.log import log

class LoginWindow(QWidget):
    # 초기화
    def __init__(self):
        super().__init__()
        self.on_demand_worker = None
        self.login_thread = None
        self.setWindowTitle("PandoGL")

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


        # 상태 수집 헤더 영역 ====================================
        status_header_layout = QHBoxLayout()
        status_header_layout.setContentsMargins(0, 0, 0, 0)
        status_header_layout.setSpacing(6)

        # 큰 제목
        status_title_label = QLabel("PandoGL")
        status_title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
            color: #222222;
        """)

        # 작은 설명
        status_sub_label = QLabel("상태 수집중...")
        status_sub_label.setStyleSheet("""
            font-size: 12px;
            color: #777777;
        """)

        # 아래 정렬로 같은 선상 배치
        status_header_layout.addWidget(status_title_label, alignment=Qt.AlignLeft | Qt.AlignBottom)
        status_header_layout.addWidget(status_sub_label, alignment=Qt.AlignLeft | Qt.AlignBottom)
        status_header_layout.addStretch()


        # 매장 정보 박스 프레임 ====================================
        store_group = QFrame(self)
        store_group.setFrameShape(QFrame.StyledPanel)
        store_group.setStyleSheet("""
            QFrame {
                border: 1px solid #cccccc;
                border-radius: 1px;
                background-color: #ffffff;
            }
        """)
        store_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        store_layout = QVBoxLayout(store_group)
        store_layout.setContentsMargins(15, 10, 15, 10)
        store_layout.setSpacing(4)

        # 타이틀
        self.store_info_label = QLabel("매장 정보")
        self.store_info_label.setAlignment(Qt.AlignLeft)
        self.store_info_label.setFrameShape(QFrame.NoFrame)  # 테두리 제거
        self.store_info_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 15px; 
            color: #222222;
            border: none;
            padding: 5px 0;
        """)

        # 항목
        self.store_info_main_label = QLabel("• 매장명 : -")
        self.store_info_main_label.setAlignment(Qt.AlignLeft)
        self.store_info_main_label.setFrameShape(QFrame.NoFrame)
        self.store_info_main_label.setStyleSheet("""
            font-size: 13px; 
            color: #444444; 
            border: none;
            padding: 5px 0;
        """)

        self.store_info_local_label = QLabel("• 지   점 : -")
        self.store_info_local_label.setAlignment(Qt.AlignLeft)
        self.store_info_local_label.setFrameShape(QFrame.NoFrame)
        self.store_info_local_label.setStyleSheet("""
            font-size: 13px; 
            color: #444444; 
            border: none;
            padding: 5px 0;
        """)

        # 레이아웃에 추가
        store_layout.addWidget(self.store_info_label)
        store_layout.addWidget(self.store_info_main_label)
        store_layout.addWidget(self.store_info_local_label)


        # 로그인 등록 정보 박스 프레임 ====================================
        login_set_group = QFrame(self)
        login_set_group.setFrameShape(QFrame.StyledPanel)
        login_set_group.setStyleSheet("""
            QFrame {
                border: 1px solid #cccccc;
                border-radius: 1px;
                background-color: #ffffff;
            }
        """)
        login_set_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        login_layout = QVBoxLayout(login_set_group)
        login_layout.setContentsMargins(15, 10, 15, 10)
        login_layout.setSpacing(4)

        # 수평 레이아웃 (텍스트 + 버튼)
        login_title_layout = QHBoxLayout()
        login_title_layout.setContentsMargins(0, 0, 0, 0)
        login_title_layout.setSpacing(0)

        # 타이틀 라벨
        self.login_info_label = QLabel("로그인 정보")
        self.login_info_label.setAlignment(Qt.AlignLeft)
        self.login_info_label.setFrameShape(QFrame.NoFrame)
        self.login_info_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 15px; 
            color: #222222;
            border: none;
            padding: 5px 0;
        """)

        # 등록 버튼
        self.login_register_button = QPushButton("등록")
        self.login_register_button.setCursor(Qt.PointingHandCursor)
        self.login_register_button.setFixedHeight(28)
        self.login_register_button.setStyleSheet("""
            background-color: #4682B4;
            color: white;
            border-radius: 5px;
            font-size: 13px;
            padding: 5px 40px;
        """)
        self.login_register_button.clicked.connect(self.register_login_info)

        # 수평 레이아웃에 추가 (왼쪽 라벨, 오른쪽 버튼)
        login_title_layout.addWidget(self.login_info_label)
        login_title_layout.addStretch(1)  # 공간 채우기 → 버튼을 오른쪽으로 밀어줌
        login_title_layout.addWidget(self.login_register_button)

        # 박스에 수평 레이아웃 추가
        login_layout.addLayout(login_title_layout)


        # 매장 등록 정보 박스 프레임 ====================================
        store_set_group = QFrame(self)
        store_set_group.setFrameShape(QFrame.StyledPanel)
        store_set_group.setStyleSheet("""
            QFrame {
                border: 1px solid #cccccc;
                border-radius: 1px;
                background-color: #ffffff;
            }
        """)
        store_set_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        store_set_layout = QVBoxLayout(store_set_group)
        store_set_layout.setContentsMargins(15, 10, 15, 10)
        store_set_layout.setSpacing(4)

        # 수평 레이아웃 (텍스트 + 버튼)
        store_set_layout_title_layout = QHBoxLayout()
        store_set_layout_title_layout.setContentsMargins(0, 0, 0, 0)
        store_set_layout_title_layout.setSpacing(0)

        # 타이틀 라벨
        self.store_set_info_label = QLabel("매장 정보")
        self.store_set_info_label.setAlignment(Qt.AlignLeft)
        self.store_set_info_label.setFrameShape(QFrame.NoFrame)
        self.store_set_info_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 15px; 
            color: #222222;
            border: none;
            padding: 5px 0;
        """)

        # 등록 버튼
        self.store_set_register_button = QPushButton("등록")
        self.store_set_register_button.setCursor(Qt.PointingHandCursor)
        self.store_set_register_button.setFixedHeight(28)
        self.store_set_register_button.setStyleSheet("""
            background-color: #4682B4;
            color: white;
            border-radius: 5px;
            font-size: 13px;
            padding: 5px 40px;
        """)
        self.store_set_register_button.clicked.connect(self.register_store_info)

        # 수평 레이아웃에 추가 (왼쪽 라벨, 오른쪽 버튼)
        store_set_layout_title_layout.addWidget(self.store_set_info_label)
        store_set_layout_title_layout.addStretch(1)  # 공간 채우기 → 버튼을 오른쪽으로 밀어줌
        store_set_layout_title_layout.addWidget(self.store_set_register_button)

        # 박스에 수평 레이아웃 추가
        store_set_layout.addLayout(store_set_layout_title_layout)

        # 시작 버튼 ====================================
        start_button = QPushButton("시작")
        start_button.setCursor(Qt.PointingHandCursor)
        start_button.setFixedHeight(28)
        start_button.setFixedWidth(100)  # 등록 버튼과 동일한 너비
        start_button.setStyleSheet("""
            background-color: #4682B4;
            color: white;
            border-radius: 5px;
            font-size: 13px;
            padding: 5px 0;
        """)
        start_button.clicked.connect(self.start_action)

        # 우측 정렬을 위한 수평 레이아웃 (버튼을 오른쪽으로 밀기)
        start_button_layout = QHBoxLayout()
        start_button_layout.setContentsMargins(0, 0, 0, 0)
        start_button_layout.addStretch()  # 왼쪽 공간 채우기
        start_button_layout.addWidget(start_button)
        start_button_layout.addStretch()                   # 오른쪽 여백

        # 마지막에 메인 레이아웃에 store_group 추가하면 됩니다.
        layout.addLayout(status_header_layout)
        layout.addWidget(store_group)
        layout.addWidget(login_set_group)
        layout.addWidget(store_set_group)
        layout.addLayout(start_button_layout)

        self.center_window()

    # 화면 중앙배치
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


    def register_login_info(self):
        dialog = LoginInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            user_id = dialog.id_input.text()
            password = dialog.pw_input.text()
            log(f"✅ 로그인 정보 등록됨: {user_id}, {password}")

    def register_store_info(self):
        dialog = StoreInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            store_id = dialog.store_input.text()
            log(f"✅ 매장 정보 등록됨: {store_id}")



    def start_action(self):
        log("매장 정보 가져오기 및 크롤링 쓰레드 시작")

        # 1. 매장 정보 화면에 표시
        self.fetch_store_info()

        # 2. QSettings로부터 로그인 정보 + 매장 ID 불러오기
        settings = QSettings("MyCompany", "PandoGL")
        user_id = settings.value("login/id", "")
        password = settings.value("login/password", "")
        store_id = settings.value("store/id", "")

        log(f"📤 전달할 로그인 정보: ID={user_id}, PW={password}")
        log(f"📤 전달할 매장 ID: {store_id}")

        # 3. 크롤링 쓰레드 생성 및 시작
        if self.on_demand_worker is None:
            self.on_demand_worker = ApiGolfzonparkSetLoadWorker(user_id, password, store_id)
            self.on_demand_worker.start()

    def fetch_store_info(self):
        settings = QSettings("MyCompany", "PandoGL")
        store_id = settings.value("store/id", "")
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2OTBkN2VhNzUwZmY5YTY2ODllOWFmMyIsInJvbGUiOiJzaW5nbGVDcmF3bGVyIiwiZXhwIjo0ODk4ODQ0MDc3fQ.aEUYvIzMhqW6O2h6hQTG8IfzJNhpvll4fOdN7udz1yc"

        url = f"https://api.dev.24golf.co.kr/stores/{store_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # 예시: 매장명과 지점명을 화면에 표시
            self.store_info_main_label.setText(f"• 매장명 : {data.get('name', '-')}")
            self.store_info_local_label.setText(f"• 지   점 : {data.get('branch', '-')}")

            log(f"✅ 매장 정보 불러오기 성공: {data}")

        except requests.RequestException as e:
            log(f"❌ 매장 정보 불러오기 실패: {str(e)}")


