import requests
from bs4 import BeautifulSoup
import json

# 요청 헤더 설정 (쿠키는 제외)
def get_headers():
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "connection": "keep-alive",
        "host": "www.diningcode.com",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

# GET 요청 후 HTML 파싱 및 JSON 데이터 추출
def fetch_and_parse(url):
    headers = get_headers()
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # <script type="application/ld+json"> 찾기
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if script_tag:
            json_data = script_tag.string.strip()
            try:
                parsed_data = json.loads(json_data)
                print(json.dumps(parsed_data, indent=4, ensure_ascii=False))  # JSON 데이터를 보기 좋게 출력
            except json.JSONDecodeError as e:
                print(f"JSON 디코딩 오류: {e}")
        else:
            print("JSON 데이터를 포함하는 스크립트 태그를 찾을 수 없습니다.")
    else:
        print(f"요청 실패: 상태 코드 {response.status_code}")

# 실행 예시
if __name__ == "__main__":
    url = "https://www.diningcode.com/profile.php?rid=AIk0w7AXhi4A"
    fetch_and_parse(url)
