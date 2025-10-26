import requests
import json
from datetime import datetime

url = "https://api.linkareer.com/graphql"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://linkareer.com/",
}

def build_params(page: int) -> dict:
    return {
        "operationName": "ActivityList_Activities",
        "variables": json.dumps({
            "filterBy": {"status": "OPEN", "activityTypeID": "3"},
            "pageSize": 20,
            "page": page,
            "activityOrder": {"field": "RECRUIT_CLOSE_AT", "direction": "ASC"},
        }, ensure_ascii=False),
        "extensions": json.dumps({
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "f59df641666ef9f55c69ed6a14866bfd2f87fb32c89a80038a466b201ee11422"
            }
        }, ensure_ascii=False),
    }

def fetch_page(page: int):
    r = requests.get(url, params=build_params(page), headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

def parse_nodes(data, page: int):
    rows = []
    try:
        nodes = data["data"]["activities"]["nodes"]
        if not nodes:  # 데이터 없으면 빈 리스트 반환
            return []
        for node in nodes:
            title = node.get("title")
            organ = node.get("organizationName")
            act_id = node.get("id")
            full_url = f"https://linkareer.com/activity/{act_id}"
            deadline_ts = node.get("recruitCloseAt")
            deadline = ""
            if deadline_ts:
                dt = datetime.fromtimestamp(deadline_ts / 1000)
                deadline = dt.strftime("%Y-%m-%d")
            rows.append({
                "사이트": "LINKAREER",
                "공모전명": title,
                "주최사": organ,
                "URL": full_url,
                "마감일": deadline,
                "페이지": page
            })
    except Exception as e:
        print(f"[WARN] 페이지 {page} 파싱 실패:", e)
    return rows

if __name__ == "__main__":
    all_rows = []
    page = 1

    while True:
        print(f"▶ 페이지 {page} 요청 중...")
        data = fetch_page(page)
        rows = parse_nodes(data, page)
        if not rows:
            print(f"❌ 페이지 {page} 데이터 없음 → 종료")
            break
        all_rows.extend(rows)
        page += 1

    print(f"\n총 {len(all_rows)}건 수집 완료")
    for row in all_rows[:20]:  # 앞 20개만 미리보기 출력
        print(row)
