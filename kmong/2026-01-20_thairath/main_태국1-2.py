# thairath_count_only.py
# -*- coding: utf-8 -*-

import csv
import time
from datetime import datetime, timezone
import requests

# =========================
# 설정 (기존과 최대한 동일)
# =========================
BASE_URL = "https://api.thairath.co.th/tr-api/v1.1/thairath-online/search"
OUT_CSV = "thairath_muslim_200404_200503_stats.csv"

# ✅ 기간 (UTC)
START_DT_UTC = datetime(2005, 3, 31, 23, 59, 59, tzinfo=timezone.utc)  # 최신부터 과거로 내려감
CUTOFF_DT    = datetime(2004, 4, 1, 0, 0, 0, tzinfo=timezone.utc)      # 이것보다 과거면 stop

# ✅ 키워드
KEYWORD = "มุสลิม"

PARAMS_FIXED = {
    "q": "ชายแดนไทย",  # 필요하면 "มุสลิม"로 변경
    "type": "all",
    "sort": "recent",
    "path": "search",
}

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

COOKIES = {
    # 기존처럼 필요한 것만 채워
}

# =========================
# 유틸 (기존 스타일 유지)
# =========================
def parse_dt(iso_z):
    if not iso_z:
        return None
    s = str(iso_z).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def dt_to_ts_ms(dt_utc):
    if dt_utc is None:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return int(dt_utc.timestamp() * 1000)

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

def pick_text(it):
    # title + (있으면) articleBody
    title = it.get("title") or ""
    body = it.get("articleBody") or ""  # 검색 응답에 없을 수 있음
    return (str(title) + "\n" + str(body)).strip()

def contains_keyword(text, keyword):
    if not text:
        return False
    return keyword in text

# =========================
# ✅ JSON 안전 fetch (핵심)
# =========================
def fetch_json_safe(session, ts, max_retries=5):
    params = dict(PARAMS_FIXED)
    params["ts"] = ts

    tries = 0
    while tries <= max_retries:
        tries += 1
        try:
            r = session.get(BASE_URL, params=params, timeout=20)

            # 429/5xx/403 같은 경우 백오프
            if r.status_code in (403, 429) or (500 <= r.status_code <= 599):
                wait = min(10, 0.8 * tries)
                print(f"[WARN] status={r.status_code} retry={tries}/{max_retries} sleep={wait}")
                time.sleep(wait)
                continue

            # 내용이 비었으면 재시도
            txt = r.text or ""
            if not txt.strip():
                wait = min(10, 0.6 * tries)
                print(f"[WARN] empty body retry={tries}/{max_retries} sleep={wait}")
                time.sleep(wait)
                continue

            # JSON 파싱 시도
            try:
                return r.json()
            except Exception:
                # JSON이 아닌 HTML(차단페이지) 등이면 앞부분 로깅 후 재시도
                head = txt.strip()[:200].replace("\n", " ")
                ctype = (r.headers.get("content-type") or "").lower()
                print(f"[WARN] JSON decode fail ctype={ctype} retry={tries}/{max_retries} head={head}")
                wait = min(10, 0.9 * tries)
                time.sleep(wait)
                continue

        except Exception as e:
            wait = min(10, 0.9 * tries)
            print(f"[WARN] request error retry={tries}/{max_retries} sleep={wait} err={str(e)[:120]}")
            time.sleep(wait)

    raise RuntimeError("fetch_json_safe 실패: JSON 응답을 안정적으로 받지 못했습니다. (차단/네트워크/쿠키 확인)")

# =========================
# 카운트 크롤
# =========================
def crawl_count(start_ts):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    seen = set()
    ts = start_ts
    page = 0

    total_docs = 0
    hit_docs = 0

    while True:
        page += 1
        data = fetch_json_safe(session, ts)
        items = get_items(data)

        if not items:
            print("[STOP] no items")
            break

        oldest_ts = None
        stop = False
        added = 0

        i = 0
        while i < len(items):
            it = items[i]
            i += 1

            canonical = (it.get("canonical") or "").strip()
            if not canonical or canonical in seen:
                continue
            seen.add(canonical)

            dt = parse_dt(it.get("publishTime"))
            if dt is None:
                continue

            # cutoff보다 과거면 stop (해당 item은 집계하지 않음)
            if dt < CUTOFF_DT:
                stop = True
                continue

            # 집계
            added += 1
            total_docs += 1

            text = pick_text(it)
            if contains_keyword(text, KEYWORD):
                hit_docs += 1

            # 다음 ts 계산
            pts = it.get("publishTs")
            if isinstance(pts, int):
                if oldest_ts is None or pts < oldest_ts:
                    oldest_ts = pts

        print(f"[PAGE] {page} added={added} total={total_docs} hit={hit_docs}")

        if stop:
            print("[STOP] reached cutoff:", CUTOFF_DT.isoformat())
            break

        if oldest_ts is None:
            print("[STOP] no publishTs")
            break

        ts = oldest_ts - 1
        time.sleep(0.5)

    hit_percent = round((hit_docs / total_docs) * 100, 4) if total_docs else 0.0
    return total_docs, hit_docs, hit_percent

def main():
    start_ts = dt_to_ts_ms(START_DT_UTC)

    total_docs, hit_docs, hit_percent = crawl_count(start_ts)

    # 결과 CSV 저장
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "keyword_th",
            "period_start",
            "period_end_inclusive",
            "query_q",
            "total_docs",
            "hit_docs",
            "hit_percent",
        ])
        w.writeheader()
        w.writerow({
            "keyword_th": KEYWORD,
            "period_start": "2004-04-01",
            "period_end_inclusive": "2005-03-31",
            "query_q": PARAMS_FIXED.get("q", ""),
            "total_docs": total_docs,
            "hit_docs": hit_docs,
            "hit_percent": hit_percent,
        })

    print("[DONE]", OUT_CSV, "| total=", total_docs, "| hit=", hit_docs, "| %=", hit_percent)

if __name__ == "__main__":
    main()
