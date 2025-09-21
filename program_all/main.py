# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSharedMemory, Qt
from src.ui.main_window import MainWindow


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


def show_already_running_alert():
    """
    운영 환경에서 콘솔 출력 대신 알림창을 최상단으로 띄움.
    - 별도의 QApplication이 없으면 임시로 생성 후 사용
    """
    app_created = False
    app = QApplication.instance()
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

    # 임시로 만든 QApplication이면 정리
    if app_created:
        app.quit()


if __name__ == "__main__":
    lock = SingleInstance("pando_single_instance")

    if lock.already_running():
        show_already_running_alert()
        sys.exit(0)

    app = QApplication(sys.argv)

    # 첫 인스턴스 유지 중에만 의미가 있으므로 app과 수명 같이 함
    # (파이썬 GC로 lock이 사라지지 않도록 참조 유지)
    app._single_instance_lock = lock  # noqa: attach

    win = MainWindow()
    win.show()

    try:
        exit_code = app.exec_()
    finally:
        # 깔끔한 정리 (첫 인스턴스만 detach 의미 있음)
        lock.release()
    sys.exit(exit_code)
