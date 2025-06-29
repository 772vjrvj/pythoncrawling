# launcher_gui.py (선택)
import subprocess
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mitmproxy 후킹 실행기")
        layout = QVBoxLayout()

        btn_cert = QPushButton("① 인증서 설치")
        btn_cert.clicked.connect(lambda: subprocess.call(["install_cert.bat"], shell=True))

        btn_run = QPushButton("② 후킹 시작")
        btn_run.clicked.connect(lambda: subprocess.call(["run_mitmproxy.bat"], shell=True))

        layout.addWidget(btn_cert)
        layout.addWidget(btn_run)
        self.setLayout(layout)

app = QApplication([])
win = Launcher()
win.show()
app.exec_()
