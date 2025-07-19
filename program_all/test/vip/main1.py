import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "If-Modified-Since": "Wed, 16 Jul 2025 15:22:12 GMT",
    "Priority": "u=1, i",
    "Referer": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&ctg=3&tab=1",
    "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

base_url = "https://vipgunma.com/bbs/loadStore.php?bo_table=gm_1&ctg=3&tab={}"
wr_id_list = []
tab = 1

while True:
    url = base_url.format(tab)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[{tab}] 상태코드 오류: {response.status_code}")
        break

    try:
        data = response.json()
    except Exception as e:
        print(f"[{tab}] JSON 파싱 오류: {e}")
        break

    if data.get("result_code") != "success":
        print(f"[{tab}] result_code != success, 종료")
        break

    html = data.get("result_data", {}).get("html", "")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".listRow")

    if not rows:
        print(f"[{tab}] listRow 없음, 종료")
        break

    tab_ids = []
    for row in rows:
        a_tag = row.select_one(".subject a[href*='wr_id']")
        if a_tag:
            match = re.search(r"wr_id=(\d+)", a_tag['href'])
            if match:
                wr_id = match.group(1)
                wr_id_list.append(wr_id)
                tab_ids.append(wr_id)

    print(f"[{tab}] 수집된 wr_id: {tab_ids}")
    tab += 1
    time.sleep(0.5)  # 요청 간 간격

# 엑셀 저장
df = pd.DataFrame({"wr_id": wr_id_list})
df.to_excel("wr_id_list.xlsx", index=False)

print(f"\n✅ 총 wr_id 수집 개수: {len(wr_id_list)}")
print("✅ 결과는 'wr_id_list.xlsx'로 저장되었습니다.")
