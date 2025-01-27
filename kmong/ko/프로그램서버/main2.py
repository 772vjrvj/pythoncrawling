import requests

def login_to_server(username, password):
    url = "http://localhost:80/api/login"
    payload = {
        "id": username,  # 사용자 ID 필드
        "password": password
    }

    try:
        # JSON 형식으로 서버에 POST 요청으로 로그인 시도
        response = requests.post(url, json=payload)

        # 요청이 성공했는지 확인
        if response.status_code == 200:
            print("Login successful")
            print("Response data:", response.json())

            # 쿠키 정보 추출
            cookies = response.cookies
            print("Cookies:")
            for cookie in cookies:
                print(f" - {cookie.name}: {cookie.value}")

            return cookies  # 쿠키 반환 (추후 요청에 사용 가능)
        else:
            print("Login failed with status code:", response.status_code)
            print("Error message:", response.text)
            return None
    except Exception as e:
        print("An error occurred during login:", e)
        return None

def fetch_active_sessions(cookies):
    url = "http://localhost:80/api/active-sessions"

    try:
        # 서버에 GET 요청을 보내면서 쿠키를 함께 전송
        response = requests.get(url, cookies=cookies)

        if response.status_code == 200:
            print("Active sessions fetched successfully:")
            print("Response data:", response.json())
        else:
            print("Failed to fetch active sessions with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred while fetching active sessions:", e)

def main():
    username = "admin"
    password = "1234"

    # 로그인 시도 및 쿠키 반환
    cookies = login_to_server(username, password)

    if cookies:
        print("Login cookies:", cookies)

        # 활성 세션 확인
        fetch_active_sessions(cookies)

        # 아무 키나 입력할 때까지 대기
        input("아무 키나 입력하세요...")
    else:
        print("No cookies returned, login may have failed.")

    input("종료하려면 아무 키나 누르세요...")  # 프로그램 종료 대기

if __name__ == "__main__":
    main()
