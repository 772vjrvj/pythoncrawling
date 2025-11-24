import requests
from bs4 import BeautifulSoup

url = "https://kopd.kipo.go.kr:8888/family.do"

# === 신규 === 요청헤더
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=sCRH3C8kgW78V3qyajTXnPkb1OiesQwkbveYQf0Pex4uvA8HtHor3C7fkwYDPytr.opdcws1_servlet_engine3; searchHistory=2025-11-24%01*13*00^KR^original%#application&^1020040090349^$2025-11-24%01*10*25^KR^original%#application&^1020040090349^$2025-11-24%01*10*08^KR^original%#application&^1020040090349^$2025-11-24%01*09*44^KR^original%#application&^1020040090349^$2025-11-24%01*09*30^KR^original%#application&^1020040090349^",
    "origin": "https://kopd.kipo.go.kr:8888",
    "referer": "https://kopd.kipo.go.kr:8888/index.do",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

# === 신규 === payload
payload = {
    "numberType1": "original",
    "ori_country": "KR",
    "ori_numberType": "U1301",
    "ori_number": "1020040090349",
    "docdb_numberType": "U1301",
    "docdb_number": "KR.20040090349.A"
}

# === 신규 === 요청
resp = requests.post(url, headers=headers, data=payload, timeout=20)

if resp.status_code != 200:
    print("요청 실패:", resp.status_code)
    exit()

soup = BeautifulSoup(resp.text, "html.parser")

# familyTable 찾기
table = soup.find("table", id="familyTable")

if not table:
    print("familyTable 을 찾지 못함")
    exit()

tbody = table.find("tbody")
rows = tbody.find_all("tr") if tbody else []

print("familyTable → tbody → tr 개수:", len(rows))
