import requests
import urllib.parse

def api_explorer():
    # URL 구성
    base_url = "http://openapi.seoul.go.kr:8088"
    key = "FPqnqSzu%2BN1m6BASDuPAmOGy%2BxbKHhPiOkpArFppBU%2B9ZzpO5sV9WKp5xMV%2FGxYhyVFk%2FJt8yttU%2BWaQJalL6A%3D%3D"  # 인증키 (sample 사용시 제한됩니다.)
    data_type = "json"  # 요청파일타입 (xml, xmlf, xls, json)
    service = "TbgisTrdarRelm"  # 서비스명 (대소문자 구분 필수)
    start_index = "1"  # 요청 시작 위치
    end_index = "5"  # 요청 종료 위치
    date = "20241"  # 서비스별 추가 요청 인자

    # 인코딩된 URL 생성
    url = f"{base_url}/{urllib.parse.quote(key)}/{urllib.parse.quote(data_type)}/{urllib.parse.quote(service)}/{urllib.parse.quote(start_index)}/{urllib.parse.quote(end_index)}/{urllib.parse.quote(date)}"

    # GET 요청
    # headers = {'Content-Type': 'application/json'}
    # response = requests.get(url, headers=headers)
    response = requests.get(url)

    # 응답 상태 코드 출력
    print("Response code:", response.status_code)

    # 응답 내용 출력
    if 200 <= response.status_code <= 300:
        print(response.text)
    else:
        print(f"Error occurred: {response.text}")

# 실행
api_explorer()
