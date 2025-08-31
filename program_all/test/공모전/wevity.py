import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.wevity.com/"
LIST_TPL = BASE + "?c=find&s=1&mode=soon&gub=1&gp={gp}"

# KST (Asia/Seoul)
KST = timezone(timedelta(hours=9))

def parse_deadline(day_text: str) -> str:
    """'D-8' → 오늘+8일, '오늘마감' → 오늘 날짜"""
    today = datetime.now(KST).date()
    m = re.search(r"D-(\d+)", day_text)
    if m:
        return (today + timedelta(days=int(m.group(1)))).isoformat()
    if "오늘" in day_text:
        return today.isoformat()
    return ""

def fetch_page(session: requests.Session, gp: int) -> list[dict]:
    """한 페이지에서 공모전 정보 목록 반환"""
    url = LIST_TPL.format(gp=gp)
    r = session.get(url, timeout=10)
    r.raise_for_status()

    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding

    soup = BeautifulSoup(r.text, "html.parser")
    ul = soup.select_one("ul.list")
    if not ul:
        return []

    rows = []
    for li in ul.find_all("li", recursive=False):
        classes = li.get("class") or []
        if "top" in classes:
            continue

        a = li.select_one("div.tit a")
        if not a:
            continue

        title = a.get_text(strip=True)
        href = (a.get("href") or "").strip()
        full_url = href if href.startswith("http") else f"{BASE}{href}"

        organ_el = li.select_one("div.organ")
        organ = organ_el.get_text(strip=True) if organ_el else ""

        day_el = li.select_one("div.day")
        day_raw = day_el.get_text(" ", strip=True) if day_el else ""
        deadline = parse_deadline(day_raw)

        rows.append({
            "사이트": "WEVITY",
            "공모전명": title,
            "주최사": organ,
            "URL": full_url,
            "마감일": deadline,
            "페이지": gp
        })
    return rows

def crawl_all(start_gp: int = 1, max_gp: int | None = None) -> list[dict]:
    """gp=start_gp 부터 끝까지 객체 배열로 반환"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
    }

    all_results: list[dict] = []
    with requests.Session() as s:
        s.headers.update(headers)
        gp = start_gp
        while True:
            if max_gp is not None and gp > max_gp:
                break

            rows = fetch_page(s, gp)
            if not rows:
                break

            all_results.extend(rows)
            gp += 1

    return all_results

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    results = crawl_all(start_gp=start)

    # 콘솔 출력 확인용
    for r in results:
        print(r)
