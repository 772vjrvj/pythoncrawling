from PyQt5.QtCore import QThread, pyqtSignal
import queue


class ProgressWorker(QThread):
    # 진행 상태 변경 시 UI 업데이트를 위한 신호 정의
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)

    def __init__(self, task_queue) -> None:
        super().__init__()
        self.task_queue = task_queue  # 작업 대기열
        self.running = True  # 실행 상태 플래그

    def run(self) -> None:
        while self.running:
            try:
                # 큐에서 작업 가져오기 (1초 대기)
                task = self.task_queue.get(timeout=1)
                if task is None:  # 종료 신호 처리
                    break

                # 20초 동안 진행
                start_value, end_value = task
                diff_value = end_value - start_value  # 진행할 단계 수
                inter_time = 40  # 1초를 40조각으로 나눔
                parts = 1

                div_value = diff_value / (parts * inter_time)
                millsecond = int(1000 / inter_time)

                for i in range(1, (parts * inter_time) + 1):
                    if not self.running:
                        break

                    pro_value = int(start_value + (div_value * i))
                    self.progress_signal.emit(pro_value)
                    QThread.msleep(millsecond)

            except queue.Empty:
                if not self.running:
                    break

    def stop(self) -> None:
        """스레드 실행 중단"""
        self.running = False
        self.task_queue.put(None)
