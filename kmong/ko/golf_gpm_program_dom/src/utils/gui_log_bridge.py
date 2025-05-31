from PyQt5.QtCore import QObject, pyqtSignal

class GuiLogBridge(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def connect_to(self, append_func):
        print("log_signal 연결됨")  # 디버깅용
        self.log_signal.connect(append_func)

    def write(self, msg):
        self.log_signal.emit(msg)

# 전역 인스턴스
log_bridge = GuiLogBridge()
