import requests

# 로그인에 사용할 정보
login_url = "https://tyc.best/include/login_chk.asp"  # 로그인 처리 URL
dashboard_url = "https://tyc.best/dashboard/"  # 로그인 후 이동할 페이지 (테스트용)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 로그인 데이터
login_data = {
    "MEMB_ID": "kkckkc",  # 아이디
    "PASS2": "k@4358220"    # 비밀번호
}

# 세션 생성
with requests.Session() as session:
    # 로그인 요청
    response = session.post(login_url, data=login_data, headers=headers)

    # 로그인 요청 결과 확인
    if response.ok:
        print("로그인 요청 성공!")

        # 쿠키 출력
        print("로그인 후 쿠키:")
        for cookie in session.cookies:
            print(f"{cookie.name}: {cookie.value}")

        # 대시보드 페이지로 이동하여 테스트
        dashboard_response = session.get(dashboard_url)
        if dashboard_response.ok:
            print("대시보드 접근 성공!")
            print(dashboard_response.text)  # 페이지 내용 출력
        else:
            print("대시보드 접근 실패!")
    else:
        print("로그인 요청 실패!")
        print(response.status_code, response.text)
