from PyQt5.QtWidgets import QApplication
from src.app_manager import AppManager
from src.core.global_state import GlobalState

import sys


def main() -> None:
    app = QApplication(sys.argv)

    state = GlobalState()
    state.initialize()

    app_manager = AppManager()
    app_manager.go_to_login()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
