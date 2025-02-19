from PyQt5.QtCore import QThread, pyqtSignal
import queue


class ProgressThread(QThread):
    # 진행 상태 변경 시 UI 업데이트를 위한 신호 정의
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)

    def __init__(self, task_queue):
        super().__init__()
        self.task_queue = task_queue  # 작업 대기열
        self.running = True  # 실행 상태 플래그

    def run(self):

        while self.running:
            try:
                # 큐에서 작업 가져오기 (1초 대기)
                task = self.task_queue.get(timeout=1)
                if task is None:  # 종료 신호 처리
                    break

                # 20초 동안 진행
                start_value, end_value = task
                diff_value = end_value - start_value  # 진행할 단계 수
                inter_time = 40 # 1초를 40조각으로 잘라서 진행
                parts = 3  # 걸리는 시간

                div_value = diff_value / (parts * inter_time)  # 각 단계에 걸리는 시간 (초)
                millsecond = int(1000 / inter_time)  # 밀리초 간격

                for i in range(1, (parts * inter_time) + 1):
                    # 실행 상태 확인
                    if not self.running:
                        break  # 실행 상태가 False이면 루프 중단

                    pro_value = int(start_value + (div_value * i))

                    # 진행 상태를 업데이트하는 신호를 보냄
                    self.progress_signal.emit(pro_value)

                    # 단계 간 시간 간격 (밀리초로 변환)
                    QThread.msleep(millsecond)  # 각 단계마다 대기

            except queue.Empty:
                # 큐가 비어 있는 경우 대기 상태 유지
                if not self.running:
                    break

    def stop(self):
        """스레드 실행 중단"""
        self.running = False
        self.task_queue.put(None)  # 큐에 종료 신호 추가
