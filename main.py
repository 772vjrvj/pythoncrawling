# thairath_crawl.py
# -*- coding: utf-8 -*-

import csv
import time
import requests
from datetime import datetime, timezone

# =========================
# 설정
# =========================
BASE_URL = "https://api.thairath.co.th/tr-api/v1.1/thairath-online/search"
OUT_CSV = "thairath_until_2022_05.csv"

START_TS = 1766124023000  # 최신 ts
CUTOFF_DT = datetime(2022, 5, 1, 0, 0, 0, tzinfo=timezone.utc)


PARAMS_FIXED = {
    "q": "ชายแดนไทย",
    "type": "all",
    "sort": "recent",
    "path": "search",
}

# ✅ 전체 헤더 (브라우저 그대로)
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://www.thairath.co.th",
    "referer": "https://www.thairath.co.th/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "cache-control": "no-cache",
    "pragma": "no-cache",
}

# ❗ 쿠키는 여기만 채워라
COOKIES = {
    # "__cf_bm": "",
    # "_cfuvid": "",
}

FIELDS = ["id", "image", "publishTime", "canonical", "title"]


# =========================
# 유틸
# =========================
def parse_dt(iso_z):
    if not iso_z:
        return None
    s = iso_z.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def get_items(data):
    if not data:
        return []
    if "items" not in data:
        return []
    if "result" not in data["items"]:
        return []
    if "items" not in data["items"]["result"]:
        return []
    return data["items"]["result"]["items"]


def extract_rows(items):
    rows = []
    i = 0
    while i < len(items):
        it = items[i]
        if isinstance(it, dict):
            rows.append({
                "id": it.get("id"),
                "image": it.get("image"),
                "publishTime": it.get("publishTime"),
                "canonical": it.get("canonical"),
                "title": it.get("title"),
            })
        i += 1
    return rows


def fetch(session, ts):
    params = dict(PARAMS_FIXED)
    params["ts"] = ts
    r = session.get(BASE_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def write_csv(path, rows):
    f = open(path, "w", newline="", encoding="utf-8-sig")
    try:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        i = 0
        while i < len(rows):
            w.writerow(rows[i])
            i += 1
    finally:
        f.close()


# =========================
# 크롤러
# =========================
def crawl(start_ts):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    seen = set()
    out = []

    ts = start_ts
    page = 0

    while True:
        page += 1
        data = fetch(session, ts)
        items = get_items(data)

        if not items:
            print("[STOP] no items")
            break

        rows = extract_rows(items)

        oldest_ts = None
        stop = False

        i = 0
        while i < len(items):
            it = items[i]
            i += 1

            pts = it.get("publishTs")
            if isinstance(pts, int):
                if oldest_ts is None or pts < oldest_ts:
                    oldest_ts = pts

        i = 0
        added = 0
        while i < len(rows):
            r = rows[i]
            i += 1

            key = r.get("canonical")
            if not key or key in seen:
                continue

            dt = parse_dt(r.get("publishTime"))
            if dt and dt < CUTOFF_DT:
                stop = True
                continue

            seen.add(key)
            out.append(r)
            added += 1

            # === 결과 로그 ===
            print(
                "  [ADD]",
                r.get("id"),
                "|",
                r.get("publishTime"),
                "|",
                r.get("title"),
                "|",
                r.get("image"),
                "|",
                r.get("canonical")
            )

        print("[PAGE]", page, "added=", added, "total=", len(out))


        if stop:
            print("[STOP] reached 2022-05-01")
            break

        if oldest_ts is None:
            print("[STOP] no publishTs")
            break

        ts = oldest_ts - 1
        time.sleep(0.5)

    return out


# =========================
# main
# =========================
def main():
    rows = crawl(START_TS)
    write_csv(OUT_CSV, rows)
    print("[DONE]", OUT_CSV, "rows=", len(rows))


if __name__ == "__main__":
    main()
