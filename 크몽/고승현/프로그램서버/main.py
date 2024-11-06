import requests

def login_to_server(username, password):
    url = "http://localhost:80/auth/login"
    payload = {
        "username": username,
        "password": password
    }

    try:
        # JSON 형식으로 서버에 POST 요청으로 로그인 시도
        response = requests.post(url, json=payload)  # 'json'을 사용하여 JSON 데이터로 전송

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
        print("An error occurred:", e)
        return None

def fetch_user_data(cookies):
    url = "http://localhost:80/user/admin"

    try:
        # 서버에 GET 요청을 보내면서 쿠키를 함께 전송
        response = requests.get(url, cookies=cookies)  # 'cookies'를 사용하여 세션 쿠키 전송

        if response.status_code == 200:
            print("User data fetched successfully:")
            print("Response data:", response.json())
        else:
            print("Failed to fetch user data with status code:", response.status_code)
            print("Error message:", response.text)
    except Exception as e:
        print("An error occurred while fetching user data:", e)

def main():
    username = "admin"
    password = "1234"

    # 로그인 시도 및 쿠키 반환
    cookies = login_to_server(username, password)

    if cookies:
        print("Login cookies:", cookies)

        # 아무 키나 입력할 때까지 대기
        input("아무 키나 입력하세요...")

        # /user/admin으로 요청
        fetch_user_data(cookies)
    else:
        print("No cookies returned, login may have failed.")

    input("종료하려면 아무 키나 누르세요...")  # 프로그램 종료 대기

if __name__ == "__main__":
    main()
