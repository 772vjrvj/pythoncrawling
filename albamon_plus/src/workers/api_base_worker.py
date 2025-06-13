from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal

class QThreadABCMeta(type(QThread), ABCMeta):
    pass

class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    msg_signal = pyqtSignal(str, str, object)
    show_countdown_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            if self.init():
                self.log_signal_func("초기화 성공")
            else:
                self.log_signal_func("초기화 실패")

            if self.main():
                self.log_signal_func("메인 성공")
            else:
                self.log_signal_func("메인 실패")

            self.destroy()
            self.log_signal_func("종료 완료")

        except Exception as e:
            self.log_signal_func(f"❌ 예외 발생: {e}")

    def log_signal_func(self, msg):
        self.log_signal.emit(msg)

    def progress_signal_func(self, before, current):
        self.progress_signal.emit(before, current)

    def progress_end_signal_func(self):
        self.progress_end_signal.emit()

    def msg_signal_func(self, content, type_name, obj):
        self.msg_signal.emit(content, type_name, obj)

    def show_countdown_signal_func(self, sec):
        self.show_countdown_signal.emit(sec)

    @abstractmethod
    def init(self) -> bool:
        pass

    @abstractmethod
    def main(self) -> bool:
        pass

    @abstractmethod
    def destroy(self):
        pass
