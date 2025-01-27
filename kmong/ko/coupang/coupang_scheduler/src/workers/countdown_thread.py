from datetime import datetime, timedelta

from PyQt5.QtCore import QThread, pyqtSignal


class CountdownThread(QThread):
    time_updated = pyqtSignal(str)  # 남은 시간을 갱신하기 위한 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True  # 스레드 실행 상태

    def run(self):
        """다음날 0시와 현재 시간의 차이를 계산하고 갱신"""
        while self.running:
            now = datetime.now()
            target_time = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            remaining_time = target_time - now

            # 남은 시간을 시/분/초로 변환
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time = f"{hours:02d}시간 {minutes:02d}분 {seconds:02d}초"

            # 시간 갱신
            self.time_updated.emit(formatted_time)

            # 1초 대기
            self.msleep(1000)  # QThread에 적합한 sleep(1000ms)