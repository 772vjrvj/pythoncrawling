import requests
import json

# 요청 URL
url = "https://bff-general.albamon.com/recruit/search"

# 요청 헤더
headers = {
    "authority": "bff-general.albamon.com",
    "method": "POST",
    "path": "/recruit/search",
    "scheme": "https",
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "albamon-domain-type": "pc",
    "content-type": "application/json",
    "origin": "https://www.albamon.com",
    "priority": "u=1, i",
    "referer": "https://www.albamon.com/jobs/area?areas=I000&employmentTypes=FULL_TIME&page=2",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "cookie": "_ga=GA1.1.1589651135.1739978839; ConditionId=1187621C-98D0-44C9-AE4E-D1D3869438EF; ab.storage.deviceId.7a5f1472-069a-4372-8631-2f711442ee40=%7B%22g%22%3A%22c3f5d6c8-3939-dca6-cfae-3a6ade1a2651%22%2C%22c%22%3A1739978837484%2C%22l%22%3A1740054277046%7D; AM_USER_UUID=b0949b94-81f4-40d0-9821-b06f97df5dfa; _gcl_aw=GCL.1740055095.CjwKCAiAn9a9BhBtEiwAbKg6frlpnpW2tBlBsqN9NMyWqBmjw0-q0bw2iATq_nb3onwpVfxHhg0n_BoCopkQAvD_BwE; _gcl_gs=2.1.k1$i1740055089$u185728505; cto_bundle=6hxCPV9vM3ZlZXNFRUNZTWV1NjAlMkZLVW5TVmNVVEo3ZUUlMkYwcUZpdWRrWkl0U1ZjdExlR3FtVWRMVnV5VGlzcGtOakhleVRORUdNaXJETUc5bXZTU2lFdUF6YWRkSDgyWHAweGF2VUZpMUM5SjBqVENvcHQlMkJZaWFUNFkxUXNhdTltZUh0ZQ; _ga_538P897ZYY=GS1.1.1740054274.4.1.1740055145.23.0.0; ab.storage.sessionId.7a5f1472-069a-4372-8631-2f711442ee40=%7B%22g%22%3A%22f25a704d-c968-fc6d-be97-810b47449261%22%2C%22e%22%3A1740056946542%2C%22c%22%3A1740054277045%2C%22l%22%3A1740055146542%7D"
}

# 요청 본문 (Payload)
payload = {
    "pagination": {
        "page": 2,
        "size": 20
    },
    "recruitListType": "AREA",
    "sortTabCondition": {
        "searchPeriodType": "ALL",
        "sortType": "DEFAULT"
    },
    "condition": {
        "areas": [{"si": "I000", "gu": "", "dong": ""}],
        "employmentTypes": ["FULL_TIME"],
        "excludeKeywords": [],
        "excludeBar": False,
        "excludeNegoAge": False,
        "excludeNegoWorkWeek": False,
        "excludeNegoWorkTime": False,
        "excludeNegoGender": False,
        "parts": [],
        "similarDongJoin": False,
        "workDayTypes": [],
        "workPeriodTypes": [],
        "workTimeTypes": [],
        "workWeekTypes": [],
        "endWorkTime": "",
        "startWorkTime": "",
        "includeKeyword": "",
        "excludeKeywordList": [],
        "age": 0,
        "genderType": "NONE",
        "moreThanEducation": False,
        "educationType": "ALL",
        "selectedArea": {"si": "", "gu": "", "dong": ""}
    }
}

# 요청 보내기
response = requests.post(url, headers=headers, json=payload)

# 응답 JSON 출력
try:
    response_json = response.json()
    print(json.dumps(response_json, indent=4, ensure_ascii=False))
except requests.exceptions.JSONDecodeError:
    print("JSON 디코딩 오류 발생")
