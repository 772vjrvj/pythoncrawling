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
        # "pando_single_instance"라는 이름표를 가진 공유 메모리 객체 생성
        # 이 key가 같으면 서로 같은 공간을 참조하게 됨
        self.key = key
        self.shared = QSharedMemory(self.key)
        self._is_owner = False  # 내가 첫 실행자인지 표시하는 플래그

    def already_running(self) -> bool:
        # 다른 인스턴스가 실행 중인지 확인하는 메소드

        # 1) attach(): 이미 실행된 인스턴스가 만든 메모리에 "붙기" 시도
        # 붙기가 성공하면 → 이미 실행 중이라는 뜻
        if self.shared.attach():
            return True

        # 2) create(1): 아직 실행된 게 없으면 새로 1바이트짜리 메모리를 만들기
        # 성공하면 내가 첫 실행자임
        if self.shared.create(1):
            self._is_owner = True
            return False

        # 3) 예외적으로 create도 실패한다면 중복 실행으로 간주
        return True

    def release(self):
        # 종료 시 정리 (첫 인스턴스만 의미 있음)
        # 내가 첫 실행자라면 detach() 해서 메모리 잠금을 해제
        if self._is_owner and self.shared.isAttached():
            self.shared.detach()


def show_already_running_alert():
    """
    운영 환경에서 콘솔 출력 대신 알림창을 최상단으로 띄움.
    - 별도의 QApplication이 없으면 임시로 생성 후 사용
    """
    # QMessageBox를 띄우려면 QApplication이 반드시 필요함
    app_created = False
    app = QApplication.instance()
    if app is None:  # 실행 중인 QApplication이 없으면 새로 하나 생성
        app = QApplication(sys.argv)
        app_created = True

    # "이미 실행 중입니다" 알림창 생성
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("이미 실행 중")
    msg.setText("프로그램이 이미 실행 중입니다.\n기존 실행 중인 창을 확인해 주세요.")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setWindowFlag(Qt.WindowStaysOnTopHint, True)  # 항상 위로 표시
    msg.exec_()

    # 내가 임시로 QApplication을 만든 경우 정리
    if app_created:
        app.quit()


if __name__ == "__main__":
    # 실행할 때 "단일 실행 잠금 장치"를 준비
    lock = SingleInstance("pando_single_instance")

    # 이미 실행 중이면 → 경고창 띄우고 프로그램 종료
    if lock.already_running():
        show_already_running_alert()
        sys.exit(0)

    # 첫 실행이라면 → QApplication 생성하고 본격 실행
    app = QApplication(sys.argv)

    # lock 객체를 app에 붙여서 프로그램이 끝날 때까지 메모리에 유지
    app._single_instance_lock = lock  # noqa: attach

    # 메인 윈도우 생성 및 표시
    win = MainWindow()
    win.show()

    try:
        # 앱 실행 (이벤트 루프 시작)
        exit_code = app.exec_()
    finally:
        # 프로그램이 종료될 때 메모리 잠금 해제
        lock.release()

    sys.exit(exit_code)
