import requests
from PyQt5.QtCore import QThread, pyqtSignal

from src.utils.config import server_url


# 로그인 API 요청을 처리하는 스레드 클래스
class LoginThread(QThread):
    login_success = pyqtSignal(object)  # 로그인 성공 시그널
    login_failed = pyqtSignal(str)  # 로그인 실패 시그널 (에러 메시지 전달)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        session = requests.Session()
        result, message, cookie = self.login_to_server(self.username, self.password, session)

        if result:
            self.login_success.emit(cookie)  # 로그인 성공 시그널 발생
        else:
            self.login_failed.emit(message)  # 로그인 실패 시그널 발생


    # 서버 로그인 함수 (네이버와 다른 서버 구분)
    def login_to_server(self, username, password, session):
        global global_server_cookies
        url = f"{server_url}/auth/login"
        payload = {
            "username": username,
            "password": password
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            # JSON 형식으로 서버에 POST 요청으로 로그인 시도
            response = session.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                # 세션 관리로 쿠키는 자동 처리
                cookies = session.cookies.get_dict()  # 쿠키 추출
                return True, "로그인 성공", cookies
            elif response.status_code == 401:
                return False, "아이디 또는 비밀번호가 잘못되었습니다.", None
            else:
                return False, f"서버 오류: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}", None