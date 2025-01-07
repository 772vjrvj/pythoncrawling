from src.ui.login_window import LoginWindow
from PyQt5.QtWidgets import QApplication
import sys

# 메인함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())