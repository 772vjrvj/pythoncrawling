# launcher_qt.py
# -*- coding: utf-8 -*-
"""
PandoP Launcher (PyQt5)
- GUI로 PandoP 감시 시작/종료 (종료는 런처만 종료, PandoP는 그대로 둠)
- 실행 파일 기준 경로에서 win-unpacked\PandoP.exe 찾음
"""

import sys
import time
import threading
import subprocess
from pathlib import Path

import psutil
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import QTimer, Qt

# =========================
# 설정
# =========================
CHECK_INTERVAL = 10  # 초


# =========================
# 경로 유틸
# =========================
def get_base_dir():
    """
    런처 기준 폴더 반환
    - PyInstaller exe: sys.executable 위치
    - .py 실행: 이 파일 위치
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_target_path():
    """
    win-unpacked/PandoP.exe 경로 계산
    """
    base = get_base_dir()
    return base / "win-unpacked" / "PandoP.exe"


# 전역 상태
launcher_thread = None
launcher_stop_flag = False
launcher_running = False


# =========================
# PandoP 제어 함수
# =========================
def is_pandop_alive(target_path: Path) -> bool:
    if not target_path.exists():
        return False

    try:
        target_real = str(target_path.resolve())
    except Exception:
        target_real = str(target_path)

    for proc in psutil.process_iter(["exe", "cmdline"]):
        try:
            exe = proc.info.get("exe") or ""
            if exe:
                if str(Path(exe).resolve()) == target_real:
                    return True
            else:
                cmd = proc.info.get("cmdline") or []
                if cmd and Path(cmd[0]).exists():
                    if str(Path(cmd[0]).resolve()) == target_real:
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False


def start_pandop(target_path: Path):
    if not target_path.exists():
        raise FileNotFoundError(f"PandoP.exe not found: {target_path}")
    subprocess.Popen([str(target_path)], cwd=str(target_path.parent))


# =========================
# 런처 루프 (백그라운드)
# =========================
def launcher_loop(status_label: QLabel, target_path: Path):
    global launcher_stop_flag

    while not launcher_stop_flag:
        try:
            if not target_path.exists():
                status_label.setText(f"❌ PandoP.exe not found:\n{target_path}")
                # 경로가 잘못되었으면 더 안 돌고 종료
                return

            if not is_pandop_alive(target_path):
                status_label.setText("PandoP not running. Starting...")
                try:
                    start_pandop(target_path)
                    time.sleep(3)
                    if is_pandop_alive(target_path):
                        status_label.setText("🟢 PandoP started.")
                    else:
                        status_label.setText("⚠️ Failed to detect PandoP. Will retry.")
                except Exception as e:
                    status_label.setText(f"⚠️ Start error: {e}")
            else:
                status_label.setText("🟢 PandoP is running.")

            # interval 동안 stop_flag 체크하며 대기
            for _ in range(CHECK_INTERVAL):
                if launcher_stop_flag:
                    return
                time.sleep(1)

        except Exception as e:
            status_label.setText(f"⚠️ Loop error: {e}")
            time.sleep(5)


# =========================
# GUI
# =========================
class LauncherUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PandoP Launcher")
        self.resize(380, 160)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)

        self.btn_start = QPushButton("시작 (런처 감시 시작)")
        self.btn_stop = QPushButton("종료 (런처만 종료)")
        self.btn_stop.hide()

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.btn_start)
        self.layout.addWidget(self.btn_stop)

        self.btn_start.clicked.connect(self.start_launcher)
        self.btn_stop.clicked.connect(self.stop_launcher)

        # 초기 상태 표시
        self.target_path = get_target_path()
        if self.target_path.exists():
            self.status_label.setText(
                f"대기 중\nTarget:\n{self.target_path}"
            )
        else:
            self.status_label.setText(
                f"❌ PandoP.exe not found.\n"
                f"기대 위치:\n{self.target_path}\n"
                f"※ launcher_qt.exe를 PandoP_V_0.19.5_prd 폴더에 두고 사용하세요."
            )

        # 2초마다 PandoP 상태 갱신 (런처 작동 여부와 무관)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2000)

    def refresh_status(self):
        # 런처가 돌고 있을 때는 launcher_loop에서 상태_label을 갱신하므로
        # 여기서는 런처가 꺼져 있을 때만 PandoP 상태를 대략 보여준다.
        global launcher_running
        if launcher_running:
            return

        if not self.target_path.exists():
            return

        if is_pandop_alive(self.target_path):
            self.status_label.setText(
                f"🟢 PandoP is running.\nTarget:\n{self.target_path}"
            )
        else:
            self.status_label.setText(
                f"🔴 PandoP not running.\nTarget:\n{self.target_path}"
            )

    def start_launcher(self):
        global launcher_thread, launcher_stop_flag, launcher_running

        if launcher_running:
            return

        if not self.target_path.exists():
            self.status_label.setText(
                f"❌ PandoP.exe not found.\n"
                f"위치 확인:\n{self.target_path}"
            )
            return

        launcher_stop_flag = False
        launcher_thread = threading.Thread(
            target=launcher_loop,
            args=(self.status_label, self.target_path),
            daemon=True,
        )
        launcher_thread.start()
        launcher_running = True

        self.btn_start.hide()
        self.btn_stop.show()
        self.status_label.setText(
            f"⏳ Launcher running...\nTarget:\n{self.target_path}"
        )

    def stop_launcher(self):
        global launcher_stop_flag, launcher_running

        launcher_stop_flag = True
        launcher_running = False

        self.btn_stop.hide()
        self.btn_start.show()
        self.status_label.setText(
            f"🛑 Launcher stopped.\nPandoP process is NOT killed."
        )

    def closeEvent(self, event):
        # 창 닫을 때도 런처 깔끔히 중지
        self.stop_launcher()
        event.accept()


# =========================
# 엔트리 포인트
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = LauncherUI()
    ui.show()
    sys.exit(app.exec_())
