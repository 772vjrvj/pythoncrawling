import requests
import json

# 요청할 URL
url = "https://www.musinsa.com/products/3228764"

# 요청 헤더
headers = {
    "authority": "www.musinsa.com",
    "method": "GET",
    "path": "/products/3228764",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

# 요청 보내기
response = requests.get(url, headers=headers)

# 응답 확인
if response.status_code == 200:
    try:
        # JSON 형식으로 변환
        json_data = response.json()

        # 예쁘게 출력
        print(json.dumps(json_data, indent=4, ensure_ascii=False))
    except ValueError:
        print("응답이 JSON 형식이 아닙니다. HTML을 출력합니다.")
        print(response.text)
else:
    print(f"페이지 요청 실패. 상태 코드: {response.status_code}")
