import requests

# 요청 URL
url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=default_life&pool=cbox5&lang=ko&country=KR&objectId=news015%2C0005024972&pageSize=20&indexSize=10&listType=OBJECT&pageType=more&page=2&sort=FAVORITE"

# 요청 헤더
headers = {
    "authority": "apis.naver.com",
    "method": "GET",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "dnt": "1",
    "referer": "https://n.news.naver.com/mnews/article/comment/015/0005024972",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Avast Secure Browser";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "script",
    "sec-fetch-mode": "no-cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Avast/127.0.0.0"
}

# GET 요청
response = requests.get(url, headers=headers)

# 결과 출력
if response.status_code == 200:
    print("요청 성공!")
    print(response.text)
else:
    print(f"요청 실패: {response.status_code}")
