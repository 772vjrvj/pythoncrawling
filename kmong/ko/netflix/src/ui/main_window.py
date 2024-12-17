from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDesktopWidget, QMessageBox,
                             QTextEdit, QApplication, QProgressBar)

from src.ui.all_register_popup import AllRegisterPopup
from src.utils.config import server_url  # 서버 URL 및 설정 정보
from src.workers.api_netflix_set_worker import ApiNetflixSetLoadWorker
from src.workers.check_worker import CheckWorker
from src.workers.progress_thread import ProgressThread

main_url_list = []


class MainWindow(QWidget):
    
    # 초기화
    def __init__(self, cookies=None):
        super().__init__()
        self.set_layout()
        self.daily_worker = None  # 24시 실행 스레드
        self.progress_thread = None
        self.on_demand_worker = None  # 요청 시 실행 스레드
        self.cookies = cookies

        # 세션 관리용 API Worker 초기화
        self.api_worker = CheckWorker(cookies, server_url)
        self.api_worker.api_failure.connect(self.handle_api_failure)
        self.api_worker.start()  # 스레드 시작


    def handle_api_failure(self, error_message):
        """API 요청 실패 처리"""
        QMessageBox.critical(self, "프로그램 종료", f"동일 접속자가 존재해서 프로그램을 종료합니다.\n오류: {error_message}")
        # self.api_worker.stop()  # 스레드 중지
        QApplication.instance().quit()  # 프로그램 종료


    # 레이아웃 설정
    def set_layout(self):
        self.setWindowTitle("메인 화면")
        self.setGeometry(100, 100, 1000, 700)  # 메인 화면 크기 설정
        self.setStyleSheet("background-color: white;")  # 배경색 흰색

        # 메인 레이아웃
        main_layout = QVBoxLayout()

        # 상단 버튼들 레이아웃
        header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬

        # 버튼 설정
        # 전체등록
        self.all_register_button = QPushButton("넷플릭스URL 등록")
        self.all_register_button.setStyleSheet("""
                    background-color: black;
                    color: white;
                    border-radius: 15%;
                    font-size: 16px;
                    padding: 10px;
                """)
        self.all_register_button.setFixedWidth(180)  # 고정된 너비
        self.all_register_button.setFixedHeight(40)  # 고정된 높이
        self.all_register_button.setCursor(Qt.PointingHandCursor)
        self.all_register_button.clicked.connect(self.open_all_register_popup)

        # 선택수집
        self.collect_button = QPushButton("시작")
        self.collect_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.collect_button.setFixedWidth(100)  # 고정된 너비
        self.collect_button.setFixedHeight(40)  # 고정된 높이
        self.collect_button.setCursor(Qt.PointingHandCursor)
        self.collect_button.clicked.connect(self.start_on_demand_worker)

        # 왼쪽 버튼 레이아웃
        left_button_layout.addWidget(self.all_register_button)
        left_button_layout.addWidget(self.collect_button)

        # 레이아웃에 요소 추가
        header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가

        # 헤더에 텍스트 추가
        header_label = QLabel("넷플릭스 데이터 추출")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; background-color: white; color: black; padding: 10px;")

        # 진행 상태 게이지바 추가
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1000000)  # 최소 0, 최대 100
        self.progress_bar.setValue(0)  # 초기값 0
        self.progress_bar.setTextVisible(True)  # 텍스트 표시 여부
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                width: 100%;  # 게이지가 공백 없이 채워짐
                margin: 0.5px;
            }
        """)

        # 로그 창 추가
        self.log_window = QTextEdit(self)
        self.log_window.setReadOnly(True)  # 읽기 전용 설정
        self.log_window.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ccc; padding: 5px;")
        # 줄 바꿈을 비활성화하고, 수평 스크롤바를 항상 표시
        self.log_window.setLineWrapMode(QTextEdit.NoWrap)  # 줄 바꿈 비활성화
        self.log_window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 수평 스크롤바 항상 표시

        main_layout.addLayout(header_layout)        # 버튼 레이아웃

        main_layout.addWidget(header_label)
        main_layout.addWidget(self.progress_bar)  # 진행 상태 게이지바 추가
        main_layout.addWidget(self.log_window, stretch=2)  # 로그 창 추가

        # 레이아웃 설정
        self.setLayout(main_layout)

        self.center_window()


    # 게이티 세팅
    def set_progress(self, end_value):

        if self.progress_thread is None or not self.progress_thread.isRunning():

            start_value = self.progress_bar.value()  # 현재 진행 상태 값을 시작값으로 설정

            # ProgressThread를 사용하여 별도의 스레드에서 실행
            self.progress_thread = ProgressThread(start_value, end_value)

            # 진행 상태가 변경될 때마다 progress_signal을 받으면 progress_bar를 업데이트
            self.progress_thread.progress_signal.connect(self.update_progress)

            # 별도의 스레드에서 실행 시작
            self.progress_thread.start()


    def update_progress(self, value):
        self.progress_bar.setValue(value)


    # 로그
    def add_log(self, message):
        """
        로그 메시지를 추가합니다.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_window.append(f"[{timestamp}] {message}")


    def start_on_demand_worker(self):
        global main_url_list

        if main_url_list is None or len(main_url_list) <= 0:
            self.show_warning("등록된 URL이 없습니다.")
            return

        # 버튼의 텍스트와 스타일 변경
        if self.collect_button.text() == "시작":

            self.collect_button.setText("중지")
            self.collect_button.setStyleSheet("""
                background-color: #FFA500;
                color: white;
                border-radius: 15%;
                font-size: 16px;
                padding: 10px;
            """)
            self.collect_button.repaint()  # 버튼 스타일이 즉시 반영되도록 강제로 다시 그리기
            if self.on_demand_worker is None:  # worker가 없다면 새로 생성
                self.on_demand_worker = ApiNetflixSetLoadWorker(main_url_list, self)
                self.on_demand_worker.start()
            elif not self.on_demand_worker.isRunning():  # 이미 종료된 worker라면 다시 시작
                self.on_demand_worker.start()

        else:
            self.collect_button.setText("시작")
            self.collect_button.setStyleSheet("""
                background-color: #8A2BE2;
                color: white;
                border-radius: 15%;
                font-size: 16px;
                padding: 10px;
            """)
            self.collect_button.repaint()  # 버튼 스타일이 즉시 반영되도록 강제로 다시 그리기
            self.add_log('중지')
            # 중지 시 on_demand_worker만 종료
            if self.on_demand_worker is not None and self.on_demand_worker.isRunning():
                self.on_demand_worker.terminate()  # 중지
                self.on_demand_worker.wait()  # 완료될 때까지 대기
                self.on_demand_worker = None  # worker 객체 초기화


    # 화면 중앙
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


    # 전체 등록 팝업
    def open_all_register_popup(self):
        # 등록 팝업창 열기
        popup = AllRegisterPopup(parent=self)  # 부모 객체 전달
        popup.exec_()


    # url 세팅
    def set_url_list(self, url_list):
        global main_url_list
        main_url_list = url_list
        self.add_log(f'URL 세팅완료: {main_url_list}')


    # 경고 alert창
    def show_warning(self, message):
        # QMessageBox 생성
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)  # 경고 아이콘 설정
        msg.setWindowTitle("경고")  # 창 제목 설정
        msg.setText(message)  # 메시지 내용 설정
        msg.setStandardButtons(QMessageBox.Ok)  # 버튼 설정 (OK 버튼만 포함)
        msg.exec_()  # 메시지 박스 표시


