class AppManager:
    def __init__(self):
        self.login_window = None
        self.select_window = None
        self.main_window = None

    def go_to_login(self):
        if not self.login_window:
            from src.ui.login_window import LoginWindow
            self.login_window = LoginWindow(self)
        self.login_window.show()

    def go_to_select(self):
        if not self.select_window:
            from src.ui.select_window import SelectWindow
            from src.utils.config import SITE_LIST

            self.select_window = SelectWindow(self, SITE_LIST)
        self.select_window.show()

    def go_to_main(self):
        if not self.main_window:
            from src.ui.main_window import MainWindow
            self.main_window = MainWindow(self)
        self.main_window.init_reset()
        self.main_window.show()

