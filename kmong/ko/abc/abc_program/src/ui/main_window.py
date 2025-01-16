from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDesktopWidget, QMessageBox,
                             QTextEdit, QApplication, QProgressBar)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from queue import Queue
from threading import Lock

from src.utils.config import server_url  # 서버 URL 및 설정 정보
from src.workers.api_abcmart_set_worker import ApiAbcmartSetLoadWorker
from src.workers.api_zalando_set_worker import ApiZalandoSetLoadWorker
from src.ui.all_register_popup import AllRegisterPopup

from src.workers.check_worker import CheckWorker
from src.workers.progress_thread import ProgressThread

main_url_list = []


class MainWindow(QWidget):
    
    # 초기화
    def __init__(self, cookies=None, site=None, color=None):
        super().__init__()
        self.site = site
        self.color = color
        self.set_layout()
        self.progress_thread = None
        self.on_demand_worker = None  # 요청 시 실행 스레드
        self.cookies = cookies
        self.check_list = []
        self.select_check_list = None
        self.task_queue = Queue()
        self.queue_lock = Lock()  # 대기열 접근 보호용 Lock 생성
        self.excel_popup = None

        # 세션 관리용 API Worker 초기화
        self.api_worker = CheckWorker(cookies, server_url)
        self.api_worker.api_failure.connect(self.handle_api_failure)
        self.api_worker.log_signal.connect(self.add_log)

        self.api_worker.start()  # 스레드 시작

        self.all_register_button = None


    # 프로그램 일시 중지 (동일한 아이디로 로그인시)
    def handle_api_failure(self, error_message):
        """API 요청 실패 처리"""
        self.collect_button.setEnabled(False)  # 버튼 비활성화
        self.collect_button.setStyleSheet("""
            background-color: #7d7c7c;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.collect_button.repaint()

        self.all_register_button.setEnabled(False)
        self.all_register_button.setStyleSheet("""
            background-color: #7d7c7c;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.all_register_button.repaint()

        self.log_window.setStyleSheet("background-color: #8a8a8a; border: 1px solid #ccc; padding: 5px;")
        self.log_window.repaint()

        # 모든 스레드 종료 요청
        self.stop_thread_async(self.api_worker)
        self.stop_thread_async(self.progress_thread)
        self.stop_thread_async(self.on_demand_worker)

        self.add_log("동시사용자 접속으로 프로그램을 종료하겠습니다...")


        # QTimer를 사용해 주기적으로 스레드 상태 확인
        def check_threads():
            if all(not t or not t.isRunning() for t in [self.api_worker, self.progress_thread, self.on_demand_worker]):
                # 모든 스레드가 종료되었으면 메시지 박스와 프로그램 종료
                QMessageBox.critical(self, "프로그램 종료", f"동일 접속자가 존재해서 프로그램을 종료합니다.\n오류: {error_message}")
                QApplication.quit()
            else:
                QTimer.singleShot(1000, check_threads)  # 100ms 후 다시 확인

        QTimer.singleShot(0, check_threads)  # 즉시 시작


    # 쓰레드 중지
    def stop_thread_async(self, thread):
        """스레드 비동기 안전 종료"""
        if thread is not None and thread.isRunning():
            thread.stop()
            self.add_log(f"{thread.__class__.__name__} 종료 요청됨")


    # 레이아웃 설정
    def set_layout(self):
        self.setWindowTitle("메인 화면")

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

        self.setGeometry(100, 100, 1000, 700)  # 메인 화면 크기 설정
        self.setStyleSheet("background-color: white;")  # 배경색 흰색

        # 메인 레이아웃
        main_layout = QVBoxLayout()

        # 상단 버튼들 레이아웃
        header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬


        # 전체등록
        self.all_register_button = QPushButton("브랜드 URL 등록")
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
        self.log_clear_button = QPushButton("초기화")
        self.log_clear_button.setStyleSheet(f"""
            background-color: {self.color};
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.log_clear_button.setFixedWidth(100)  # 고정된 너비
        self.log_clear_button.setFixedHeight(40)  # 고정된 높이
        self.log_clear_button.setCursor(Qt.PointingHandCursor)
        self.log_clear_button.clicked.connect(self.log_clear)


        # 선택수집
        self.collect_button = QPushButton("시작")
        self.collect_button.setStyleSheet(f"""
            background-color: {self.color};
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
        left_button_layout.addWidget(self.log_clear_button)
        left_button_layout.addWidget(self.collect_button)

        # 레이아웃에 요소 추가
        header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가

        # 헤더에 텍스트 추가
        header_label = QLabel(f"{self.site} 데이터 추출")
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


    # 프로그래스바 세팅
    def set_progress(self, end_value):
        with self.queue_lock:  # 대기열 접근 보호
            self.task_queue.put(end_value)

        # 실행 중인 쓰레드가 없으면 작업 시작
        if self.progress_thread is None or not self.progress_thread.isRunning():
            self.start_next_task()


    # 게이지 세팅
    def start_next_task(self):
        # 스레드 동기화를 위한 잠금(lock) 메커니즘.
        # self.queue_lock은 다중 스레드 환경에서 작업 큐(task_queue)에 동시 접근하지 못하도록 보호합니다.
        # with 블록 안에서만 잠금이 유지되며, 블록이 끝나면 자동으로 잠금이 해제됩니다.
        with self.queue_lock:  # 대기열 보호
            if not self.task_queue.empty():
                next_end_value = self.task_queue.get()
                self.progress_thread = ProgressThread(self.progress_bar.value(), next_end_value)
                self.progress_thread.log_signal.connect(self.add_log)
                self.progress_thread.progress_signal.connect(self.update_progress)
                self.progress_thread.finished.connect(self.on_progress_thread_finished)
                self.progress_thread.start()


    # 프로그래스바 업데이트
    def update_progress(self, value):
        self.progress_bar.setValue(value)


    # 로그
    def add_log(self, message):
        """
        로그 메시지를 추가합니다.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        self.log_window.append(log_message)  # 직접 호출

    
    
    def start_on_demand_worker(self):

        if self.check_list is None:
            self.show_message("크롤링 목록을 선택하세요.", 'warn')
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

                if self.site == 'ABC-MART':
                    self.on_demand_worker = ApiAbcmartSetLoadWorker(self.select_check_list)
                # elif self.site == 'GRAND STAGE':
                #     self.on_demand_worker = ApiZalandoSetLoadWorker(self.select_check_list)
                # elif self.site == 'On the spot':
                #     self.on_demand_worker = ApiZalandoSetLoadWorker(self.select_check_list)

                self.on_demand_worker.log_signal.connect(self.add_log)
                self.on_demand_worker.progress_signal.connect(self.set_progress)
                self.on_demand_worker.progress_end_signal.connect(self.on_progress_thread_last_finished)
                self.on_demand_worker.start()

            elif not self.on_demand_worker.isRunning():  # 이미 종료된 worker라면 다시 시작

                self.on_demand_worker.start()

        else:
            self.collect_button.setText("시작")
            self.collect_button.setStyleSheet(f"""
                background-color: {self.color};
                color: white;
                border-radius: 15%;
                font-size: 16px;
                padding: 10px;
            """)
            self.collect_button.repaint()  # 버튼 스타일이 즉시 반영되도록 강제로 다시 그리기
            self.add_log('중지')
            # 중지 시 on_demand_worker만 종료
            if self.on_demand_worker is not None and self.on_demand_worker.isRunning():
                self.on_demand_worker.stop()  # 사용자 정의 루프(while self.running) 기반 작업에 적합.
                self.on_demand_worker.wait()  # 완료될 때까지 대기
                self.on_demand_worker = None  # worker 객체 초기화
                self.on_progress_stop()


    # 화면 중앙
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


    # 경고 alert창
    def show_message(self, message, type):
        # QMessageBox 생성
        msg = QMessageBox(self)
        if type == 'warn':
            msg.setIcon(QMessageBox.Warning)  # 경고 아이콘 설정
            msg.setWindowTitle("경고")  # 창 제목 설정
        elif type == 'info':
            msg.setIcon(QMessageBox.Information)  # 경고 아이콘 설정
            msg.setWindowTitle("확인")  # 창 제목 설정
        msg.setText(message)  # 메시지 내용 설정
        msg.setStandardButtons(QMessageBox.Ok)  # 버튼 설정 (OK 버튼만 포함)
        msg.exec_()  # 메시지 박스 표시


    # 전체 등록 팝업
    def open_all_register_popup(self):
        # 등록 팝업창 열기
        self.excel_popup = AllRegisterPopup(parent=self)  # 부모 객체 전달
        self.excel_popup.updateList.connect(self.update_list)
        self.excel_popup.exec_()


    # url list 업데이트
    def update_list(self, url_list):
        self.url_list = url_list
        self.add_log(f'브랜드 목록 갯수 : {len(self.url_list)}')
        for url in url_list:
            self.add_log(url)


    # 항목 업데이트
    def check_list_update(self, select_check_list):
        self.select_check_list = select_check_list
        self.add_log(f'크롤링 목록 : {select_check_list}')


    # 프로그래쓰 쓰레드 종료 후 queue 실행
    def on_progress_thread_finished(self):
        self.progress_thread = None


    # 프로그래쓰 쓰레드 완전 종료
    def on_progress_thread_last_finished(self):
        self.progress_thread = None
        self.add_log("모든 작업이 종료되었습니다.")
        self.progress_bar.setValue(100)  # 게이지 초기화 (또는 완료 상태 유지)



    def on_progress_stop(self):
        """
        중지 버튼을 눌렀을 때 호출되는 메서드
        현재 진행 중인 작업을 중단하고, 대기 중인 작업을 모두 제거.
        """
        # 현재 실행 중인 작업 중단
        if self.progress_thread and self.progress_thread.isRunning():
            self.progress_thread.stop()  # 스레드 중단 요청
            self.progress_thread.wait()  # 스레드 종료 대기
            self.progress_thread = None  # 스레드 객체 초기화
            self.add_log("현재 작업이 강제로 중단되었습니다.")

        # 작업 큐 비우기
        with self.queue_lock:
            while not self.task_queue.empty():
                self.task_queue.get()  # 큐에서 작업 제거
            self.add_log("작업 큐가 초기화되었습니다.")

    # 로그 초기화
    def log_clear(self):
        self.url_list = []
        self.log_window.clear()