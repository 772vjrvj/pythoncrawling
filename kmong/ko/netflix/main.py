import requests
from bs4 import BeautifulSoup

# Netflix URL
url = "https://www.netflix.com/watch/80022580"

# 요청 헤더 (쿠키는 제외)
headers = {
    "authority": "www.netflix.com",
    "method": "GET",
    "path": "/kr/title/80018294",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": "Windows",
    "sec-ch-ua-platform-version": "10.0.0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

# HTTP GET 요청
response = requests.get(url, headers=headers)

# 응답 확인
if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")

    # 지정된 클래스의 텍스트 추출
    elements = soup.find("span", class_="default-ltr-cache-3z6sz6 euy28770")

    for element in elements:
        print(element.get_text(strip=True))
else:
    print(f"Failed to fetch the page. Status code: {response.status_code}")
