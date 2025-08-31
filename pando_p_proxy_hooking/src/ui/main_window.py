# src/ui/main_window.py
import os
import subprocess
import time
import socket
import ctypes
import winreg
import sys

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QFrame, QSpacerItem, QDialog, QCheckBox,
    QSystemTrayIcon, QMenu, QAction, QStyle
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from src.ui.store_dialog import StoreDialog
from src.utils.file_storage import load_data, save_data
from src.utils.token_manager import start_token
from src.utils.api import fetch_store_info
from src.utils.logger import ui_log, init_pando_logger


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.auto_login_checkbox = None
        self.current_store_id    = None
        self.start_button        = None
        self.store_button        = None
        self.branch_value        = None
        self.store_name_value    = None

        # 트레이 관련
        self.tray                = None
        self.tray_act_start      = None
        self.tray_act_stop       = None

        # 상태 플래그
        self.is_running          = False  # "시작" 후 동작 중 여부
        self.enable_tray_toast = False  # ✅ 알림(풍선) 표시 여부. 기본 False로 OFF

        self.init_set()

    # ─────────────────────────────────────────────────────────────────────────
    # 공용 경로 유틸
    def get_runtime_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    def get_resource_path(self, relative_path):
        base = self.get_runtime_dir()
        return os.path.join(base, relative_path)

    # ─────────────────────────────────────────────────────────────────────────
    # 초기화
    def init_set(self):
        init_pando_logger()
        self.ui_set()
        self.create_tray()         # ← 트레이 아이콘 구성

        self.load_store_id()

        # 자동로그인 설정이면 자동 시작
        if self.current_store_id and self.store_name_value and self.branch_value and self.auto_login_checkbox.isChecked():
            self.start_action()

    # ─────────────────────────────────────────────────────────────────────────
    # UI 구성
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

        # 자동 로그인 체크박스
        self.auto_login_checkbox = QCheckBox("자동 로그인", self)
        self.auto_login_checkbox.setCursor(Qt.PointingHandCursor)
        self.auto_login_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #444;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #888;
                background-color: #f0f0f0;
            }
            QCheckBox::indicator:checked {
                background-color: #4682B4;
                image: url();
            }
        """)

        data = load_data()
        checked = (data.get('auto_login') != "F")
        self.auto_login_checkbox.setChecked(checked)
        self.auto_login_checkbox.stateChanged.connect(self.on_auto_login_changed)

        checked_box = QHBoxLayout()
        checked_box.addStretch()
        checked_box.addWidget(self.auto_login_checkbox)
        checked_box.addStretch()
        layout.addLayout(checked_box)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 버튼 박스
        button_box = QHBoxLayout()
        self.store_button = QPushButton("등록")
        self.store_button.setFixedWidth(130)
        self.store_button.setCursor(Qt.PointingHandCursor)

        self.start_button = QPushButton("시작")  # 동적 변경: 시작 ↔ 중지
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

        # 시그널
        self.store_button.clicked.connect(self.open_store_dialog)
        self.start_button.clicked.connect(self.start_action)

    # ─────────────────────────────────────────────────────────────────────────
    # 트레이 아이콘/메뉴 구성
    def create_tray(self):
        # 초기 아이콘: 중지 상태(대기)
        initial_icon = "assets/pandop_off.ico"  # ← 원하는 파일명
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("PandoP")
        self.set_tray_icon(initial_icon)

        icon_path = self.get_resource_path("assets/pandop.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            # 아이콘 없으면 기본 아이콘 폴백
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)

        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("PandoP")

        menu = QMenu()

        act_show = QAction("열기", self)
        act_show.triggered.connect(self.showMainWindow)
        menu.addAction(act_show)
        menu.addSeparator()

        self.tray_act_start = QAction("시작", self)
        self.tray_act_start.triggered.connect(self.start_action)
        menu.addAction(self.tray_act_start)

        self.tray_act_stop = QAction("중지", self)
        self.tray_act_stop.setEnabled(False)  # 초기엔 중지 불가
        self.tray_act_stop.triggered.connect(self.stop_action)
        menu.addAction(self.tray_act_stop)

        menu.addSeparator()

        act_quit = QAction("종료", self)
        act_quit.triggered.connect(self.quit_app)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)

        # 좌클릭(Trigger)시 창 토글
        self.tray.activated.connect(self.on_tray_activated)

        self.tray.show()
        ui_log("[판도] 트레이 아이콘 준비됨")

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # 좌클릭
            self.showMainWindow()

    def showMainWindow(self):
        self.show()
        self.raise_()
        self.activateWindow()

    # ─────────────────────────────────────────────────────────────────────────
    # 설정 저장
    def on_auto_login_changed(self):
        auto_login = "T" if self.auto_login_checkbox.isChecked() else "F"
        data = load_data()
        data['auto_login'] = auto_login
        save_data(data)

    # ─────────────────────────────────────────────────────────────────────────
    # 스토어 로드/저장
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

    # ─────────────────────────────────────────────────────────────────────────
    # 프록시 대기/시작/중지/종료
    def wait_for_proxy(self, port=8080, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                if result == 0:
                    ui_log(f"[판도] 프록시 서버가 포트 {port}에서 실행 중입니다.")
                    return True
            time.sleep(0.5)
        ui_log(f"[판도] 프록시 서버가 포트 {port}에서 실행되지 않았습니다.")
        return False

    def start_action(self):
        """시작(프록시/토큰/매장정보)"""
        if self.is_running:
            return
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
            ui_log("[판도] 매장 정보 요청 실패")

        # 상태 전환: 실행 중
        self.is_running = True
        # 실행 중 아이콘
        self.set_tray_icon("assets/pandop_on.ico")

        self.store_button.hide()

        # 버튼/트레이 상태 동기화
        try:
            self.start_button.clicked.disconnect()
        except Exception:
            pass
        self.start_button.setText("중지")
        self.start_button.clicked.connect(self.stop_action)

        if self.tray_act_start: self.tray_act_start.setEnabled(False)
        if self.tray_act_stop:  self.tray_act_stop.setEnabled(True)

        # 트레이 풍선 도움말
        # ↓↓↓ 알림 off (필요하면 True로 켜고, 메시지 유지)
        if self.tray and self.enable_tray_toast:
            self.tray.showMessage("PandoP", "동작을 시작했습니다. 창을 닫아도 트레이에서 계속 실행됩니다.",
                                  QSystemTrayIcon.Information, 2500)


    def stop_action(self):
        """중지(프록시/인증서 정리). 창은 닫지 않음."""
        if not self.is_running:
            return

        self._do_cleanup()  # 실제 정리 로직

        # 상태 전환: 중지됨
        self.is_running = False
        # 중지(대기) 아이콘
        self.set_tray_icon("assets/pandop_off.ico")
        self.store_button.show()

        try:
            self.start_button.clicked.disconnect()
        except Exception:
            pass
        self.start_button.setText("시작")
        self.start_button.clicked.connect(self.start_action)

        if self.tray_act_start: self.tray_act_start.setEnabled(True)
        if self.tray_act_stop:  self.tray_act_stop.setEnabled(False)

        if self.tray and self.enable_tray_toast:
            self.tray.showMessage("PandoP", "동작을 중지했습니다. 필요 시 다시 시작하세요.",
                                  QSystemTrayIcon.Information, 2500)

    def quit_app(self):
        """트레이 '종료'에서 호출: 동작 중이면 정리 후 앱 종료"""
        if self.is_running:
            self._do_cleanup()
            self.is_running = False
        # 앱 완전 종료
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().quit()

    # ─────────────────────────────────────────────────────────────────────────
    # 기존 정리 로직 분리
    def _do_cleanup(self):
        """프록시/인증서 정리 (창 닫지 않음). 기존 cleanup_and_exit의 핵심만 분리."""
        ui_log("[판도] 🧹 정리 작업 수행 중...")
        self.kill_mitmdump_process()
        # 1) 프록시 해제
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            ui_log("[판도] 프록시 설정 해제 완료")
        except Exception as e:
            ui_log(f"[판도] 프록시 해제 실패: {e}")

        # 2) 인증서 제거
        user_profile = os.environ.get("USERPROFILE", "")
        mitm_folder = os.path.join(user_profile, ".mitmproxy")
        try:
            subprocess.call(["certutil", "-delstore", "Root", "mitmproxy"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(mitm_folder):
                subprocess.call(f'rmdir /s /q "{mitm_folder}"', shell=True)
            ui_log("[판도] 인증서 제거 완료")
        except Exception as e:
            ui_log(f"[판도] 인증서 제거 실패: {e}")

    # (유지) 기존 메서드는 Quit 경로에서만 사용하도록 래핑 가능
    def cleanup_and_exit(self):
        """하위호환: 호출되면 정리 후 앱 종료"""
        self._do_cleanup()
        self.close()  # closeEvent에서 실제 종료 로직을 가로채지 않도록 아래에서 처리

    # ─────────────────────────────────────────────────────────────────────────
    # 프록시/인증서 셋업 & 실행
    def set_windows_gui_proxy(self, host="127.0.0.1", port=8080):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}")
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            ui_log(f"[판도] Windows GUI 프록시 설정됨: {host}:{port}")
        except Exception as e:
            ui_log(f"[판도] 프록시 설정 실패: {e}")

    def kill_mitmdump_process(self):
        try:
            subprocess.call(["taskkill", "/F", "/IM", "mitmdump.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ui_log("[판도] 기존 mitmdump 프로세스 종료됨")
        except Exception as e:
            ui_log(f"[판도] mitmdump 종료 실패: {e}")

    def init_cert_and_proxy(self):
        ui_log("[판도] 인증서 초기화 및 프록시 서버 시작 중...")
        self.kill_mitmdump_process()
        self.set_windows_gui_proxy()

        mitmdump_path = self.get_resource_path("mitmdump.exe")
        user_profile  = os.environ.get("USERPROFILE", "")
        mitm_folder   = os.path.join(user_profile, ".mitmproxy")
        cert_path     = os.path.join(mitm_folder, "mitmproxy-ca-cert.cer")

        if os.path.exists(cert_path):
            subprocess.call(["certutil", "-delstore", "Root", "mitmproxy"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(mitm_folder):
            subprocess.call(f'rmdir /s /q "{mitm_folder}"', shell=True)

        ui_log("[판도] 🔧 mitmdump 실행 중 (인증서 생성)...")
        subprocess.Popen([mitmdump_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)

        self.kill_mitmdump_process()

        if os.path.exists(cert_path):
            result = subprocess.call(["certutil", "-addstore", "Root", cert_path])
            if result != 0:
                ui_log("[판도] 인증서 등록 실패. 관리자 권한 필요!")
                return
            ui_log("[판도] 인증서 등록 완료!")
        else:
            ui_log("[판도] 인증서 생성 실패. mitmdump 실행 확인 필요.")
            return

        self.run_proxy()

    def run_proxy(self):
        ui_log("[판도] [프록시] 프록시 실행 준비 중...")
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

            # 운영시 로그 완전 비활성화 버전
            # subprocess.Popen(
            #     [mitmdump_path, "--no-http2", "--ssl-insecure", "-s", script_path],
            #     creationflags=subprocess.CREATE_NO_WINDOW
            # )

            ui_log(f"[판도] [프록시] mitmdump 실행 완료 (로그: {log_path})")
        except Exception as e:
            ui_log(f"[판도] [프록시] 실행 실패: {e}")


    def set_tray_icon(self, relative_path: str) -> None:
        """
        트레이 아이콘을 교체한다. 존재하지 않으면 기본 아이콘으로 폴백.
        """
        try:
            path = self.get_resource_path(relative_path)
            if os.path.exists(path):
                icon = QIcon(path)
                self.tray.setIcon(icon)
                # (선택) 메인 윈도우 아이콘도 맞춰서 변경
                self.setWindowIcon(icon)
                ui_log(f"[판도] 트레이 아이콘 변경: {relative_path}")
            else:
                # 폴백: 시스템 기본 아이콘
                fallback = self.style().standardIcon(QStyle.SP_ComputerIcon)
                self.tray.setIcon(fallback)
                ui_log(f"[판도] 아이콘 파일 없음 → 기본 아이콘 사용: {relative_path}")
        except Exception as e:
            ui_log(f"[판도] 아이콘 변경 실패: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 창 닫힘/최소화 처리 (트레이로 이동)
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # ✅ 숨길 때 토스트 띄우지 않음
        if self.tray and self.enable_tray_toast:
            self.tray.showMessage("PandoP", "트레이로 이동했습니다. 종료는 트레이 아이콘 우클릭 → '종료'.",
                                  QSystemTrayIcon.Information, 2500)
        ui_log("[판도] 창이 트레이로 숨겨졌습니다.")