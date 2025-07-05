# src/ui/main_window
import os
import subprocess
import time
import socket
import ctypes
import winreg
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QFrame, QSpacerItem, QDialog
)
from PyQt5.QtCore import Qt
from src.ui.store_dialog import StoreDialog
from src.utils.file_storage import load_data, save_data
from src.utils.token_manager import start_token
from src.utils.api import fetch_store_info

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_store_id = None
        self.start_button     = None
        self.store_button     = None
        self.branch_value     = None
        self.store_name_value = None
        self.ui_set()
        self.load_store_id()


    def get_runtime_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


    def get_resource_path(self, relative_path):
        base = self.get_runtime_dir()
        return os.path.join(base, relative_path)


    def ui_set(self):
        self.setWindowTitle("PandoP")
        self.setMinimumSize(600, 200)
        self.setStyleSheet("""
            QWidget { background-color: #fff; font-family: Arial; font-size: 13px; }
            QLabel { color: #333; }
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

        layout = QVBoxLayout()
        layout.setSpacing(10)
        title = QLabel("PandoP")
        title.setStyleSheet("font-size: 20px; margin: 10px 20px 0 20px;")
        layout.addWidget(title, alignment=Qt.AlignLeft)

        info_box = QFrame()
        info_box.setObjectName("infoBox")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)

        label_section = QLabel("매장 정보")
        label_section.setStyleSheet("font-weight: bold; background-color: #fafafa;")
        info_layout.addWidget(label_section)

        row1 = QHBoxLayout()
        label1 = QLabel("● 매장명 :")
        label1.setFixedWidth(70)
        self.store_name_value = QLabel("-")
        row1.addWidget(label1)
        row1.addSpacing(10)
        row1.addWidget(self.store_name_value)
        row1.addStretch()

        row2 = QHBoxLayout()
        label2 = QLabel("● 지   점 :")
        label2.setFixedWidth(70)
        self.branch_value = QLabel("-")
        row2.addWidget(label2)
        row2.addSpacing(10)
        row2.addWidget(self.branch_value)
        row2.addStretch()

        info_layout.addLayout(row1)
        info_layout.addLayout(row2)
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)

        button_box = QHBoxLayout()
        self.store_button = QPushButton("등록")
        self.store_button.setFixedWidth(130)
        self.store_button.setCursor(Qt.PointingHandCursor)

        self.start_button = QPushButton("시작")
        self.start_button.setFixedWidth(130)
        self.start_button.setCursor(Qt.PointingHandCursor)

        button_box.addStretch()
        button_box.addWidget(self.store_button)
        button_box.addSpacing(20)
        button_box.addWidget(self.start_button)
        button_box.addStretch()

        layout.addLayout(button_box)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)
        self.setWindowFlag(Qt.Window)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.store_button.clicked.connect(self.open_store_dialog)
        self.start_button.clicked.connect(self.start_action)


    def load_store_id(self):
        data = load_data()
        self.current_store_id = data.get("store_id") or self.current_store_id
        self.store_name_value.setText(data.get("name") or "-")
        self.branch_value.setText(data.get("branch") or "-")


    def save_store_id(self, store_id):
        self.current_store_id = store_id
        data = load_data()
        data['store_id'] = store_id
        save_data(data)


    def open_store_dialog(self):
        dialog = StoreDialog(current_store_id=self.current_store_id)
        if dialog.exec_() == QDialog.Accepted:
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

        self.init_cert_and_proxy()
        time.sleep(2)

        if not self.wait_for_proxy():
            return

        data = load_data()
        data['store_id'] = self.current_store_id
        start_token(data)

        info = fetch_store_info(data['token'], data['store_id'])
        if info:
            self.store_name_value.setText(info.get("name", "-"))
            self.branch_value.setText(info.get("branch", "-"))
            data.update({"name": info.get("name", ""), "branch": info.get("branch", "")})
            save_data(data)
        else:
            print("매장 정보 요청 실패")

        self.store_button.hide()
        self.start_button.setText("종료")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.cleanup_and_exit)


    def set_windows_gui_proxy(self, host="127.0.0.1", port=8080):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}")
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            print(f"✅ Windows GUI 프록시 설정됨: {host}:{port}")
        except Exception as e:
            print(f"❌ 프록시 설정 실패: {e}")


    def kill_mitmdump_process(self):
        try:
            subprocess.call(["taskkill", "/F", "/IM", "mitmdump.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("🛑 기존 mitmdump 프로세스 종료됨")
        except Exception as e:
            print(f"⚠️ mitmdump 종료 실패: {e}")


    def init_cert_and_proxy(self):
        print("🔐 인증서 초기화 및 프록시 서버 시작 중...")

        # 1. 실행 중인 프록시 종료
        self.kill_mitmdump_process()

        # 2. 윈도우 시스템 프록시 설정
        self.set_windows_gui_proxy()

        # 3. 경로 설정
        mitmdump_path = self.get_resource_path("mitmdump.exe")
        user_profile  = os.environ.get("USERPROFILE", "")
        mitm_folder   = os.path.join(user_profile, ".mitmproxy")
        cert_path     = os.path.join(mitm_folder, "mitmproxy-ca-cert.cer")

        # 4. 기존 인증서 제거
        if os.path.exists(cert_path):
            subprocess.call(["certutil", "-delstore", "Root", "mitmproxy"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(mitm_folder):
            subprocess.call(f'rmdir /s /q "{mitm_folder}"', shell=True)

        # 5. 인증서 생성을 위해 잠깐 mitmdump 실행
        print("🔧 mitmdump 실행 중 (인증서 생성)...")
        subprocess.Popen(
            [mitmdump_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)

        self.kill_mitmdump_process()

        # 6. 인증서 등록
        if os.path.exists(cert_path):
            result = subprocess.call(["certutil", "-addstore", "Root", cert_path])
            if result != 0:
                print("❌ 인증서 등록 실패. 관리자 권한 필요!")
                return
            print("✅ 인증서 등록 완료!")
        else:
            print("❌ 인증서 생성 실패. mitmdump 실행 확인 필요.")
            return

        # 7. 프록시 서버 실행
        self.run_proxy()


    def run_proxy(self):
        print("[프록시] 프록시 실행 준비 중...")

        mitmdump_path = self.get_resource_path("mitmdump.exe")
        script_path   = self.get_resource_path("src/server/proxy_server.py")
        logs_dir      = self.get_resource_path("logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "proxy_server.log")

        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                subprocess.Popen(
                    [mitmdump_path, "--no-http2", "--ssl-insecure", "-s", script_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print(f"[프록시] mitmdump 실행 완료 (로그: {log_path})")
        except Exception as e:
            print(f"[프록시] 실행 실패: {e}")


    def cleanup_and_exit(self):
        print("🧹 종료 작업 수행 중...")

        # 1. 프록시 프로세스 종료
        self.kill_mitmdump_process()

        # 2. 윈도우 프록시 해제
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            print("✅ 프록시 설정 해제 완료")
        except Exception as e:
            print(f"❌ 프록시 해제 실패: {e}")

        # 3. 인증서 제거
        user_profile = os.environ.get("USERPROFILE", "")
        mitm_folder = os.path.join(user_profile, ".mitmproxy")
        try:
            subprocess.call(["certutil", "-delstore", "Root", "mitmproxy"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(mitm_folder):
                subprocess.call(f'rmdir /s /q "{mitm_folder}"', shell=True)
            print("✅ 인증서 제거 완료")
        except Exception as e:
            print(f"❌ 인증서 제거 실패: {e}")

        # 4. 종료
        self.close()


    def closeEvent(self, event):
        self.cleanup_and_exit()
        event.accept()