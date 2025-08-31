import requests
import json
from datetime import datetime

URL = "https://www.thinkcontest.com/thinkgood/user/contest/subList.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://www.thinkcontest.com",
    "Referer": "https://www.thinkcontest.com/thinkgood/user/contest/index.do",
    "X-Requested-With": "XMLHttpRequest",
}

# 고정된 querystr (사이트마다 다를 수 있음, 네트워크탭에서 확인)
QUERYSTR = "Y_lDUDfEFsFTgLsbFt-VyefFa_wNrqLAoJIolxPo8ycVd6GOlgXVj7ap50cJxtWOLgFMFsM1kbLnzIZm-i9SszImy2-ricuLrjl9bQDJNig"

def fetch_page(page: int, records_per_page: int = 10) -> dict:
    payload = {
        "querystr": QUERYSTR,
        "recordsPerPage": records_per_page,
        "currentPageNo": page,
        "contest_field": "",
        "host_organ": "",
        "enter_qualified": "",
        "award_size": "",
        "searchStatus": "Y",
        "sidx": "d_day",
        "sord": "ASC"
    }
    r = requests.post(URL, headers=HEADERS, data=json.dumps(payload), timeout=20)
    r.raise_for_status()
    return r.json()

def convert_date(dt_str: str) -> str:
    """ '2025-08-31 23:59:00.0' → '2025-08-31' """
    if not dt_str:
        return ""
    try:
        return datetime.strptime(dt_str.split()[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return dt_str

def parse_rows(data: dict) -> list:
    items = []
    for item in data.get("listJsonData", []):
        title = item.get("program_nm", "").strip()
        organ = item.get("host_company", "").strip()
        url = item.get("hompage_url", "").strip()
        deadline = convert_date(item.get("finish_dt", ""))

        items.append({
            "사이트": "THINKCONTEST",
            "공모전명": title,
            "주최사": organ,
            "URL": url,
            "마감일": deadline,
            "페이지": item.get("currentPageNo", 1)
        })
    return items

if __name__ == "__main__":
    all_rows = []
    page = 1
    while True:
        print(f"▶ 페이지 {page} 요청 중...")
        data = fetch_page(page)
        rows = parse_rows(data)
        if not rows:
            print(f"❌ 페이지 {page} 데이터 없음 → 종료")
            break

        all_rows.extend(rows)

        total = data.get("totalcnt", 0)
        per_page = data.get("recordsPerPage", 10)
        total_pages = (total + per_page - 1) // per_page
        if page >= total_pages:
            print("✅ 마지막 페이지 도달")
            break

        page += 1

    print(f"\n총 {len(all_rows)}건 수집 완료")
    for row in all_rows[:20]:  # 앞 20개만 출력
        print(row)
