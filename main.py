# -*- coding: utf-8 -*-
"""
Matichon Google CSE(JSONP) 수집기 (싱글 스레드)

- URL: https://cse.google.com/cse/element/v1
- start=0,10,20... 페이징
- results에서 title, url, richSnippet.cseImage.src, metatags.articleModifiedTime 추출
- articleModifiedTime -> Asia/Seoul(KST) "YYYY-MM-DD HH:MM:SS" 변환
- 기간 [START_DATE, END_DATE]만 CSV 저장, 나머지 SKIP
- sort=date(최신->과거) 가정: 페이지 내 oldest < START_DATE 이면 중지
- 403/429 방어: 랜덤 딜레이 + 쿨다운 + 재시도 + 연속 empty/fail 종료
- ✅ 쿠키는 아래 COOKIES 빈값 dict에 직접 넣어서 사용
"""

import csv
import json
import random
import time
from datetime import datetime, date, timezone, timedelta
from urllib.parse import urlencode

import requests


# =========================
# 1) 기간
# =========================
START_DATE = "2022.01.01"
END_DATE   = "2026.01.19"
OUT_CSV = "matichon_cse_2022-01-01_to_2025-05-31.csv"

# =========================
# 2) URL + payload(params)
# =========================
CSE_URL = "https://cse.google.com/cse/element/v1"

BASE_PARAMS = {
    "rsz": "filtered_cse",
    "num": "10",
    "hl": "th",
    "source": "gcsc",
    "start": "0",  # 루프에서 변경
    "cselibv": "f71e4ed980f4c082",
    "cx": "31cd9c819eaa64215",
    "q": "ชายแดนภาคใต้",
    "safe": "off",
    "cse_tok": "AEXjvhIhTiYbPsXu-AY2cCY74XIS:1768783191616",
    "lr": "",
    "cr": "",
    "gl": "",
    "filter": "0",
    "sort": "date",
    "as_oq": "",
    "as_sitesearch": "",
    "exp": "cc,apo",
    # callback은 고정해도 OK (파서는 함수명 무시)
    "callback": "google.search.cse.api7078",
    "rurl": "https://www.matichon.co.th/search?q=%E0%B8%8A%E0%B8%B2%E0%B8%A2%E0%B9%81%E0%B8%94%E0%B8%99%E0%B8%A0%E0%B8%B2%E0%B8%84%E0%B9%83%E0%B8%95%E0%B9%89#gsc.tab=0&gsc.q=%E0%B8%8A%E0%B8%B2%E0%B8%A2%E0%B9%81%E0%B8%94%E0%B8%99%E0%B8%A0%E0%B8%B2%E0%B8%84%E0%B9%83%E0%B8%95%E0%B9%89&gsc.page=1",
}

# =========================
# 3) 쿠키(여기에만 넣어서 쓰면 됨)
# =========================
COOKIES = {
    # 예) "NID": "",
    # 예) "__Secure-ENID": "",
    # 예) "CONSENT": "",
}

# =========================
# 4) 차단 완화 옵션
# =========================
SLEEP_MIN = 2.5
SLEEP_MAX = 6.5

COOLDOWN_MIN = 120
COOLDOWN_MAX = 420

MAX_RETRIES_PER_PAGE = 6
TIMEOUT_SEC = 25

MAX_CONSECUTIVE_EMPTY = 3
MAX_CONSECUTIVE_FAIL  = 5

KST = timezone(timedelta(hours=9))


# =========================
# utils
# =========================
def parse_date_any(s: str) -> date:
    s2 = (s or "").strip().replace("/", "-").replace(".", "-")
    return datetime.strptime(s2, "%Y-%m-%d").date()


def parse_jsonp(text: str) -> dict:
    """
    /*O_o*/
    google.search.cse.api7078({ ... });
    """
    s = (text or "").strip()

    # 1) /* ... */ 주석 제거
    if s.startswith("/*"):
        end = s.find("*/")
        if end != -1:
            s = s[end + 2 :].lstrip()

    # 2) 첫 '(' 와 마지막 ')' 사이를 JSON으로 본다
    lp = s.find("(")
    rp = s.rfind(")")
    if lp == -1 or rp == -1 or rp <= lp:
        raise ValueError("JSONP parse failed: cannot find (...)")

    payload = s[lp + 1 : rp].strip()
    return json.loads(payload)


def iso_to_kst(iso_str: str) -> tuple[str, date | None]:
    """
    '2026-01-18T22:47:16+07:00' -> KST(+09) 변환 후 텍스트
    return (yyyy-mm-dd hh:mm:ss, date_obj)
    """
    if not iso_str:
        return "", None
    try:
        fixed = iso_str.replace("Z", "+00:00")
        dt_obj = datetime.fromisoformat(fixed)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=KST)
        dt_kst = dt_obj.astimezone(KST)
        return dt_kst.strftime("%Y-%m-%d %H:%M:%S"), dt_kst.date()
    except Exception:
        return "", None


def human_sleep(a=SLEEP_MIN, b=SLEEP_MAX):
    time.sleep(random.uniform(a, b))


def cooldown():
    t = random.uniform(COOLDOWN_MIN, COOLDOWN_MAX)
    print(f"[COOLDOWN] {t:.1f}s")
    time.sleep(t)


def extract_rows(results: list[dict]) -> tuple[list[dict], date | None]:
    rows = []
    dates = []

    for r in results:
        rich = r.get("richSnippet") or {}
        img = rich.get("cseImage") or {}
        meta = rich.get("metatags") or {}

        title = r.get("titleNoFormatting") or r.get("title") or ""
        url = r.get("unescapedUrl") or r.get("url") or ""
        image_src = img.get("src") or ""

        mod_iso = meta.get("articleModifiedTime") or ""
        mod_kst, mod_date = iso_to_kst(mod_iso)

        if mod_date:
            dates.append(mod_date)

        rows.append({
            "title": title,
            "url": url,
            "image_src": image_src,
            "article_modified_kst": mod_kst,
            "article_modified_iso": mod_iso,
            "_modified_date": mod_date,
        })

    oldest = min(dates) if dates else None
    return rows, oldest


def fetch_page(sess: requests.Session, params: dict) -> dict:
    last_err = None

    for attempt in range(1, MAX_RETRIES_PER_PAGE + 1):
        try:
            resp = sess.get(CSE_URL, params=params, timeout=TIMEOUT_SEC)

            if resp.status_code in (403, 429):
                raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)

            resp.raise_for_status()
            return parse_jsonp(resp.text)

        except Exception as e:
            last_err = e
            print(f"[RETRY] attempt={attempt}/{MAX_RETRIES_PER_PAGE} err={e}")

            if isinstance(e, requests.HTTPError) and getattr(e, "response", None) is not None:
                sc = e.response.status_code
                if sc in (403, 429):
                    cooldown()
                else:
                    time.sleep(random.uniform(2.0, 5.0))
            else:
                time.sleep(random.uniform(2.0, 5.0))

    raise last_err


def crawl():
    sd = parse_date_any(START_DATE)
    ed = parse_date_any(END_DATE)
    if sd > ed:
        raise ValueError(f"START_DATE({sd}) > END_DATE({ed})")

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.matichon.co.th/",
        "DNT": "1",
        "Connection": "keep-alive",
    })

    # ✅ 쿠키 주입(빈 dict면 아무것도 안 들어감)
    if COOKIES:
        sess.cookies.update(COOKIES)

    num = int(BASE_PARAMS.get("num", "10") or "10")
    start = int(BASE_PARAMS.get("start", "0") or "0")

    wrote = 0
    seen = set()

    consecutive_empty = 0
    consecutive_fail = 0

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "title", "url", "image_src", "article_modified_kst", "article_modified_iso"
        ])
        w.writeheader()

        page_no = 1
        while True:
            params = dict(BASE_PARAMS)
            params["start"] = str(start)

            print(f"[REQ] page={page_no} start={start} url={CSE_URL}?{urlencode(params)}")

            try:
                data = fetch_page(sess, params)
                consecutive_fail = 0
            except Exception as e:
                consecutive_fail += 1
                print(f"[FAIL] page={page_no} start={start} err={e}")
                if consecutive_fail >= MAX_CONSECUTIVE_FAIL:
                    break
                human_sleep(8.0, 15.0)
                continue

            results = data.get("results") or []
            if not results:
                consecutive_empty += 1
                print(f"[EMPTY] page={page_no} start={start}")
                if consecutive_empty >= MAX_CONSECUTIVE_EMPTY:
                    break
                human_sleep(10.0, 20.0)
                continue
            else:
                consecutive_empty = 0

            rows, oldest = extract_rows(results)

            stop = (oldest is not None and oldest < sd)

            for row in rows:
                md = row["_modified_date"]
                if md is None:
                    continue
                if md < sd or md > ed:
                    continue

                u = row["url"] or ""
                if u and u in seen:
                    continue
                if u:
                    seen.add(u)

                w.writerow({
                    "title": row["title"],
                    "url": row["url"],
                    "image_src": row["image_src"],
                    "article_modified_kst": row["article_modified_kst"],
                    "article_modified_iso": row["article_modified_iso"],
                })
                wrote += 1

            # ✅ 여기 추가 (페이지 1회 처리 끝나면 즉시 저장)
            f.flush()

            print(f"[PAGE] {page_no} start={start} fetched={len(results)} wrote={wrote} oldest={oldest}")

            if stop:
                break

            page_no += 1
            start += num
            human_sleep()


    print(f"[DONE] wrote={wrote} file={OUT_CSV}")


if __name__ == "__main__":
    crawl()
