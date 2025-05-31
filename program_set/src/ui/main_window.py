import keyring

from datetime import datetime
from queue import Queue
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDesktopWidget, QMessageBox,
                             QTextEdit, QProgressBar)
from src.ui.style.style import create_common_button, main_style, LOG_STYLE, HEADER_TEXT_STYLE
from src.utils.config import server_url  # 서버 URL 및 설정 정보
from src.core.global_state import GlobalState
from src.workers.factory.worker_factory import WORKER_CLASS_MAP
from src.workers.main.api_albamon_set_worker import ApiAlbamonSetLoadWorker
from src.workers.check_worker import CheckWorker
from src.workers.progress_worker import ProgressWorker
from src.utils.config import server_name  # 서버 URL 및 설정 정보


class MainWindow(QWidget):

    # 초기화
    def __init__(self, app_manager):
        super().__init__()
        self.log_out_button = None
        self.header_label = None
        self.log_reset_button = None
        self.site_list_button = None
        self.program_reset_button = None
        self.collect_button = None
        self.check_list_button = None
        self.select_check_list = None
        self.task_queue = None
        self.progress_worker = None
        self.progress_bar = None
        self.log_window = None
        self.daily_worker = None  # 24시 실행 스레드
        self.on_demand_worker = None  # 요청 시 실행 스레드
        self.app_manager = app_manager
        self.site = None
        self.color = None
        self.check_list = None
        self.cookies = None
        self.api_worker = None

    # 변경값 세팅
    def common_data_set(self):
        state = GlobalState()
        self.name = state.get("name")
        self.site = state.get("site")
        self.color = state.get("color")
        self.check_list = state.get("check_list")
        self.cookies = state.get("cookies")

    # 재 초기화
    def init_reset(self):
        self.common_data_set()
        self.api_worker_set()
        self.ui_set()

    # 로그인 확인 체크
    def api_worker_set(self):
        if self.api_worker is None:  # 스레드가 있으면 중단
            self.api_worker = CheckWorker(self.cookies, server_url)
            self.api_worker.api_failure.connect(self.handle_api_failure)
            self.api_worker.log_signal.connect(self.add_log)
            self.api_worker.start()

    # 화면 업데이트
    def ui_set(self):
        if self.layout():
            self.header_label.setText(f"{self.name}")
            self.log_reset_button.setStyleSheet(main_style(self.color))
            self.program_reset_button.setStyleSheet(main_style(self.color))
            self.collect_button.setStyleSheet(main_style(self.color))
        else:
            self.set_layout()

    # ui 속성 변경
    def update_style_prop(self, item_name, prop, value):
        widget = getattr(self, item_name, None)  # item_name에 해당하는 속성 가져오기
        if widget is None:
            raise AttributeError(f"No widget found with name '{item_name}'")

        current_stylesheet = widget.styleSheet()
        new_stylesheet = f"{current_stylesheet}{prop}: {value};"
        widget.setStyleSheet(new_stylesheet)

    # 프로그램 일시 중지 (동일한 아이디로 로그인시)
    def handle_api_failure(self, error_message):
        self.collect_button.setEnabled(False)  # 버튼 비활성화
        self.collect_button.setStyleSheet(main_style(self.color))
        self.collect_button.repaint()

        self.check_list_button.setEnabled(False)
        self.check_list_button.setStyleSheet(main_style(self.color))
        self.check_list_button.repaint()

        self.log_window.setStyleSheet(LOG_STYLE)
        self.log_window.repaint()

        # 모든 스레드 종료 요청
        self.api_worker.stop()
        self.api_worker.wait()
        self.api_worker = None
        self.stop()
        self.add_log("동시사용자 접속으로 프로그램을 종료하겠습니다...")

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
        self.setWindowIcon(QIcon(icon_pixmap))

        # 메인화면 설졍
        self.setGeometry(100, 100, 1000, 700)  # 메인 화면 크기 설정
        self.setStyleSheet("background-color: white;")  # 배경색 흰색

        # 메인 레이아웃
        main_layout = QVBoxLayout()

        # 상단 버튼들 레이아웃
        header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬

        self.site_list_button     = create_common_button("목록", self.go_site_list, self.color, 100)
        self.log_reset_button     = create_common_button("로그리셋", self.log_reset, self.color, 100)
        self.program_reset_button = create_common_button("초기화", self.log_reset, self.color, 100)
        self.collect_button       = create_common_button("시작", self.start_on_demand_worker, self.color, 100)
        self.log_out_button       = create_common_button("로그아웃", self.on_log_out, self.color, 100)

        # 왼쪽 버튼 레이아웃
        left_button_layout.addWidget(self.site_list_button)
        left_button_layout.addWidget(self.log_reset_button)
        left_button_layout.addWidget(self.program_reset_button)
        left_button_layout.addWidget(self.collect_button)
        left_button_layout.addWidget(self.log_out_button)

        # 레이아웃에 요소 추가
        header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가

        # 헤더에 텍스트 추가
        self.header_label = QLabel(f"{self.name} 데이터 추출")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet(HEADER_TEXT_STYLE)

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
        self.log_window.setStyleSheet(LOG_STYLE)
        self.log_window.setLineWrapMode(QTextEdit.NoWrap)  # 줄 바꿈 비활성화
        self.log_window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 수평 스크롤바 항상 표시

        main_layout.addLayout(header_layout) # 버튼 레이아웃
        main_layout.addWidget(self.header_label)
        main_layout.addWidget(self.progress_bar)  # 진행 상태 게이지바 추가
        main_layout.addWidget(self.log_window, stretch=2)  # 로그 창 추가

        # 레이아웃 설정
        self.setLayout(main_layout)
        self.center_window()

    # 로그
    def add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_window.append(log_message)  # 직접 호출

    # 프로그램 시작 중지
    def start_on_demand_worker(self):
        if self.collect_button.text() == "시작":
            self.collect_button.setText("중지")
            self.collect_button.setStyleSheet(main_style(self.color))
            self.collect_button.repaint()  # 버튼 스타일이 즉시 반영되도록 강제로 다시 그리기

            self.task_queue = Queue()
            self.progress_worker = ProgressWorker(self.task_queue)
            self.progress_worker.progress_signal.connect(self.update_progress)
            self.progress_worker.log_signal.connect(self.add_log)
            self.progress_worker.start()

            if self.on_demand_worker is None:  # worker가 없다면 새로 생성
                worker_class = WORKER_CLASS_MAP.get(self.site)
                if worker_class:
                    self.on_demand_worker = worker_class(self.select_check_list)
                    self.on_demand_worker.log_signal.connect(self.add_log)
                    self.on_demand_worker.progress_signal.connect(self.set_progress)
                    self.on_demand_worker.progress_end_signal.connect(self.stop)
                    self.on_demand_worker.start()
                else:
                    self.add_log(f"[오류] '{self.site}'에 해당하는 워커가 없습니다.")
        else:
            self.collect_button.setText("시작")
            self.collect_button.setStyleSheet(main_style(self.color))
            self.collect_button.repaint()  # 버튼 스타일이 즉시 반영되도록 강제로 다시 그리기
            self.add_log('중지')
            self.stop()

    # 프로그램 중지
    def stop(self):
        # 프로그래스 중지
        if self.on_demand_worker is not None:
            self.on_demand_worker.stop()
            self.on_demand_worker = None

        # 크롤링 중지
        if self.progress_worker is not None:
            self.progress_bar.setValue(0)  # 초기값 0
            self.progress_worker.stop()
            self.progress_worker = None
            self.task_queue = None
        self.show_message("크롤링 종료", 'info', None)

    # 프로그래스 큐 데이터 담기
    def set_progress(self, start_value, end_value):
        if self.task_queue:
            self.task_queue.put((start_value, end_value))

    # 프로그래스 UI 업데이트
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # 화면 중앙
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 경고 alert창
    def show_message(self, message, type, event):
        """메시지 박스를 띄우고 OK 버튼이 눌리면 event.set() 호출"""
        try:
            msg = QMessageBox(self)
            if type == 'warn':
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("경고")
            elif type == 'info':
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("확인")

            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()  # 사용자가 OK를 누를 때까지 대기

            # OK 버튼을 누르면 event 해제
            if event:
                event.set()
        except Exception as e:
            self.add_log(f"⚠️ 메시지 박스 오류 발생: {e}")
            if event:
                event.set()  # 예외 발생 시에도 이벤트 해제 (무한 대기 방지)

    # url 세팅
    def set_url_list(self, url_list):
        global main_url_list
        main_url_list = url_list
        self.add_log(f'URL 세팅완료: {main_url_list}')

    # 항목 업데이트
    def check_list_update(self, select_check_list):
        self.select_check_list = select_check_list
        self.add_log(f'크롤링 목록 : {select_check_list}')

    # 로그 리셋
    def log_reset(self):
        self.log_window.clear()

    # 프로그램 리셋
    def program_reset(self):
        self.log_reset()
        self.update_progress(0)
        self.stop()

    # 사이트 이동
    def go_site_list(self):
        self.close()  # 로그인 화면 종료
        self.app_manager.go_to_select()

    # 로그아웃
    def on_log_out(self):
        try:
            keyring.delete_password(server_name, "username")
            keyring.delete_password(server_name, "password")
            self.add_log("🔐 저장된 로그인 정보 삭제 완료")
        except keyring.errors.PasswordDeleteError as e:
            self.add_log(f"⚠️ 로그인 정보 삭제 실패 (저장 안 되어 있음): {str(e)}")
        except Exception as e:
            self.add_log(f"❌ 로그인 정보 삭제 중 예외 발생: {str(e)}")

        self.add_log("🚪 로그아웃 처리 및 로그인 화면으로 이동")
        self.close()  # 메인 창 종료
        self.app_manager.go_to_login()