import requests  # HTTP 요청 처리
from PyQt5.QtCore import QThread, pyqtSignal  # PyQt 쓰레드 및 시그널
from src.utils.config import SERVER_URL  # 서버 URL 및 설정 정보


# 비밀번호 변경 API 요청을 처리하는 스레드 클래스
class ChangePasswordThread(QThread):
    password_change_success = pyqtSignal()  # 비밀번호 변경 성공 시그널
    password_change_failed = pyqtSignal(str)  # 비밀번호 변경 실패 시그널 (에러 메시지 전달)

    def __init__(self, session, username, current_password, new_password):
        super().__init__()
        self.session = session
        self.username = username
        self.current_password = current_password
        self.new_password = new_password

    def run(self):
        result, message = self.change_password(
            self.session,
            self.username,
            self.current_password,
            self.new_password
        )

        if result:
            self.password_change_success.emit()  # 성공 시그널 발생
        else:
            self.password_change_failed.emit(message)  # 실패 시그널 발생

    # 비밀번호 변경 함수
    def change_password(self, session, username, current_password, new_password):
        url = f"{SERVER_URL}/auth/change-password"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "id": username,
            "currentPassword": current_password,
            "newPassword": new_password
        }

        try:
            # PUT 요청으로 비밀번호 변경 요청
            response = session.put(url, params=payload, headers=headers)

            if response.status_code == 200:
                return True, "비밀번호 변경 성공"
            elif response.status_code == 400:
                return False, "현재 비밀번호가 올바르지 않습니다."
            elif response.status_code == 403:
                return False, "권한이 없습니다."
            else:
                return False, f"서버 오류: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
