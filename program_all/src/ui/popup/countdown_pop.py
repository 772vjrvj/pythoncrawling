from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt

class CountdownPop(QDialog):
    def __init__(self, seconds):
        super().__init__()
        self.remaining = seconds
        self.setWindowTitle("대기 중...")
        self.setFixedSize(300, 100)

        self.label = QLabel(f"남은 시간: {self.remaining}초", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 1초마다 업데이트
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def update_countdown(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.accept()  # 팝업 종료
        else:
            self.label.setText(f"남은 시간: {self.remaining}초")
