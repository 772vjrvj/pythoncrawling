# src/ui/main_window.py
import os
import subprocess
import time
import socket
import ctypes
import winreg
import sys
import shutil
import threading
import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QFrame, QSpacerItem, QDialog, QCheckBox,
    QSystemTrayIcon, QMenu, QAction, QStyle, QMessageBox,
    QDesktopWidget  # === 신규 ===
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.store_dialog import StoreDialog
from src.utils.file_storage import load_data, save_data
from src.utils.token_manager import start_token
from src.utils.api import fetch_store_info
from src.utils.logger import ui_log, init_pando_logger
from src.ui.init_dialog import InitDialog
from pathlib import Path

class MainWindow(QWidget):

    proxy_ready = pyqtSignal(bool, dict)


    # region : 초기 init
    def __init__(self):
        super().__init__()
        self.init_dialog         = None
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
        self.enable_tray_toast   = False  # 알림(풍선) 표시 여부. 기본 False로 OFF

        # 프록시 프로세스 및 로그 파일 핸들 보관
        self.proxy_proc          = None
        self.proxy_log_file      = None

        self.init_set()
    # endregion


    # region : 초기화
    def init_set(self):
        init_pando_logger()
        self.ui_set()
        self.create_tray()
        self.load_store_id()
        self.proxy_ready.connect(self.on_proxy_ready)

        # 자동로그인 설정이면 자동 시작
        if self.current_store_id and self.store_name_value.text() != "-" and self.branch_value.text() != "-" and self.auto_login_checkbox.isChecked():
            self.start_action()
    # endregion


    # === 신규 === MainWindow 중앙에 자식 다이얼로그 배치 유틸
    def _center_over_self(self, child: QWidget) -> None:
        try:
            # frameGeometry()를 사용해야 윈도우 테두리/그림자까지 포함한 실제 사이즈 기준 정렬 가능
            parent_fg = self.frameGeometry()
            child_fg  = child.frameGeometry()
            child_fg.moveCenter(parent_fg.center())
            child.move(child_fg.topLeft())
        except Exception as e:
            ui_log(f"_center_over_self 실패: {e}")


    # region : 공용 경로 유틸
    # 현재 실행경로를 가져옴
    def get_runtime_dir(self):

        # sys.frozen = PyInstaller로 묶였다는 표시.
        # 이 경우 sys.executable이 곧 main.exe의 절대경로니까, 그 디렉토리를 반환 → dist\ 안.
        # 즉, 빌드된 EXE가 있는 폴더 경로.
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)

        # 개발 환경(Python 소스 실행)일 때
        # __file__ = 현재 파이썬 소스 파일 경로 (src/ui/main_window.py).
        # 거기서 ../../ 올라가면 프로젝트 루트 근처가 됨.
        # 즉, 소스 실행 시에도 실행 루트와 비슷한 위치를 반환.
        else:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    # endregion


    # region : 프로그램 전체 경로
    def get_resource_path(self, relative_path):
        base = self.get_runtime_dir()
        return os.path.join(base, relative_path)
    # endregion


    # region : UI 구성
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
    # endregion


    # region : 트레이 아이콘/메뉴 구성
    def create_tray(self):
        # 초기 아이콘: 중지 상태(대기)
        icon_path = self.get_resource_path("assets/pandop_off.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)        # 윈도우 아이콘
        else:
            # 아이콘 없으면 기본 아이콘 폴백
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
            self.setWindowIcon(icon)        # 윈도우 아이콘

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
        ui_log("트레이 아이콘 준비됨")
    # endregion


    # region : 스토어 로드/저장
    def load_store_id(self):
        data = load_data()
        self.current_store_id = data.get("store_id") or self.current_store_id
        self.store_name_value.setText(data.get("name") or "-")
        self.branch_value.setText(data.get("branch") or "-")
    # endregion


    # region : 트레이 창 닫힘/최소화 처리 (트레이로 이동)
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # ✅ 숨길 때 토스트 띄우지 않음
        if self.tray and self.enable_tray_toast:
            self.tray.showMessage("PandoP", "트레이로 이동했습니다. 종료는 트레이 아이콘 우클릭 → '종료'.",
                                  QSystemTrayIcon.Information, 2500)
        ui_log("창이 트레이로 숨겨졌습니다.")
    # endregion


    # region : 트래이 화면 최대화
    def showMainWindow(self):
        self.show()
        self.raise_()
        self.activateWindow()
    # endregion


    # region : 좌클릭(Trigger)시 창 토글
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # 좌클릭
            self.showMainWindow()
    # endregion


    # region : mitmdump.exe 종료
    # /F : 강제 종료 (force).
    # /IM mitmdump.exe : 이미지 이름(프로세스 이름)을 기준으로 종료 대상 지정.
    # /T : 자식 프로세스들도 함께 종료(트리 종료).
    # taskkill /F /IM mitmdump.exe /T
    def kill_mitmdump_process(self):
        """
        mitmdump 프로세스 강제 종료.
        - 성공: info 로그
        - 프로세스 없음: info 로그 (에러 아님)
        - 실패: RuntimeError 발생 (상위로 전파)
        """
        res = subprocess.run(
            ["taskkill", "/F", "/IM", "mitmdump.exe", "/T"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if res.returncode == 0:
            ui_log("[info] 기존 mitmdump.exe 프로세스 종료됨 (taskkill)")
            return

        # === 신규 ===: 프로세스 없음은 에러가 아님
        if "찾을 수 없습니다" in res.stderr or "not found" in res.stderr.lower():
            ui_log("[info] mitmdump.exe 프로세스 없음(이미 종료됨)")
            return

        # 실패는 예외로 바로 올림
        msg = f"mitmdump.exe 에러 taskkill rc={res.returncode}, stdout={res.stdout!r}, stderr={res.stderr!r}"
        ui_log(msg)
        raise RuntimeError(msg)
    # endregion


    # region : 프록시 셋업 & 실행
    def set_windows_gui_proxy(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        r"""
        기존의 HKCU(사용자 레벨) 프록시 설정을 수행한 뒤,
        가능한 경우 WinHTTP(머신/서비스 레벨)와도 동기화한다.

        동작 요약:
          1) HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
             에 ProxyEnable / ProxyServer 값 설정 (사용자 UI/브라우저에 적용)
          2) WinInet API 호출로 변경 즉시 반영 (InternetSetOptionW SETTINGS_CHANGED + REFRESH)
          3) self.set_winhttp_proxy() 호출하여 WinHTTP(서비스/머신 레벨)도 동기화 시도
        주석/로그를 자세히 남기므로 문제 디버깅에 용이함.
        """
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        proxy_value = f"{host}:{port}"
        try:
            # HKCU(현재 로그인 사용자) 레지스트리에 프록시 활성화/서버 저장
            # HKEY_CURRENT_USER 를 사용하므로 "현재 프로세스를 실행한 사용자"의 설정을 변경함.
            # 만약 프로세스가 SYSTEM등 다른 계정으로 실행 중이면 UI에 반영되지 않을 수 있음(이 경우 WinHTTP로도 동기화 필요).
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                # ProxyEnable = 1 (프록시 사용)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                # ProxyServer = "host:port"
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_value)

                # 로컬 주소(예: 127.0.0.1, localhost)나 특정 도메인을 프록시 우회하려면 ProxyOverride를 설정할 수 있음.
                # 예: winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>;127.0.0.1;localhost")
                # (현재 코드는 기본적으로 우회 항목을 비워둠 — 필요 시 주석 해제)
                # winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>;127.0.0.1;localhost")

            #  WinInet에 설정 변경을 알림 -> 대부분의 앱/브라우저(WinINet 기반)에 즉시 반영
            # INTERNET_OPTION_SETTINGS_CHANGED = 39, INTERNET_OPTION_REFRESH = 37
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)

            ui_log(f"Windows GUI 프록시 설정됨: {proxy_value} (HKCU에 적용)")

            # WinHTTP (서비스/머신 레벨)도 동기화 시도
            # - 과거 권한 문제로 UI에 반영되지 않았던 환경을 보완하기 위해 병행 적용 권장
            ok = self.set_winhttp_proxy(host, port)
            if not ok:
                ui_log("WinHTTP 동기화 실패 — HKCU(사용자) 설정은 적용되었음")

        except Exception as e:
            # 레지스트리 접근 실패, 권한 문제, 또는 WinInet API 호출 문제 등이 여기로 잡힘
            ui_log(f"프록시/인증서 셋업 & 실행 실패: {e}")
            raise
    # endregion


    # region : WinHTTP(머신/서비스 레벨) 프록시 설정
    def set_winhttp_proxy(self, host: str = "127.0.0.1", port: int = 8080) -> bool:
        """
        WinHTTP (시스템/서비스 레벨) 프록시를 설정한다.
        - 우선 현재 사용자(IE/WinINet)의 설정을 WinHTTP로 복사(import)하여 동기화하려 시도한다.
        - import 실패 시 fallback으로 직접 WinHTTP 프록시를 설정(set)한다.
        - 반환: 성공(True) / 실패(False)
        주의: netsh 명령은 관리자 권한 필요. EXE는 --uac-admin으로 빌드되어야 함.
        """
        proxy_spec = f"{host}:{port}"
        try:
            # === 신규 ===: 우선 HKCU(IE/WinINet) 설정을 WinHTTP로 복사해 동기화
            # import from IE 는 보통 "UI에서 설정한 값"을 WinHTTP로 옮김 -> WinHTTP를 사용하는 서비스도 동일한 프록시를 사용하게 됨
            subprocess.run(
                ["netsh", "winhttp", "import", "proxy", "source=ie"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            ui_log(f"winhttp proxy imported from IE (동기화 성공)")
            return True
        except subprocess.CalledProcessError as e:
            # import가 실패하면(예: 현재 IE 설정 없음 등) fallback으로 직접 WinHTTP 프록시를 설정시도
            ui_log(f"winhttp import 실패(아마 IE설정 없음) — fallback 시도: {e}")
        except Exception as e:
            ui_log(f"winhttp import 예외: {e}")

        # import 실패 시 직접 설정 시도
        try:
            subprocess.run(
                ["netsh", "winhttp", "set", "proxy", proxy_spec],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            ui_log(f"winhttp proxy set: {proxy_spec} (동기화 성공 : fallback)")
            return True
        except subprocess.CalledProcessError as e:
            ui_log(f"winhttp set proxy 실패: rc={e.returncode} / {e}")
            return False
        except Exception as e:
            ui_log(f"winhttp set proxy 예외: {e}")
            return False
    # endregion


    # region : mitmproxy 인증서/폴더 정리 전용 함수
    def cleanup_mitm_cert(self, mitm_folder, cert_path) -> None:
        ui_log("🔧 mitmdump 기존 인증서/폴더 정리 (있으면 삭제)")

        # 1) 루트 스토어 인증서 제거
        if os.path.exists(cert_path):
            try:
                res = subprocess.run(
                    ["certutil", "-delstore", "Root", "mitmproxy"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
            except Exception as e:
                ui_log(f"certutil -delstore 호출 예외: {e}")
                raise

            if res.returncode == 0:
                ui_log("certutil -delstore: 삭제 성공(루트 스토어에서 제거됨).")
                if res.stdout:
                    ui_log(f"certutil stdout: {res.stdout.strip()}")
            else:
                if res.stdout:
                    ui_log(f"certutil stdout: {res.stdout.strip()}")
                if res.stderr:
                    ui_log(f"certutil stderr: {res.stderr.strip()}")
                ui_log(f"certutil -delstore 실패: rc={res.returncode}")
                raise RuntimeError(f"certutil -delstore 실패: rc={res.returncode}")

        # 2) mitmproxy 폴더 삭제
        if os.path.exists(mitm_folder):
            try:
                shutil.rmtree(mitm_folder)
                ui_log(f"기존 .mitmproxy 폴더 삭제: {mitm_folder}")
            except Exception as e:
                ui_log(f".mitmproxy 폴더 삭제 실패: {e}")
                raise
    # endregion


    # region : CPU 상태에 따라 인증서 생성 타임아웃을 동적으로 조정
    def get_dynamic_timeout(self) -> int:
        """
        CPU 상태에 따라 인증서 생성 타임아웃을 동적으로 조정한다.
        - 기본값: 180초
        - CPU 사용률 >= 60%: 300초
        - CPU 사용률 >= 90%: 600초
        실패 시 예외를 상위로 전파한다.
        """
        timeout = 180
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
        except Exception as e:
            ui_log(f"CPU 사용률 측정 실패 기본값 설정: {e}")
            return timeout

        # 기본 타임아웃
        
        if cpu_percent >= 90:
            timeout = 600
        elif cpu_percent >= 60:
            timeout = 300

        ui_log(f"CPU 사용률 감지: {cpu_percent:.1f}% -> 인증서 생성 타임아웃 설정 {timeout}s.")
        return timeout
    # endregion


    # region : mitmdump 실행 + (베스트에포트) 우선순위 낮추기.
    def start_mitmdump(self) -> subprocess.Popen:
        """
        mitmdump 실행 + (베스트에포트) 우선순위 낮추기.
        - 실패 시: 로그 찍고 예외를 상위로 전파
        - 성공 시: Popen 객체 반환
        """
        ui_log("🔧 mitmdump 실행 중 (인증서 생성 시작)...")

        mitmdump_path = self.get_resource_path("mitmdump.exe")
        if not os.path.exists(mitmdump_path):
            msg = f"mitmdump 실행 파일 미발견: {mitmdump_path}"
            ui_log(msg)
            raise FileNotFoundError(msg)

        try:
            proc = subprocess.Popen(
                [mitmdump_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,  # Windows
            )
        except Exception as e:
            ui_log(f"mitmdump 실행 실패: {e}")
            raise

        # 우선순위 낮추기 (실패해도 치명적이지 않으므로 로그만)
        try:
            p = psutil.Process(proc.pid)
            if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)  # Windows 전용
            else:
                p.nice(10)  # *nix 베스트-에포트
        except Exception as e_nice:
            ui_log(f"mitmdump 우선도 설정 실패: {e_nice}")

        return proc
    # endregion


    # region : mitmdump가 인증서 파일을 생성할 때까지 대기
    def wait_for_mitmdump_cert(self, cert_path: str) -> None:
        """
        mitmdump가 인증서 파일을 생성할 때까지 대기.
        - 성공: 정상 종료(반환값 없음)
        - 실패(타임아웃): 로그 후 예외 전파
        """
        timeout = self.get_dynamic_timeout()

        ui_log("🔧 mitmdump 인증서 파일 생성 확인중...")
        interval = 0.5
        elapsed = 0.0

        while elapsed < timeout:
            if os.path.exists(cert_path):
                break
            time.sleep(interval)
            elapsed += interval

        if not os.path.exists(cert_path):
            ui_log(f"🔧 인증서 파일 생성 타임아웃 (없음): {cert_path}")
            # 타임아웃 시에도 프로세스 정리는 시도하고, 실패하면 그 예외가 상위로 전파됨
            self.kill_mitmdump_process()
            raise TimeoutError(f"mitmdump 인증서 생성 타임아웃: {cert_path} (timeout={timeout}s)")

        ui_log("🔧 mitmdump 인증서 파일 생성 확인 완료")
        # 성공해도 프로세스는 종료
        self.kill_mitmdump_process()
        ui_log("🔧 mitmdump 인증서 생성 후 mitmdump.exe 종료")
    # endregion


    # region : 생성된 mitmproxy 인증서를 루트 스토어에 등록
    def install_mitm_cert(self, cert_path: str) -> None:
        """
        생성된 mitmproxy 인증서를 루트 스토어에 등록한다.
        - 성공: 로그만 남기고 종료
        - 실패: 로그 남기고 예외 전파
        """
        ui_log("🔧 mitmdump 인증서 생성 루트 스토어에 등록")

        try:
            res = subprocess.run(
                ["certutil", "-addstore", "Root", cert_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as e:
            ui_log(f"certutil addstore 호출 예외: {e}")
            raise

        if res.returncode != 0:
            ui_log(f"certutil addstore 실패: rc={res.returncode}, stdout={res.stdout}, stderr={res.stderr}")
            raise RuntimeError(f"certutil addstore 실패: rc={res.returncode}")

        ui_log("인증서 등록 완료!")
        if res.stdout:
            ui_log(f"certutil stdout: {res.stdout.strip()}")
    # endregion


    # region : 인증서 초기화
    def init_cert(self):
        ui_log("인증서 초기화 및 프록시 서버 시작 중...")

        user_profile = os.environ.get("USERPROFILE", "") or str(Path.home())
        mitm_folder  = os.path.join(user_profile, ".mitmproxy")
        cert_path    = os.path.join(mitm_folder, "mitmproxy-ca-cert.cer")

        try:
            # 1. mitmdump.exe process 종료
            self.kill_mitmdump_process()

            # 2. 프록시 셋업 & 실행
            self.set_windows_gui_proxy()

            # 3. mitmproxy 인증서/폴더 정리 전용 함수
            self.cleanup_mitm_cert(mitm_folder, cert_path)

            # 4. mitmdump 실행 + (베스트에포트) 우선순위 낮추기.
            self.start_mitmdump()

            # 5. mitmdump가 인증서 파일을 생성할 때까지 대기
            self.wait_for_mitmdump_cert(cert_path)

            # 6. 생성된 mitmproxy 인증서를 루트 스토어에 등록
            self.install_mitm_cert(cert_path)

        except Exception as e:
            ui_log(f"인증서 초기화 및 프록시 서버 시작 중 오류: {e}")
            raise
    # endregion


    # region : proxy 서버 시작
    def run_proxy(self) -> None:
        """
        mitmdump 기반 프록시 실행.
        - 로그 파일을 열어 stdout/stderr를 기록
        - 실행된 프로세스를 self.proxy_proc에 저장 (나중에 정리 가능)
        - 실행 실패 시 RuntimeError 발생
        """
        ui_log("[프록시] 프록시 실행 준비 중...")

        mitmdump_path = self.get_resource_path("mitmdump.exe")
        script_path   = self.get_resource_path("src/server/proxy_server.py")
        logs_dir      = self.get_resource_path("logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "proxy_server.log")

        # --- 1) 이전 로그 핸들 닫기 (치명적이지 않음) ---
        if self.proxy_log_file:
            try:
                self.proxy_log_file.close()
            except Exception as e_close:
                ui_log(f"[프록시] 이전 로그 핸들 닫기 실패: {e_close}")
            self.proxy_log_file = None

        # --- 2) 로그 파일 열기 + 3) 프로세스 실행 (치명적) ---
        try:
            self.proxy_log_file = open(log_path, "w", encoding="utf-8")
            self.proxy_proc = subprocess.Popen(
                [mitmdump_path, "--no-http2", "--ssl-insecure", "-s", script_path],
                stdout=self.proxy_log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            ui_log(f"[프록시] 실행 실패: {e}")
            raise RuntimeError(f"프록시 실행 실패: {e}") from e

        # --- 4) 우선도 낮추기 (비치명적) ---
        try:
            p2 = psutil.Process(self.proxy_proc.pid)
            if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
                p2.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)  # Windows
            else:
                p2.nice(10)  # *nix fallback
        except Exception as e_nice:
            ui_log(f"[프록시] proxy_proc 우선도 설정 실패: {e_nice}")

        # --- 5) 실행 완료 로그 ---
        ui_log(f"[프록시] mitmdump 실행 완료 (로그: {log_path})")
    # endregion



    # region : 프록시 대기/시작/중지/종료
    def wait_for_proxy(self, port: int = 8080, timeout: int = 30) -> bool:
        try:
            start = time.time()
            deadline = start + timeout
            while time.time() < deadline:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    result = sock.connect_ex(("127.0.0.1", port))
                if result == 0:
                    ui_log(f"프록시 서버가 포트 {port}에서 실행 중입니다.")
                    return True
                time.sleep(0.5)

            # 타임아웃 → 실패는 예외로 전파
            msg = f"프록시 서버가 포트 {port}에서 {timeout}s 내에 실행되지 않았습니다."
            ui_log(msg)
            raise TimeoutError(msg)
        except Exception as e:
            ui_log(f"wait_for_proxy 예외: {e}")
            raise
    # endregion


    # region : update_store_info
    def update_store_info(self) -> dict:
        """
        - load_data() 로 기존 데이터 불러오기
        - 현재 store_id 설정 후 start_token(data) 호출
        - token 없으면 에러로 처리 (로그 찍고 예외 전파)
        - fetch_store_info(token, store_id) 실패/None이면 에러로 처리
        - 성공 시 name/branch 갱신하고 save_data(data)
        - 최종 data 반환
        """
        try:
            data = load_data()
            data["store_id"] = self.current_store_id

            # 토큰 발급/갱신
            start_token(data)
            token = data.get("token")
            if not token:
                ui_log("[error] 토큰 생성 실패: token 없음")
                raise RuntimeError("토큰 생성 실패")

            # 매장 정보 조회
            info = fetch_store_info(token, data["store_id"])
            if not info:
                ui_log("[error] 매장 정보 조회 실패: 결과 없음")
                raise RuntimeError("매장 정보 조회 실패")

            # 데이터 갱신 및 저장
            data.update({
                "name": info.get("name", ""),
                "branch": info.get("branch", "")
            })
            save_data(data)
            ui_log("[info] 매장 정보 저장 완료")

        except Exception as e:
            ui_log(f"[error] update_store_info 예외: {e}")
            raise
    # endregion


    # region : background 초기화
    def _background_init(self):
        """
        백그라운드에서 인증서/프록시 초기화 후 프록시 확인, 토큰/매장정보 요청까지 수행.
        완료 시 proxy_ready 시그널을 emit 함.
        """

        try:
            # 1. 인증서 초기화
            self.init_cert()

            # 2. proxy 서버 시작
            self.run_proxy()

            # 3. 프록시 대기/시작/중지/종료
            self.wait_for_proxy(timeout=30)
            
            # 4. 매장 정보 저장
            self.update_store_info()

            # 5. 화면 갱신
            self.proxy_ready.emit(True, {}) # on_proxy_ready

        except Exception as e:
            ui_log(f"백그라운드 처리 중 예외: {e}")
            self.proxy_ready.emit(False, {'msg': e}) # on_proxy_ready

    # endregion


    # region : tray icon set
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
                ui_log(f"트레이 아이콘 변경: {relative_path}")
            else:
                # 폴백: 시스템 기본 아이콘
                fallback = self.style().standardIcon(QStyle.SP_ComputerIcon)
                self.tray.setIcon(fallback)
                self.setWindowIcon(fallback)
                ui_log(f"아이콘 파일 없음 → 기본 아이콘 사용: {relative_path}")
        except Exception as e:
            ui_log(f"아이콘 변경 실패: {e}")
    # endregion


    # region : proxy 준비
    def on_proxy_ready(self, success: bool, info: dict):
        """
        백그라운드 초기화 완료 콜백 (메인 스레드).
        UI 업데이트 및 상태 전환을 여기서 안전하게 수행.
        """
        self.init_dialog.close()       # 창 닫기
        self.init_dialog.deleteLater() # Qt가 메모리 안전하게 해제하도록 예약
        self.init_dialog = None        # Python에서 참조 해제

        if not success:
            try:
                self._do_cleanup()
            except Exception as e:
                ui_log(f"cleanup 실행 중 예외: {e}")

            self.start_button.setEnabled(True)
            self.store_button.setEnabled(True)
            self._notify_start_failed(
                "프록시/인증서 초기화에 실패했습니다.\n"
                f"{info.get('msg', '-')}"  # === 신규 ===: 따옴표 충돌 수정
            )
            ui_log("프록시 초기화 실패로 인해 시작이 취소되었습니다.")
            return

        data = load_data()
        self.store_name_value.setText(data.get("name"))
        self.branch_value.setText(data.get("branch"))

        self.is_running = True
        self.set_tray_icon("assets/pandop_on.ico")
        self.store_button.hide()

        # 버튼/트레이 상태 동기화
        self.start_button.clicked.disconnect()
        self.start_button.setText("중지")
        self.start_button.clicked.connect(self.stop_action)
        self.start_button.setEnabled(True)

        self.tray_act_start.setEnabled(False)
        self.tray_act_stop.setEnabled(True)

        if self.enable_tray_toast:
            self.tray.showMessage("PandoP", "동작을 시작했습니다. 창을 닫아도 트레이에서 계속 실행됩니다.", QSystemTrayIcon.Information, 2500)
    # endregion


    # region : [버튼 이벤트] 자동 시작 저장
    def on_auto_login_changed(self):
        auto_login = "T" if self.auto_login_checkbox.isChecked() else "F"
        data = load_data()
        data['auto_login'] = auto_login
        save_data(data)
    # endregion


    # region : [버튼 이벤트] id 저장
    def save_store_id(self, store_id):
        self.current_store_id = store_id
        data = load_data()
        data['store_id'] = store_id
        save_data(data)
    # endregion


    # region : [버튼 이벤트] 업장 저장 팝업
    def open_store_dialog(self):
        dialog = StoreDialog(current_store_id=self.current_store_id)
        if dialog.exec_() == QDialog.Accepted:
            store_id = dialog.get_data()
            if store_id is not None:
                self.save_store_id(store_id)
    # endregion


    # region : [버튼 이벤트] 시작버튼 클릭시 시작 이벤트
    def start_action(self):

        """시작(프록시/토큰/매장정보)"""
        if self.is_running:
            return

        if not self.current_store_id:
            self._notify_start_failed("매장 등록이 필요합니다.\n'등록' 버튼으로 매장 ID를 설정한 뒤 다시 시작하세요.")
            return

        self.start_button.setEnabled(False)
        self.store_button.setEnabled(False)

        self.init_dialog = InitDialog(self)
        self.init_dialog.show()
        self._center_over_self(self.init_dialog)  # === 신규 === MainWindow 정중앙에 배치

        t = threading.Thread(target=self._background_init, daemon=True)
        t.start()
    # endregion ====================


    # region: mitmdump 프로세스 존재 여부 확인 (tasklist 사용, 외부 의존성 없음)
    def _is_mitmdump_running(self) -> bool:
        try:
            # tasklist 출력에서 mitmdump.exe를 찾음
            res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq mitmdump.exe"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            out = (res.stdout or "").lower()
            return "mitmdump.exe" in out
        except Exception:
            # 호출 실패 시 안전하게 True로 두지 않고 False 반환(없는 것으로 간주)
            return False
    # endregion


    # region : 해제 함수 winhttp proxy reset
    def reset_winhttp_proxy(self) -> bool:
        try:
            subprocess.run(["netsh", "winhttp", "reset", "proxy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ui_log("winhttp proxy reset 완료")
            return True
        except Exception as e:
            ui_log(f"winhttp reset 실패: {str(e)}")
            return False
    # endregion


    # region: 해제 함수 (HKCU + WinHTTP 모두 롤백)
    def unset_windows_gui_proxy(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
                winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "")
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            ui_log("Windows GUI 프록시 해제됨")
        except Exception as e:
            ui_log(f"프록시 해제 실패: {str(e)}")

        # WinHTTP도 리셋
        try:
            self.reset_winhttp_proxy()
        except Exception as e:
            ui_log(f"winhttp reset 예외: {str(e)}")
    # endregion


    # region: 오류 알림(팝업/트레이) 유틸
    def _notify_start_failed(self, msg: str) -> None:
        """
        시작/초기화 실패 시 알림창을 띄우고, 실패하면 트레이 풍선으로 폴백.
        - 절대: 기존 import 라인 수정 없이, 함수 내부에서만 임포트
        """
        try:
            QMessageBox.critical(self, "PandoP - 시작 실패", msg, QMessageBox.Ok)
        except Exception:
            # 팝업이 불가능한 환경이면 트레이 풍선으로 폴백
            self.tray.showMessage("PandoP - 시작 실패", msg, QSystemTrayIcon.Critical, 4000)
    # endregion


    # region : 기존 정리 로직 분리
    def _do_cleanup(self):
        """프록시/인증서 정리 (창 닫지 않음). 기존 cleanup_and_exit의 핵심만 분리."""
        ui_log("🧹 정리 작업 수행 중...")

        # 1) proxy_proc 종료 + 로그파일 핸들 정리
        try:
            if self.proxy_proc and self.proxy_proc.poll() is None:
                ui_log("proxy_proc 종료 시도(terminate)")
                self.proxy_proc.terminate()
                try:
                    self.proxy_proc.wait(timeout=5)
                    ui_log(f"proxy_proc 종료 완료 (rc={self.proxy_proc.returncode})")
                except subprocess.TimeoutExpired:
                    ui_log("terminate 타임아웃 → kill 시도")
                    self.proxy_proc.kill()
                    try:
                        self.proxy_proc.wait(timeout=3)
                        ui_log(f"proxy_proc kill 완료 (rc={self.proxy_proc.returncode})")
                    except Exception as e:
                        ui_log(f"proxy_proc kill 대기 중 예외: {e}")

            if self.proxy_log_file:
                try:
                    self.proxy_log_file.close()
                    ui_log("proxy 로그 파일 핸들 닫음")
                except Exception as e:
                    ui_log(f"proxy 로그 파일 닫기 실패: {e}")
            self.proxy_log_file = None
            self.proxy_proc = None
        except Exception as e:
            ui_log(f"proxy_proc 정리 오류: {e}")



        # 2) mitmdump 종료 + 최대 5초 확인
        try:
            self.kill_mitmdump_process()
            t0 = time.time()
            while self._is_mitmdump_running() and (time.time() - t0) < 5:
                time.sleep(0.5)
            ui_log("mitmdump 종료 확인" if not self._is_mitmdump_running()
                   else "경고: mitmdump 여전히 실행중")
        except Exception as e:
            ui_log(f"mitmdump 정리 오류: {e}")


        # 1) 프록시 해제 (HKCU + WinHTTP)
        try:
            self.unset_windows_gui_proxy()
        except Exception as e:
            ui_log(f"프록시 해제 중 예외: {e}")

        # 2) 인증서 제거 (certutil로 루트스토어에서 제거) 및 .mitmproxy 폴더 삭제
        try:
            # certutil로 루트 스토어에서 'mitmproxy' common name으로 된 항목 삭제 시도
            # certutil 반환값을 체크하여 실패 시 로그 남김
            result = subprocess.call(["certutil", "-delstore", "Root", "mitmproxy"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result == 0:
                ui_log("인증서 루트스토어에서 삭제됨 (certutil 반환 0).")
            else:
                ui_log(f"certutil -delstore 반환값: {result} (삭제 안 됐거나 항목 없음).")

            # 폴더 제거는 shutil.rmtree 권장(쉘 호출 회피, 예외처리 가능)
            user_profile = os.environ.get("USERPROFILE", "")
            mitm_folder = os.path.join(user_profile, ".mitmproxy")
            if os.path.exists(mitm_folder):
                try:
                    # 재시도 루프: 프로세스가 파일을 점유할 경우 삭제 실패할 수 있으므로 소량 재시도
                    for attempt in range(3):
                        try:
                            shutil.rmtree(mitm_folder)
                            ui_log(f".mitmproxy 폴더 삭제됨: {mitm_folder}")
                            break
                        except Exception as e_rm:
                            ui_log(f".mitmproxy 삭제 실패(재시도 {attempt+1}): {e_rm}")
                            time.sleep(0.5)
                    else:
                        ui_log(f".mitmproxy 폴더를 삭제하지 못했습니다: {mitm_folder} (수동 확인 필요)")
                except Exception as e:
                    ui_log(f".mitmproxy 삭제 중 예외: {e}")
            else:
                ui_log(".mitmproxy 폴더 없음(삭제 불필요)")

            ui_log("인증서 제거 작업 완료(루트스토어 및 로컬 폴더).")
        except Exception as e:
            ui_log(f"인증서 제거 전체 실패: {e}")
    # endregion


    # region : [버튼 이벤트] 중지 버튼 클릭시 이벤트
    def stop_action(self):
        ui_log(f"🧑‍💻 유저 화면 중지 버튼 클릭")
        """중지(프록시/인증서 정리). 창은 닫지 않음."""
        if not self.is_running:
            return
        self._do_cleanup()  # 실제 정리 로직

        # 상태 전환: 중지됨
        self.is_running = False
        # 중지(대기) 아이콘
        self.set_tray_icon("assets/pandop_off.ico")
        self.store_button.show()
        self.store_button.setEnabled(True)

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
    # endregion


    # region : 트레이 '종료'에서 호출
    def quit_app(self):
        """트레이 '종료'에서 호출: 동작 중이면 정리 후 앱 종료"""
        ui_log(f"🧑‍💻 유저 트레이 종료 버튼 클릭")
        if self.is_running:
            self._do_cleanup()
            self.is_running = False
        # 앱 완전 종료
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().quit()
    # endregion
