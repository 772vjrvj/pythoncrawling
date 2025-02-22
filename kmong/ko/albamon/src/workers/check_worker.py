from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.config import server_url
import requests

class CheckWorker(QThread):
    api_failure = pyqtSignal(str)  # API 실패 시그널 (에러 메시지 전달)
    log_signal = pyqtSignal(str)

    def __init__(self, cookies, server_url):
        super().__init__()
        self.cookies = cookies  # 쿠키를 인자로 받음
        self.server_url = server_url  # 쿠키를 인자로 받음
        self.running = True

    def run(self):
        url = f"{server_url}/session/check-me"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        while self.running:
            try:
                response = requests.get(url, headers=headers, cookies=self.cookies)

                if response.text == "fail":
                    self.api_failure.emit("세션 오류: 상태가 유효하지 않음")
                    self.running = False

                if response.status_code != 200:
                    self.api_failure.emit("세션 오류: 상태가 유효하지 않음")
                    self.running = False

            except Exception as e:
                self.api_failure.emit(f"네트워크 오류: {str(e)}")
                self.running = False
            self.sleep(60)  # 1분 대기

    def stop(self):
        self.log_signal.emit("로그인 체크 종료")
        self.running = False

