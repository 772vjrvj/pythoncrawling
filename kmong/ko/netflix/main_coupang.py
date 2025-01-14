import requests
import json

# c2b8c98b-386f-471e-bb52-40ab10cfb2d2
# 38bdc2d1-4c20-4018-bfe8-3a41d6b212fa

# url = "https://discover.coupangstreaming.com/v1/discover/titles/c2b8c98b-386f-471e-bb52-40ab10cfb2d2"
# url = "https://discover.coupangstreaming.com/v1/discover/titles/d79b5e63-0483-4e7b-8a32-5b8bb216e3fe"
url = "https://discover.coupangstreaming.com/v1/discover/titles/caee24fe-eab1-469a-ae28-cc51d2daf6d3"

headers = {
    # "authority": "discover.coupangstreaming.com",
    # "method": "GET",
    # "path": "/v1/discover/titles/c2b8c98b-386f-471e-bb52-40ab10cfb2d2?platform=WEBCLIENT&locale=ko&filterRestrictedContent=false&includeChannelContents=false",
    # "scheme": "https",
    # "accept": "application/json",
    # "accept-encoding": "gzip, deflate, br, zstd",
    # "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    # "content-type": "application/json",
    # "if-none-match": "\"190c-UzqgDWfhBxfb16uVnFvlF8Fm/kU\"",
    # "newrelic": "eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjI4NjcyMDYiLCJhcCI6IjE3Mjg4Njc4OTQiLCJpZCI6IjgxMDk3NmIyNDUxMzUzNjQiLCJ0ciI6ImM1YmVhMjczYzk0MGJkN2Y1MjkxNDQ0ZDNiM2YyMzMwIiwidGkiOjE3MzY3ODE4NDM0NjcsInRrIjoiOTEyOTQyIn19",
    # "origin": "https://www.coupangplay.com",
    # "priority": "u=1, i",
    # "referer": "https://www.coupangplay.com/",
    # "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    # "sec-ch-ua-mobile": "?0",
    # "sec-ch-ua-platform": "\"Windows\"",
    # "sec-fetch-dest": "empty",
    # "sec-fetch-mode": "cors",
    # "sec-fetch-site": "cross-site",
    # "traceparent": "00-c5bea273c940bd7f5291444d3b3f2330-810976b245135364-01",
    # "tracestate": "912942@nr=0-1-2867206-1728867894-810976b245135364----1736781843467",
    # "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # "x-app-version": "1.55.16",
    # "x-device-id": "web-e4a6061e-f171-48da-8d21-fa5c12060a7c",
    # "x-device-os-version": "131",
    # "x-membersrl": "19239754",
    # "x-nr-session-id": "fce7b68e-ed00-4ca3-b07a-bba78ae3992c",
    # "x-pcid": "17367808236724893956135",
    # "x-platform": "WEBCLIENT",
    # "x-profileid": "cba99ff1-c74b-4e58-b386-15522c86150c",
    # "x-profiletype": "standard"
}

# headers.pop("if-none-match", None)  # 헤더에서 If-None-Match 제거

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))
else:
    print(f"Request failed with status code {response.status_code}: {response.text}")