import requests
import time
import re

# 요청 헤더 설정
headers = {
    "authority": "api.kream.co.kr",
    "method": "GET",
    "scheme": "https",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://kream.co.kr",
    "referer": "https://kream.co.kr/my/selling?tab=finished",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "authorization": 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MDMxMDA1OCwianRpIjoiMTg3Zjk1YjgtY2M5Yy00ZWZkLWI3MGQtNTYwOGY2NDgwNTljIiwidHlwZSI6ImFjY2VzcyIsImlkZW50aXR5Ijo2MjQwNjc1LCJuYmYiOjE3NDAzMTAwNTgsImNzcmYiOiJmZTA4ZjUyMi0zYzVlLTQ5ZDAtOThiYy00ZmMwMjc1ZTJmZTMiLCJleHAiOjE3NDAzMTcyNTgsInVjIjp7InNhZmUiOnRydWV9LCJ1ZCI6Ii5lSnhGanN0T3d6QVVSSF9seXF0V3FoMF9FeWRaSVJZZ2xiSWhVcGVSRTktQzFiU08zRUI1aUg4bkVVaG9kbWRtTlBORl9FUXFJcmswbEVzcVZTTkVKWXRLV2FhTjVsS1NEZkg0Rm5wc3A0OFI1LWdWdTM4V19DLXBEMzFYS3NNOUxZVzNWTHZDMGxJYlQ3SFVvclM2ejVYTjUxckNVNXl3ZGQ2blpWVllKblRCaEpKTXFzVl92V0JxM1RPZWwxTzctQm1Hd1dXR2NWanR3OW5INndVZUd4Q2M4UnBta09zYTNuTzlocHR4SEhDUDNUWk1tVkVGVXptc3R2Zk43bUVEUXpnaTNHRl9qR3U0ZlVueGhKbFFpdkZGOE9RT0xvV19Ddm4tQWZtYVNzay5nOHNKNnF2ZnVQM0ZRYXNfTm5VcHBJLU1MNW8ifQ.Cj2huuqtjBFTzB7gpLkcwnG31r9YJWdYZnqP10lBPQg',
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-kream-api-version": "41",
    "x-kream-client-datetime": "20250223183955+0900",
    "x-kream-device-id": "web;fcb9350d-91d8-4a78-945d-e941984c6386",
    "x-kream-web-build-version": "6.7.4",
    "x-kream-web-request-secret": "kream-djscjsghdkd"
}

# URL 패턴 정규표현식 (숫자만 추출)
url_pattern = re.compile(r"https://kream\.co\.kr/my/selling/(\d+)")
extracted_ids = []

def fetch_data(cursor):
    # status=expired
    # status=canceled


    url = f"https://api.kream.co.kr/api/o/asks/?cursor={cursor}&tab=finished&status=expired&request_key=731e4f47-dab0-4219-b161-b221fafcc1d3"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            for item in data["items"]:
                if item.get("actions", []):
                    for action in item.get("actions", []):
                        if "value" in action and "https://kream.co.kr/my/selling/" in action["value"]:
                            match = url_pattern.search(action["value"])
                            if match:
                                print(match.group(1))
                                extracted_ids.append(match.group(1))  # 숫자 부분만 저장
            print(f"Cursor {cursor}: {extracted_ids}")
    else:
        print(f"Cursor {cursor}: 요청 실패 (HTTP {response.status_code})")

def main():
    for cursor in range(1, 20):  # 1부터 52까지 반복
        fetch_data(cursor)
        time.sleep(1)  # 1초 대기
    print(extracted_ids)

if __name__ == "__main__":
    main()
