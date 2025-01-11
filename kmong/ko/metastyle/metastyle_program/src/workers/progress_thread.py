from PyQt5.QtCore import QThread, pyqtSignal

class ProgressThread(QThread):
    # 진행 상태 변경 시 UI 업데이트를 위한 신호 정의
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    def __init__(self, start_value, end_value):
        super().__init__()
        self.start_value = start_value
        self.end_value = end_value
        self.running = True  # 실행 상태 플래그 초기화

    def run(self):
        # 20초 동안 진행
        diff_value = self.end_value - self.start_value  # 진행할 단계 수
        inter_time = 40
        parts = 3  # 걸리는 시간

        div_value = diff_value / (parts * inter_time)  # 각 단계에 걸리는 시간 (초)
        millsecond = int(1000 / inter_time)  # 밀리초 간격

        for i in range(1, (parts * inter_time) + 1):
            # 실행 상태 확인
            if not self.running:
                break  # 실행 상태가 False이면 루프 중단

            pro_value = int(self.start_value + (div_value * i))

            # 진행 상태를 업데이트하는 신호를 보냄
            self.progress_signal.emit(pro_value)

            # 단계 간 시간 간격 (밀리초로 변환)
            QThread.msleep(millsecond)  # 각 단계마다 대기

    def stop(self):
        """스레드 실행 중단"""
        self.log_signal.emit("프로그래스 종료")
        self.running = False
