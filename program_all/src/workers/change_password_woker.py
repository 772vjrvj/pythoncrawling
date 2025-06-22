import requests
from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.config import server_url

class ChangePasswordWorker(QThread):
    password_change_success = pyqtSignal()
    password_change_failed = pyqtSignal(str)

    def __init__(self, session, username, current_pw, new_pw):
        super().__init__()
        self.session = session
        self.username = username
        self.current_pw = current_pw
        self.new_pw = new_pw

    def run(self):
        ok, msg = self._change_password()
        if ok:
            self.password_change_success.emit()
        else:
            self.password_change_failed.emit(msg)

    def _change_password(self):
        url = f"{server_url}/auth/change-password"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "id": self.username,
            "currentPassword": self.current_pw,
            "newPassword": self.new_pw
        }

        try:
            res = self.session.put(url, params=payload, headers=headers)
            if res.status_code == 200:
                return True, "비밀번호 변경 성공"
            if res.status_code == 400:
                return False, "현재 비밀번호가 올바르지 않습니다."
            if res.status_code == 403:
                return False, "권한이 없습니다."
            return False, f"서버 오류: {res.status_code}"

        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {e}"
        except Exception as e:
            return False, f"예상치 못한 오류: {e}"
