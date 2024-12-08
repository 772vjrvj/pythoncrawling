from PyQt5.QtCore import QThread, pyqtSignal

class ProgressThread(QThread):
    # 진행 상태 변경 시 UI 업데이트를 위한 신호 정의
    progress_signal = pyqtSignal(int)

    def __init__(self, start_value, end_value):
        super().__init__()
        self.start_value = start_value
        self.end_value = end_value

    def run(self):
        # 20초 동안 진행
        diff_value = self.end_value - self.start_value  # 진행할 단계 수
        div_value = diff_value / 400  # 각 단계에 걸리는 시간 (초)

        inter_time = 20
        parts = 20
        millsecond = int(1000 / parts)  # 100

        for i in range(1, (parts * inter_time) + 1):
            pro_value = int(self.start_value + (div_value * i))

            # 진행 상태를 업데이트하는 신호를 보냄
            self.progress_signal.emit(pro_value)

            # 단계 간 시간 간격 (밀리초로 변환)
            QThread.msleep(millsecond)  # 각 단계마다 0.25초 대기