import ssl

ssl._create_default_https_context = ssl._create_unverified_context
from src.workers.api_base_worker import BaseApiWorker


class ApiCoupangSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.base_login_url = "https://login.coupang.com/login/login.pang"
        self.base_main_url = "https://www.coupang.com"

        self.com_list = []
        self.main_model = None
        self.product_info_list = []

        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.sess = None
        self.running = True
        self.driver = None
        self.base_url = None
        self.before_pro_value = 0


    def init(self):
        self.log_signal_func("init 대기중")

    def main(self):
        self.log_signal_func("main 대기중")

    def destroy(self):
        self.log_signal_func("main 대기중")

