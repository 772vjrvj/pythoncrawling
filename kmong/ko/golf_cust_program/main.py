from PyQt5.QtWidgets import QApplication
from src.ui.login_window import LoginWindow
import sys

# 메인함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_ui = LoginWindow()
    main_ui.show()
    sys.exit(app.exec_())