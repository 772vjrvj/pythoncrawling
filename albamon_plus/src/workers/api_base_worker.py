from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal

# PyQt5 QThread와 ABCMeta의 메타클래스 병합
class QThreadABCMeta(type(QThread), ABCMeta):
    pass

# 병합된 메타클래스를 사용하는 추상 클래스 정의
class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    msg_signal = pyqtSignal(str, str, object)

    # 초기화
    def __init__(self):
        super().__init__()

    # 실행
    def run(self):
        # 시작
        self.init()

        # 메인
        self.main()

        # 끝
        self.destroy()


    def log_signal_func(self, msg):
        self.log_signal.emit(msg)
        # print(msg) # 테스트 일때만

    def progress_signal_func(self, before_pro_value, pro_value):
        self.progress_signal.emit(before_pro_value, pro_value)


    def progress_end_signal_func(self):
        self.progress_end_signal.emit()


    def msg_signal_func(self, content, type_name, obj):
        self.msg_signal.emit(content, type_name, obj)

    # 초기
    @abstractmethod
    def init(self):
        pass

    # 메인
    @abstractmethod
    def main(self):
        pass

    # 종료
    @abstractmethod
    def destroy(self):
        pass