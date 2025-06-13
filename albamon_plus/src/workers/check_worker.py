from PyQt5.QtCore import QThread, pyqtSignal
import requests

class CheckWorker(QThread):
    api_failure = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, cookies, server_url):
        super().__init__()
        self.cookies = cookies
        self.server_url = server_url
        self.running = True

    def run(self):
        url = f"{self.server_url}/session/check-me"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        while self.running:
            try:
                res = requests.get(url, headers=headers, cookies=self.cookies)
                if res.status_code != 200 or res.text == "fail":
                    self.api_failure.emit("세션 오류: 유효하지 않음")
                    break
            except Exception as e:
                self.api_failure.emit(f"네트워크 오류: {e}")
                break

            self.sleep(60)

    def stop(self):
        self.log_signal.emit("로그인 체크 종료")
        self.running = False
