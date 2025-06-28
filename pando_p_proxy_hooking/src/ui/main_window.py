#src/ui/main_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QFrame, QSpacerItem, QDialog
)
from PyQt5.QtCore import Qt
from src.ui.store_dialog import StoreDialog
from src.utils.file_storage import load_data, save_data
import os
import subprocess
from src.utils.token_manager import start_token_refresh
import time
from src.utils.token_manager import start_token_refresh, get_token
from src.utils.api import fetch_store_info
import socket
import pathlib

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_store_id = None # 매장 ID
        self.start_button     = None # 시작 버튼
        self.store_button     = None # 저장 버튼
        self.branch_value     = None # 지점 이름 : GPM스크랩
        self.store_name_value = None # 매장 이름 : 용인 골프존파크 죽전골프앤D
        self.ui_set()                # UI 초기화
        self.load_store_id()         # data.json에서 상점 ID가져오기
    
    # UI 세팅
    def ui_set(self):

        # QHBoxLayout 수평
        # QVBoxLayout 수직
        self.setWindowTitle("PandoP")  # 윈도우 제목 설정
        # self.setFixedSize(600, 300)  # 최소 크기 지정 그리고 고정
        self.setMinimumSize(600, 200)

        # 전체 위젯 및 내부 위젯들 스타일 설정 (폰트, 색상 등)
        self.setStyleSheet("""
            QWidget {
                background-color: #fff;
                font-family: Arial;
                font-size: 13px;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 6px 16px;
                border-radius: 4px;
                background-color: #4682B4;
                color: white;
                font-size: 13px;
            }
            QFrame#infoBox {
                border: 1px solid #ccc;
                padding: 20px;
                margin: 10px 20px;
                border-radius: 4px;
                background-color: #fafafa;
            }
        """)

        layout = QVBoxLayout()  # 전체 수직 레이아웃 생성
        layout.setSpacing(10)  # 위젯 사이 수직 간격 설정

        title = QLabel("PandoP")  # 타이틀 라벨 생성
        title.setStyleSheet("font-size: 20px; margin: 10px 20px 0 20px;")  # 타이틀 스타일 시계방향
        layout.addWidget(title, alignment=Qt.AlignLeft)  # 왼쪽 정렬로 레이아웃에 추가

        info_box = QFrame()  # 매장 정보 묶는 박스 생성
        info_box.setObjectName("infoBox")  # 스타일링을 위한 객체명 지정
        info_layout = QVBoxLayout()  # 매장 정보용 수직 레이아웃 생성
        info_layout.setSpacing(12)   # 수직간격

        label_section = QLabel("매장 정보")  # 섹션 타이틀
        label_section.setStyleSheet("font-weight: bold; background-color: #fafafa;")
        info_layout.addWidget(label_section)  # 섹션 제목 추가

        row1 = QHBoxLayout()  # 첫 번째 행 (매장명)
        label1 = QLabel("● 매장명 :")
        label1.setFixedWidth(70)  # 동일한 너비로 고정
        label1.setStyleSheet("background-color: #fafafa;")
        self.store_name_value = QLabel("-")  # 매장명 값이 들어갈 라벨
        row1.addWidget(label1)
        row1.addSpacing(10)
        row1.addWidget(self.store_name_value)
        row1.addStretch()  # 오른쪽 정렬용

        row2 = QHBoxLayout()  # 두 번째 행 (지점명)
        label2 = QLabel("● 지   점 :")
        label2.setFixedWidth(70)  # 동일한 너비로 고정
        label2.setStyleSheet("background-color: #fafafa;")
        self.branch_value = QLabel("-")  # 지점명 값 라벨
        row2.addWidget(label2)
        row2.addSpacing(10)
        row2.addWidget(self.branch_value)
        row2.addStretch()

        info_layout.addLayout(row1)  # info_layout에 첫 번째 행 추가
        info_layout.addLayout(row2)  # info_layout에 두 번째 행 추가
        info_box.setLayout(info_layout)  # QFrame에 info_layout 지정
        layout.addWidget(info_box)  # 전체 레이아웃에 info_box 추가

        button_box = QHBoxLayout()  # 버튼들 수평 정렬
        self.store_button = QPushButton("등록")
        self.start_button = QPushButton("시작")

        self.store_button.setFixedWidth(130)
        self.start_button.setFixedWidth(130)

        button_box.addStretch()  # 좌측 여백 확보
        button_box.addWidget(self.store_button)
        button_box.addSpacing(20)
        button_box.addWidget(self.start_button)
        button_box.addStretch()  # 우측 여백 확보

        layout.addLayout(button_box)  # 버튼 박스를 전체 레이아웃에 추가
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))  # 하단 공간 확보
        # 10, 10	폭 10px, 높이 10px짜리 기본 크기의 스페이서 아이템입니다. 그러나 실제 사용 시 크기보다 **정책(SizePolicy)**에 따라 동작합니다.
        # QSizePolicy.Minimum	가로 방향은 최소한의 크기를 유지합니다. 즉, 가로 공간을 확장하지 않습니다.
        # QSizePolicy.Expanding	세로 방향은 가능한 한 빈 공간을 최대한 차지하여 확장합니다. 이게 핵심입니다.

        self.setLayout(layout)  # 현재 위젯에 레이아웃 지정
        self.setWindowFlag(Qt.Window)  # 창으로 표시
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)  # 최소/최대 버튼 허용
        self.store_button.clicked.connect(self.open_store_dialog)  # 등록 버튼 클릭 시 동작 연결
        self.start_button.clicked.connect(self.start_action)  # 시작 버튼 클릭 시 동작 연결

    # data.json에서 store_id를 가져온다.
    def load_store_id(self):
        data = load_data()
        self.current_store_id = data.get("store_id") or self.current_store_id
        self.store_name_value.setText(data.get("name") or "-")
        self.branch_value.setText(data.get("branch") or "-")

    # 매장 팝업에서 가져온 ID를 저장
    def save_store_id(self, store_id):
        self.current_store_id = store_id
        data = load_data()
        data['store_id'] = store_id
        save_data(data)

    # 매장 ID 등록 팝업 열기
    def open_store_dialog(self):
        dialog = StoreDialog(current_store_id=self.current_store_id)
        if dialog.exec_() == QDialog.Accepted: # 다이얼로그가 닫힐 때까지 블로킹(blocking) 대기
            store_id = dialog.get_data()
            if store_id is not None:
                self.save_store_id(store_id)


    def wait_for_proxy(self, port=8080, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                if result == 0:
                    print(f"프록시 서버가 포트 {port}에서 실행 중입니다.")
                    return True
            time.sleep(0.5)
        print(f"프록시 서버가 포트 {port}에서 실행되지 않았습니다.")
        return False

    def start_action(self):
        if not self.current_store_id:
            return

        # 프록시 실행
        self.run_proxy()

        if not self.wait_for_proxy():
            print("프록시 서버가 포트 8080에서 실행되지 않았습니다.")
            return

        # 저장
        data = load_data()
        data['store_id'] = self.current_store_id
        save_data(data)

        # 토큰 발급 및 저장
        start_token_refresh(self.current_store_id)

        # 토큰 기다렸다가 받아오기
        token = None
        for _ in range(10):  # 최대 5초 대기
            token = get_token()
            if token:
                break
            time.sleep(0.5)

        if not token:
            print("토큰이 없습니다.")
            return

        # 매장 정보 요청
        info = fetch_store_info(token, self.current_store_id)
        if info:
            self.store_name_value.setText(info.get("name", "-"))
            self.branch_value.setText(info.get("branch", "-"))
            print("매장 정보 UI 업데이트 완료")

            # 옵션: data.json에도 저장
            data.update({
                "name": info.get("name", ""),
                "branch": info.get("branch", "")
            })
            save_data(data)

        else:
            print("매장 정보 요청 실패")


    def run_proxy(self):
        print("[프록시] 프록시 실행 준비 중...")

        # 루트 경로 (pando_p_proxy_hooking)
        project_root = str(pathlib.Path(__file__).resolve().parents[2])

        mitmdump_path = os.path.join(project_root, "mitmdump.exe")
        script_path   = os.path.join(project_root, "src", "server", "proxy_server.py")
        logs_dir      = os.path.join(project_root, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path      = os.path.join(logs_dir, "mitm_bat.log")

        # 경로 확인 로그
        print(f"[디버그] mitmdump 경로: {mitmdump_path}") #
        print(f"[디버그] proxy_server.py 경로: {script_path}")

        if not os.path.exists(mitmdump_path):
            print(f"mitmdump.exe 파일이 없습니다: {mitmdump_path}")
            return

        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                subprocess.Popen(
                    [mitmdump_path, "-s", script_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print(f"[프록시] mitmdump 실행 완료 (로그: {log_path})")
        except Exception as e:
            print(f"[프록시] 실행 실패: {e}")