import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.all-con.co.kr/page/ajax.contest_list.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.all-con.co.kr",
    "Referer": "https://www.all-con.co.kr/list/contest/1/3?sortname=cl_end_date&sortorder=asc&stx=&sfl=&t=1&ct=&sc=&tg=",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_page(page: int) -> dict:
    """특정 페이지 요청"""
    payload = {
        "sortorder": "asc",
        "page": str(page),
        "sortname": "cl_end_date",
        "stx": "",
        "sfl": "",
        "rows": "15",
        "t": "1"
    }
    r = requests.post(URL, headers=HEADERS, data=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def convert_date(date_str: str) -> str:
    """
    '25.08.25' → '2025-08-25' 로 변환
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%y.%m.%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str


def parse_rows(data: dict) -> list:
    """JSON rows → 객체 배열 변환"""
    page = int(data.get("currentPage", 1))
    items = []
    for item in data.get("rows", []):
        # cl_title 파싱
        soup = BeautifulSoup(item.get("cl_title", ""), "html.parser")
        a_tag = soup.find("a")
        title = a_tag.get_text(strip=True) if a_tag else ""
        url_path = a_tag["href"] if a_tag else ""
        full_url = f"https://www.all-con.co.kr{url_path}"

        # 주최사
        organ = item.get("cl_host", "").strip()

        # 기간 → 종료일 변환
        date_text = item.get("cl_date", "")
        deadline = ""
        if "~" in date_text:
            end_raw = date_text.split("~")[-1]  # "25.09.23"
            deadline = convert_date(end_raw)

        items.append({
            "사이트": "ALL-CON",
            "공모전명": title,
            "주최사": organ,
            "URL": full_url,
            "마감일": deadline,
            "페이지": page
        })
    return items


if __name__ == "__main__":
    all_rows = []
    page = 1

    while True:
        print(f"▶ 페이지 {page} 요청...")
        data = fetch_page(page)

        rows = parse_rows(data)
        if not rows:
            print(f"❌ 페이지 {page} 데이터 없음 → 종료")
            break

        all_rows.extend(rows)

        total_page = int(data.get("totalPage", page))
        if page >= total_page:
            print("✅ 마지막 페이지 도달")
            break

        page += 1

    print(f"\n총 {len(all_rows)}건 수집 완료")
    for row in all_rows[:20]:  # 앞 20개만 출력
        print(row)
