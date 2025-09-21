# main.py
import sys
from typing import Optional

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSharedMemory, Qt
# === 기존 ===
from src.app_manager import AppManager
from src.core.global_state import GlobalState


# === 신규: 단일 인스턴스 락 구현 ===
class SingleInstance:
    """
    QSharedMemory 기반 단일 인스턴스 락.
    - 같은 key로 이미 실행 중이면 attach()가 성공 → 중복 실행
    - 아니면 create()로 세마포어 역할의 1바이트 메모리를 생성
    """
    def __init__(self, key: str = "pando_single_instance"):
        self.key = key
        self.shared = QSharedMemory(self.key)
        self._is_owner = False

    def already_running(self) -> bool:
        # 다른 인스턴스가 먼저 띄워둔 공유메모리에 붙을 수 있으면 이미 실행 중
        if self.shared.attach():
            return True
        # 아니면 지금 인스턴스가 주인이 되도록 1바이트 메모리 생성
        if self.shared.create(1):
            self._is_owner = True
            return False
        # 예외적으로 create 실패 시에도 중복으로 간주
        return True

    def release(self):
        # 종료 시 정리 (첫 인스턴스만 의미 있음)
        if self._is_owner and self.shared.isAttached():
            self.shared.detach()


# === 신규: 중복 실행 경고창 ===
def show_already_running_alert(existing_app: Optional[QApplication] = None) -> None:
    """
    콘솔 출력 대신 경고 알림창을 최상단으로 띄움.
    - 기존 QApplication이 없으면 임시 생성 후 표시하고 정리
    """
    app_created = False
    app = existing_app or QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app_created = True

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("이미 실행 중")
    msg.setText("프로그램이 이미 실행 중입니다.\n기존 실행 중인 창을 확인해 주세요.")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setWindowFlag(Qt.WindowStaysOnTopHint, True)  # 항상 위로
    msg.exec_()

    if app_created:
        # 임시로 만든 QApplication이면 정리
        app.quit()


# === 신규: PyQt5/6 exec 호환 헬퍼 ===
def qt_exec(app: QApplication) -> int:
    """
    PyQt5는 exec_(), PyQt6는 exec() 이므로 둘 다 대응.
    """
    if hasattr(app, "exec_"):
        return app.exec_()  # PyQt5
    return app.exec()       # PyQt6


def main() -> None:
    # === 신규: 앱 생성 전에 단일 인스턴스 락 확인 (권장) ===
    lock = SingleInstance("pando_single_instance")
    if lock.already_running():
        # 아직 QApplication을 만들기 전이므로 임시 생성해서 경고창 표시
        show_already_running_alert(None)
        sys.exit(0)

    # === 기존: Qt 앱, 상태 초기화, AppManager 진입 ===
    app = QApplication(sys.argv)

    # (참조 유지: GC로 lock이 해제되지 않게 App 객체에 붙여둠)
    app._single_instance_lock = lock  # noqa: attach

    # 앱 종료 직전에 락 정리
    def _on_about_to_quit():
        try:
            lock.release()
        except Exception:
            pass
    app.aboutToQuit.connect(_on_about_to_quit)

    # === 기존 ===
    state = GlobalState()
    state.initialize()

    app_manager = AppManager()
    app_manager.go_to_login()

    sys.exit(qt_exec(app))


if __name__ == "__main__":
    main()
