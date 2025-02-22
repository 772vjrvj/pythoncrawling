import requests

# 요청 URL
url = "https://bff-general.albamon.com/v1/recruit/view"

# 요청 헤더
headers = {
    "authority": "bff-general.albamon.com",
    "method": "POST",
    "path": "/v1/recruit/view",
    "scheme": "https",
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "albamon-domain-type": "pc",
    "content-type": "application/json",
    "origin": "https://www.albamon.com",
    "priority": "u=1, i",
    "referer": "https://www.albamon.com/jobs/area?page=3&areas=I000&employmentTypes=FULL_TIME",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "cookie": "_gcl_aw=GCL.1739978839.CjwKCAiAn9a9BhBtEiwAbKg6frlpnpW2tBlBsqN9NMyWqBmjw0-q0bw2iATq_nb3onwpVfxHhg0n_BoCopkQAvD_BwE; _gcl_gs=2.1.k1$i1739978833$u185728505; _ga=GA1.1.1589651135.1739978839; ConditionId=1187621C-98D0-44C9-AE4E-D1D3869438EF; ab.storage.deviceId.7a5f1472-069a-4372-8631-2f711442ee40=%7B%22g%22%3A%22c3f5d6c8-3939-dca6-cfae-3a6ade1a2651%22%2C%22c%22%3A1739978837484%2C%22l%22%3A1740054277046%7D; AM_USER_UUID=b0949b94-81f4-40d0-9821-b06f97df5dfa; ab.storage.sessionId.7a5f1472-069a-4372-8631-2f711442ee40=%7B%22g%22%3A%22f25a704d-c968-fc6d-be97-810b47449261%22%2C%22e%22%3A1740056633118%2C%22c%22%3A1740054277045%2C%22l%22%3A1740054833118%7D; cto_bundle=zAJ2bl9vM3ZlZXNFRUNZTWV1NjAlMkZLVW5TVmFFM09lOWdkQk95SHJRMXQlMkYxeTNaalZ3MmtORTk0UjA3R21wT0lYMGFuVFI1emFpenJVQWNQbzA2SzIlMkJERHY2R1BMWSUyRlo0a0VwWkd0b0pGWkdXMEdKQ3dLcCUyRkgwTiUyRkRuS3RSeEtpd2JiRQ; _ga_538P897ZYY=GS1.1.1740054274.4.1.1740054837.51.0.0"
}

# 요청 본문 (Payload)
payload = {
    "clientIp": "",
    "naverInfoStat": "1",
    "optTotalStat": "2",
    "recruitNo": 107993031
}

# 요청 보내기
response = requests.post(url, headers=headers, json=payload)

# 응답 JSON 출력
try:
    print(response.json())
except requests.exceptions.JSONDecodeError:
    print("JSON 디코딩 오류 발생")
