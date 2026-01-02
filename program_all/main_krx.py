# -*- coding: utf-8 -*-
import json
import requests

URL = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
REFERER = "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"

payload = {
    "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
    "locale": "ko_KR",
    "mktId": "ALL",
    "trdDd": "20251226",
    "share": "1",
    "money": "1",
    "csvxls_isNo": "false",
}

headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://data.krx.co.kr",
    "referer": REFERER,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "x-requested-with": "XMLHttpRequest",
}

s = requests.Session()

# ✅ 1) 세션 워밍업 (여기서 JSESSIONID 자동 발급)
s.get("https://data.krx.co.kr", headers=headers)

# ✅ 2) 같은 세션으로 POST
r = s.post(URL, headers=headers, data=payload)
r.raise_for_status()

data = r.json()
print(json.dumps(data, ensure_ascii=False, indent=2))
