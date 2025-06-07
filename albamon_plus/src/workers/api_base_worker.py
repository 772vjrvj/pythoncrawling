from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal


# QThread와 ABCMeta 메타클래스 병합
class QThreadABCMeta(type(QThread), ABCMeta):
    pass


# 추상 기반 QThread 워커 클래스
class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    msg_signal = pyqtSignal(str, str, object)
    show_countdown_signal = pyqtSignal(int)  # UI에 딜레이 요청

    def __init__(self):
        QThread.__init__(self)  # 명시적 호출 (PyQt 관행)


    def run(self):
        try:
            # 초기화
            init_rs = self.init()
            if init_rs is not False:
                self.log_signal_func('초기화 성공')
            else:
                self.log_signal_func('초기화 실패')

            # 메인
            main_rs = self.main()
            if main_rs is not False:
                self.log_signal_func('메인 성공')
            else:
                self.log_signal_func('메인 실패')

            # 종료 (반환값 기대 안함)
            self.destroy()
            self.log_signal_func('종료 완료')

        except Exception as e:
            self.log_signal_func(f"❌ 워커 실행 중 예외 발생: {e}")


    def log_signal_func(self, msg: str):
        self.log_signal.emit(msg)


    def progress_signal_func(self, before_pro_value: float, pro_value: float):
        self.progress_signal.emit(before_pro_value, pro_value)


    def progress_end_signal_func(self):
        self.progress_end_signal.emit()


    def msg_signal_func(self, content: str, type_name: str, obj: object):
        self.msg_signal.emit(content, type_name, obj)


    def show_countdown_signal_func(self, second: int):
        self.show_countdown_signal.emit(second)


    # 자식 클래스에서 반드시 구현해야 하는 메서드들
    @abstractmethod
    def init(self) -> bool:
        """작업 시작 전 초기화"""
        pass

    @abstractmethod
    def main(self) -> bool:
        """실제 작업 수행"""
        pass

    @abstractmethod
    def destroy(self):
        """정리 작업 (리턴값 불필요)"""
        pass
