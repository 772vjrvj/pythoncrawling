from PyQt5.QtWidgets import QApplication
from src.app_manager import AppManager
from src.utils.singleton import GlobalState

import sys

# 메인함수
if __name__ == "__main__":
    app = QApplication(sys.argv)

    state = GlobalState()
    state.initialize()

    app_manager = AppManager()
    app_manager.go_to_login()
    sys.exit(app.exec_())