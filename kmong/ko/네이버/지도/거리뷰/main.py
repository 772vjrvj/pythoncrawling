import requests
import json

# 요청할 URL
url = 'https://map.naver.com/p/api/panorama/nearby/127.05382990000169/37.239594600001126/3'

# 헤더 설정
headers = {
    # 'authority': 'map.naver.com',
    # 'method': 'GET',
    # 'path': '/p/api/panorama/nearby/127.05382990000169/37.239594600001126/3',
    # 'scheme': 'https',
    # 'accept': 'application/json, text/plain, */*',
    # 'accept-encoding': 'gzip, deflate, br, zstd',
    # 'accept-language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4',
    # 'cache-control': 'no-cache',
    # 'cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; NACT=1; MM_PF=SEARCH; page_uid=iW0zbwqVOZwssnX/GfCssssstch-469857; _naver_usersession_=WKxpZguvNoNpGton2lZoEw==; ASID=da9384ec00000191d00facf700000072; BUC=l8H48pIZNnHx2-1elMrG9OLrxkoUQwCoj79n7akwZ3M=',
    # 'expires': 'Sat, 01 Jan 2000 00:00:00 GMT',
    # 'pragma': 'no-cache',
    # 'priority': 'u=1, i',
    'referer': 'https://map.naver.com/p/entry/place',
    # 'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    # 'sec-ch-ua-mobile': '?0',
    # 'sec-ch-ua-platform': '"Windows"',
    # 'sec-fetch-dest': 'empty',
    # 'sec-fetch-mode': 'cors',
    # 'sec-fetch-site': 'same-origin',
    # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

# GET 요청 보내기
response = requests.get(url, headers=headers)

# 요청이 성공했는지 확인
if response.status_code == 200:
    # JSON 데이터를 파싱하고 예쁘게 출력
    data = response.json()
    pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
    print(pretty_json)
else:
    print(f"Error: {response.status_code}")
