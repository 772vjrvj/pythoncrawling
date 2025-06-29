import requests
from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.config import server_url

class LoginWorker(QThread):
    login_success = pyqtSignal(object)
    login_failed = pyqtSignal(str)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        session = requests.Session()
        ok, msg, cookies = self._login(self.username, self.password, session)

        if ok:
            self.login_success.emit(cookies)
        else:
            self.login_failed.emit(msg)

    def _login(self, username, password, session):
        url = f"{server_url}/auth/login"
        payload = {"username": username, "password": password}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            res = session.post(url, json=payload, headers=headers)

            if res.status_code == 200:
                return True, "로그인 성공", session.cookies.get_dict()
            if res.status_code == 401:
                return False, "아이디 또는 비밀번호가 잘못되었습니다.", None
            return False, f"서버 오류: {res.status_code}", None

        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {e}", None
        except Exception as e:
            return False, f"알 수 없는 오류: {e}", None
