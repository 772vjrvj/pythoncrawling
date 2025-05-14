import ctypes
import keyring
from datetime import datetime
from queue import Queue
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDesktopWidget, QMessageBox, \
    QTextEdit, QProgressBar
from src.ui.all_register_popup import AllRegisterPopup
from src.utils.config import server_url  # 서버 URL 및 설정 정보
from src.utils.singleton import GlobalState
from src.workers.api_domeggook_set_worker import ApiDomeggookSetLoadWorker
from src.workers.api_golfzonpark_set_worker import ApiGolfzonparkSetLoadWorker
from src.workers.api_sellingkok_set_worker import ApiSellingkokSetLoadWorker
from src.workers.check_worker import CheckWorker
from src.workers.progress_thread import ProgressThread
from src.utils.config import server_name  # 서버 URL 및 설정 정보

class MainWindow(QWidget):

    # 초기화
    def __init__(self, app_manager):
        super().__init__()
        self.log_out_button = None
        self.header_layout = None
        self.id_list_button = None
        self.site_list_button = None
        self.collect_button = None
        self.log_reset_button = None
        self.program_reset_button = None
        self.progress_thread = None
        self.on_demand_worker = None
        self.task_queue = None
        self.excel_popup = None
        self.progress_bar = None
        self.log_window = None
        self.id_list = []
        self.app_manager = app_manager
        self.site = None
        self.color = None
        self.cookies = None
        self.api_worker = None

    # 변경값 세팅
    def common_data_set(self):
        state = GlobalState()
        self.site = state.get("site")
        self.color = state.get("color")
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
            self.header_label.setText(f"{self.site}")
            self.update_style_prop('log_reset_button', 'background-color', self.color)
            self.update_style_prop("program_reset_button", 'background-color', self.color)
            self.update_style_prop("collect_button", 'background-color', self.color)
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
        self.collect_button.setStyleSheet("""
            background-color: #7d7c7c;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.collect_button.repaint()

        self.site_list_button.setEnabled(False)
        self.site_list_button.setStyleSheet("""
            background-color: #7d7c7c;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.site_list_button.repaint()

        self.log_window.setStyleSheet("background-color: #8a8a8a; border: 1px solid #ccc; padding: 5px;")
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
        QPixmap(32, 32).fill(QColor("transparent"))  # 투명 배경
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
        self.header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬

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

        # 로그리셋
        self.log_reset_button = QPushButton("로그리셋")
        self.log_reset_button.setStyleSheet(f"""
            background-color: {self.color};
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.log_reset_button.setFixedWidth(100)  # 고정된 너비
        self.log_reset_button.setFixedHeight(40)  # 고정된 높이
        self.log_reset_button.setCursor(Qt.PointingHandCursor)
        self.log_reset_button.clicked.connect(self.log_reset)


        self.log_out_button = QPushButton("로그아웃")
        self.log_out_button.setStyleSheet(f"""
            background-color: {self.color};
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.log_out_button.setFixedWidth(100)  # 고정된 너비
        self.log_out_button.setFixedHeight(40)  # 고정된 높이
        self.log_out_button.setCursor(Qt.PointingHandCursor)
        self.log_out_button.clicked.connect(self.on_log_out)

        # 왼쪽 버튼 레이아웃
        left_button_layout.addWidget(self.collect_button)
        left_button_layout.addWidget(self.log_reset_button)
        left_button_layout.addWidget(self.log_out_button)

        # 레이아웃에 요소 추가
        self.header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가

        # 헤더에 텍스트 추가
        self.header_label = QLabel(f"{self.site} 후킹")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("font-size: 18px; font-weight: bold; background-color: white; color: black; padding: 10px;")

        # 로그 창 추가
        self.log_window = QTextEdit(self)
        self.log_window.setReadOnly(True)  # 읽기 전용 설정
        self.log_window.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ccc; padding: 5px;")
        # 줄 바꿈을 비활성화하고, 수평 스크롤바를 항상 표시
        self.log_window.setLineWrapMode(QTextEdit.NoWrap)  # 줄 바꿈 비활성화
        self.log_window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 수평 스크롤바 항상 표시

        main_layout.addLayout(self.header_layout)        # 버튼 레이아웃
        main_layout.addWidget(self.header_label)
        main_layout.addWidget(self.log_window, stretch=2)  # 로그 창 추가

        # 레이아웃 설정
        self.setLayout(main_layout)
        self.center_window()
        self.add_log('프로그램 시작')

    # 로그
    def add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_window.append(log_message)  # 직접 호출

    def start_on_demand_worker(self):
        if self.collect_button.text() == "시작":
            self.collect_button.setText("중지")
            self.collect_button.setStyleSheet("""
                background-color: #FFA500;
                color: white;
                border-radius: 15%;
                font-size: 16px;
                padding: 10px;
            """)
            self.collect_button.repaint()
            self.task_queue = Queue()
            self.progress_thread = ProgressThread(self.task_queue)
            self.progress_thread.log_signal.connect(self.add_log)
            self.progress_thread.start()
            if self.on_demand_worker is None:  # worker가 없다면 새로 생성
                if self.site == '골프존파크 그린':
                    self.on_demand_worker = ApiGolfzonparkSetLoadWorker()
                self.on_demand_worker.log_signal.connect(self.add_log)
                self.on_demand_worker.msg_signal.connect(self.show_message_box)  # 메시지 박스 표시
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
            self.stop()


    # 프로그램 시작 중지
    def start_on_demand_worker_old(self):
        if self.id_list is None:
            self.show_message("유저 목록이 없습니다.", 'warn')
            return
        if self.collect_button.text() == "시작":
            self.collect_button.setText("중지")
            self.collect_button.setStyleSheet("""
                background-color: #FFA500;
                color: white;
                border-radius: 15%;
                font-size: 16px;
                padding: 10px;
            """)
            self.collect_button.repaint()
            self.task_queue = Queue()
            self.progress_thread = ProgressThread(self.task_queue)
            self.progress_thread.progress_signal.connect(self.update_progress)
            self.progress_thread.log_signal.connect(self.add_log)
            self.progress_thread.finally_finished_signal.connect(self.finally_finished)
            self.progress_thread.start()
            if self.on_demand_worker is None:  # worker가 없다면 새로 생성
                if self.site == '도매꾹':
                    self.on_demand_worker = ApiDomeggookSetLoadWorker(self.id_list)
                elif self.site == '셀링콕':
                    self.on_demand_worker = ApiSellingkokSetLoadWorker(self.id_list)
                self.on_demand_worker.log_signal.connect(self.add_log)
                self.on_demand_worker.progress_signal.connect(self.set_progress)
                self.on_demand_worker.progress_end_signal.connect(self.progress_end)
                self.on_demand_worker.finally_finished_signal.connect(self.finally_finished)
                self.on_demand_worker.msg_signal.connect(self.show_message_box)  # 메시지 박스 표시
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
            self.stop()

    # 크롤링 완료
    def progress_end(self):
        self.stop()
        self.show_message("크롤링이 완료되었습니다.", "info")

    def finally_finished(self, msg):
        self.add_log(msg)

    # 프로그램 중지
    def stop(self):
        # 크롤링 중지
        if self.on_demand_worker is not None:
            self.on_demand_worker.stop()
            self.on_demand_worker = None

        # 프로그래스 중지
        if self.progress_thread is not None:
            self.progress_thread.stop()
            self.progress_thread = None
            self.task_queue = None

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

        # 깜빡이게 설정
        ctypes.windll.user32.FlashWindow(int(self.winId()), True)

        msg.exec_()  # 메시지 박스 표시


    def show_message_box(self, title, message):
        """메시지 박스를 띄우고 응답을 LoginWorker에 전달"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        response = msg_box.exec_()

        if response == QMessageBox.Ok:
            self.on_demand_worker.msg_response_signal.emit(True)  # 로그인 재시도 요청
        else:
            self.on_demand_worker.msg_response_signal.emit(False)  # 로그인 중단 요청

    # 로그 초기화
    def log_reset(self):
        self.log_window.clear()

    # 선택목록으로 이동
    def go_site_list(self):
        self.close()  # 메인 화면 종료
        self.app_manager.go_to_select()


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