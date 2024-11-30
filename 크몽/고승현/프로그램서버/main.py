import requests
import time
import threading

URL = "http://vjrvj.cafe24.com"
# URL = "http://localhost"

def login_to_server(username, password, session):
    url = f"{URL}/auth/login"
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
        response = session.post(url, json=payload, headers=headers)  # 헤더 추가

        # 요청이 성공했는지 확인
        if response.status_code == 200:
            print("Login successful")
            print("Response data:", response.json())

            # 세션 관리로 쿠키는 자동 처리
            print("Cookies after login:", session.cookies)
            print("Cookies:", session.cookies.get_dict())
            return True
        else:
            print("Login failed with status code:", response.status_code)
            print("Error message:", response.text)
            return False
    except Exception as e:
        print("An error occurred during login:", e)
        return False

def fetch_user_data(session):
    url = f"{URL}/user/select-all"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # 서버에 GET 요청을 보내면서 쿠키는 session 객체가 자동으로 관리
        response = session.get(url, headers=headers)  # 헤더 추가
        print("Request headers:", response.request.headers)

        if response.status_code == 200:
            print("User data fetched successfully:")
            print("Response data:", response.json())
        else:
            print("Failed to fetch user data with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred while fetching user data:", e)

# 추가된 로그아웃 함수
def logout_from_server(session):
    url = f"{URL}/auth/logout"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # 서버에 POST 요청을 보내서 로그아웃 시도
        response = session.post(url, headers=headers)

        if response.status_code == 200:
            print("Logout successful")
            print("Response data:", response.text)
        else:
            print("Logout failed with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred during logout:", e)


def check_session(session):
    url = f"{URL}/session/check-me"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # /check-me 엔드포인트를 호출하여 세션 상태 확인
        response = session.get(url, headers=headers)
        print("Request headers for check-me:", response.request.headers)

        if response.status_code == 200:
            print("Session check successful:", response.text)
            # fail이면 실패
        else:
            print("Session check failed with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred while checking session:", e)

# 추가된 비밀번호 변경 함수
def change_password(session, username, current_password, new_password):
    url = f"{URL}/auth/change-password"
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
        # PUT 요청을 사용하여 비밀번호 변경
        response = session.put(url, params=payload, headers=headers)

        if response.status_code == 200:
            print("Password changed successfully")
            print("Response data:", response.text)
        else:
            print("Failed to change password with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred while changing password:", e)


def main():
    username = "test"
    password = "2222"

    # 세션 생성
    session = requests.Session()

    login_to_server(username, password, session)

    # 로그인 시도
    check_session(session)

    logout_from_server(session)

    check_session(session)

    login_to_server(username, password, session)

    check_session(session)

    change_password(session, username, password, "2222")

    check_session(session)

    login_to_server(username, password, session)

    input("종료하려면 아무 키나 누르세요...")  # 프로그램 종료 대기



    check_session(session)
    input("종료하려면 아무 키나 누르세요...")  # 프로그램 종료 대기


if __name__ == "__main__":
    main()
