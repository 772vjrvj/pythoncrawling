from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal

class QThreadABCMeta(type(QThread), ABCMeta):
    pass

class BaseApiWorker(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    msg_signal = pyqtSignal(str, str, object)
    show_countdown_signal = pyqtSignal(int)


    def __init__(self):
        super().__init__()
        self.setting_detail = None
        self.user = None
        self.excel_data_list = None
        self.region = None
        self.columns = None
        self.sites = None
        self.setting = None
        self.running = True  # 실행 상태 플래그 추가


    def run(self):
        try:
            if not self.init():
                self.log_signal_func("초기화 실패 → 종료")
                self.destroy()
                return

            self.log_signal_func("초기화 성공")

            if not self.main():
                self.log_signal_func("메인 실패")
            else:
                self.log_signal_func("메인 성공")

            self.destroy()
            self.log_signal_func("종료 완료")

        except Exception as e:
            self.log_signal_func("❌ 예외 발생: " + str(e))
            self.destroy()


    def log_signal_func(self, msg):
        self.log_signal.emit(msg)


    def progress_signal_func(self, before, current):
        self.progress_signal.emit(before, current)


    def progress_end_signal_func(self):
        self.progress_end_signal.emit()


    def msg_signal_func(self, content, type_name, obj):
        self.msg_signal.emit(content, type_name, obj)


    def show_countdown_signal_func(self, sec):
        self.show_countdown_signal.emit(sec)


    def get_setting_value(self, setting_list, code_name):
        for item in setting_list:
            if item.get("code") == code_name:
                return item.get("value")
        return None  # 또는 기본값 0 등


    def set_setting(self, setting_list):
        self.setting = setting_list
    
    def set_setting_detail(self, setting_detail):
        self.setting_detail = setting_detail


    def set_excel_data_list(self, excel_data_list):
        self.excel_data_list = excel_data_list


    def set_user(self, user):
        self.user = user


    def set_columns(self, columns):
        self.columns = []
        if columns:
            self.columns = [col["value"] for col in columns if col.get("checked", False)]


    def set_sites(self, sites):
        self.sites = []
        if sites:
            self.sites = [col["value"] for col in sites if col.get("checked", False)]


    def set_region(self, region):
        self.region = region


    @abstractmethod
    def init(self) -> bool:
        pass

    @abstractmethod
    def main(self) -> bool:
        pass

    @abstractmethod
    def destroy(self):
        pass
