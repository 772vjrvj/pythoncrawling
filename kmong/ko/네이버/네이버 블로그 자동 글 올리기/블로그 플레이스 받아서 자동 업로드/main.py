from src.ui.login_window import LoginWindow
from src.ui.login_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    # window = MainWindow()
    window.show()
    sys.exit(app.exec_())