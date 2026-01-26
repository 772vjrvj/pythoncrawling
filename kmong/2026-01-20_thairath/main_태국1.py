# thairath_crawl.py
# -*- coding: utf-8 -*-

import csv
import time
import re
import os
import hashlib
import json
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


# =========================
# 설정
# =========================
BASE_URL = "https://api.thairath.co.th/tr-api/v1.1/thairath-online/search"
OUT_CSV = "thairath_until_2022_05 태국1.csv"

# ✅ (1) 시작 날짜를 "날짜"로 지정 가능하게
# - START_DT_UTC: 이 날짜(포함)부터 "과거로 내려가며" 수집 시작
# - None이면 기존 START_TS 값 사용
START_DT_UTC = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)  # 예: 2025-01-01부터 시작
START_TS = 1766124023000  # 최신 ts (START_DT_UTC가 None일 때만 사용)

# ✅ (2) 종료(컷오프) 날짜
CUTOFF_DT = datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

# ✅ 이미지 다운로드 폴더 (실행 경로 기준)
IMAGE_DIR = "../../image"

# ✅ 이미지 파일명 규칙: YYYYMMDD_기사제목
# 너무 길거나/특수문자/중복 대비 옵션
MAX_TITLE_LEN = 80  # 파일명용 제목 최대 길이(너무 길면 잘라냄)

# ✅ 상세 페이지 병렬 처리 워커 수
MAX_WORKERS = 10

# ✅ 상세 페이지 요청 타임아웃/재시도
DETAIL_TIMEOUT = 25
DETAIL_RETRIES = 2

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

# ✅ CSV 필드
FIELDS = [
    "id",
    "image",
    "image_large",
    "publishTime",
    "canonical",
    "title",
    "articleBody",   # ✅ 신규
    "image_file",
    "image_path",
]


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


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def safe_filename(text):
    """
    파일명으로 안전하게 변환 (윈도우 기준)
    """
    if text is None:
        text = ""
    s = str(text).strip()

    # 공백/개행 정리
    s = re.sub(r"\s+", " ", s)

    # 윈도우 금지문자 제거: \ / : * ? " < > |
    s = re.sub(r'[\\/:*?"<>|]', "", s)

    # 기타 특수문자 조금 정리
    s = re.sub(r"[\u200b-\u200f]", "", s)  # 제로폭 등
    s = s.strip(" .")

    if len(s) > MAX_TITLE_LEN:
        s = s[:MAX_TITLE_LEN].rstrip()

    if not s:
        s = "untitled"

    return s


def pick_image_url(item):
    """
    API item에서 이미지 URL 후보를 안전하게 선택
    - image_large 있으면 우선
    - 없으면 image
    """
    if not isinstance(item, dict):
        return ""
    url = item.get("image_large") or item.get("image") or ""
    if not url:
        return ""
    return str(url)


def guess_ext_from_url(url):
    """
    URL에서 확장자 추정. 애매하면 jpg
    """
    if not url:
        return "jpg"
    u = url.split("?")[0].split("#")[0].lower()
    for ext in ("jpg", "jpeg", "png", "webp", "gif"):
        if u.endswith("." + ext):
            return "jpg" if ext == "jpeg" else ext
    return "jpg"


def download_image(session, url, out_path):
    """
    이미지 다운로드 (스트리밍)
    """
    if not url:
        return False
    try:
        r = session.get(url, stream=True, timeout=30)
        r.raise_for_status()

        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
        return True
    except Exception:
        return False


def extract_rows(items):
    rows = []
    i = 0
    while i < len(items):
        it = items[i]
        if isinstance(it, dict):
            rows.append({
                "id": it.get("id"),
                "image": it.get("image"),
                "image_large": it.get("image_large"),
                "publishTime": it.get("publishTime"),
                "canonical": it.get("canonical"),
                "title": it.get("title"),

                # ✅ 신규 필드(초기값)
                "articleBody": "",   # ✅ 신규
                "image_file": "",
                "image_path": "",
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
        # ✅ 혹시라도 row에 임시 필드가 더 생겨도 CSV 안 터지게
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        i = 0
        while i < len(rows):
            w.writerow(rows[i])
            i += 1
    finally:
        f.close()


def dt_to_ts_ms(dt_utc):
    """
    datetime(UTC) -> epoch ms
    """
    if dt_utc is None:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return int(dt_utc.timestamp() * 1000)


def make_image_filename(publish_dt, title, ext, canonical=""):
    """
    YYYYMMDD_기사제목.ext
    - 동일 제목/날짜 충돌 대비: canonical 기반 짧은 해시 suffix
    """
    ymd = "00000000"
    if publish_dt:
        ymd = publish_dt.strftime("%Y%m%d")

    safe_title = safe_filename(title)

    base = f"{ymd}_{safe_title}"
    # 충돌 방지: canonical 있으면 6자리 해시
    if canonical:
        h = hashlib.md5(canonical.encode("utf-8")).hexdigest()[:6]
        base = f"{base}_{h}"

    return f"{base}.{ext}"


# =========================
# 상세(기사) 파싱: JSON-LD에서 articleBody 추출
# =========================
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL
)

def _clean_jsonld_text(s):
    if s is None:
        return ""
    t = s.strip()
    # HTML 안에서 종종 </script> 대응용으로 \u003c 같은 형태가 있을 수 있음
    # json.loads가 처리 가능하도록 그대로 두되, 앞뒤만 정리
    return t


def _pick_newsarticle_obj(obj):
    """
    JSON-LD가 dict or list일 수 있음.
    NewsArticle / Article / @graph 안에서 NewsArticle 찾아 반환.
    """
    if isinstance(obj, dict):
        # @graph 형태
        g = obj.get("@graph")
        if isinstance(g, list):
            for x in g:
                if isinstance(x, dict):
                    t = x.get("@type")
                    if t in ("NewsArticle", "Article"):
                        return x
        # 단일 객체
        t = obj.get("@type")
        if t in ("NewsArticle", "Article"):
            return obj
        return None

    if isinstance(obj, list):
        for x in obj:
            got = _pick_newsarticle_obj(x)
            if got:
                return got
        return None

    return None


def extract_article_body_from_html(html):
    """
    HTML에서 JSON-LD 스크립트들을 찾아 articleBody 추출
    """
    if not html:
        return ""

    matches = _JSONLD_RE.findall(html)
    if not matches:
        return ""

    i = 0
    while i < len(matches):
        raw = _clean_jsonld_text(matches[i])
        i += 1

        # JSON-LD가 여러 개 있을 수 있어서 하나씩 파싱 시도
        try:
            obj = json.loads(raw)
        except Exception:
            continue

        news = _pick_newsarticle_obj(obj)
        if not news:
            continue

        body = news.get("articleBody")
        if body:
            return str(body)

    return ""


# =========================
# thread-local session
# =========================
_thread_local = threading.local()

def get_thread_session():
    s = getattr(_thread_local, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update(HEADERS)
        s.cookies.update(COOKIES)
        _thread_local.session = s
    return s


def fetch_article_body(canonical_url):
    """
    canonical URL을 GET해서 JSON-LD에서 articleBody 추출
    """
    if not canonical_url:
        return ""

    tries = 0
    while tries <= DETAIL_RETRIES:
        tries += 1
        try:
            session = get_thread_session()
            r = session.get(canonical_url, timeout=DETAIL_TIMEOUT)
            r.raise_for_status()
            html = r.text
            return extract_article_body_from_html(html)
        except Exception:
            if tries > DETAIL_RETRIES:
                return ""
            time.sleep(0.5 * tries)

    return ""


def enrich_row(row, publish_dt, download_images=True):
    """
    row 단위로:
    1) articleBody 채우기 (canonical 상세페이지)
    2) 이미지 다운로드 + image_file / image_path 채우기
    """
    if not isinstance(row, dict):
        return row

    canonical = row.get("canonical") or ""
    # 1) articleBody
    body = fetch_article_body(canonical)
    row["articleBody"] = body

    # 2) 이미지 다운로드
    if download_images:
        img_url = pick_image_url(row)
        if img_url:
            ext = guess_ext_from_url(img_url)
            fname = make_image_filename(publish_dt, row.get("title"), ext, canonical=canonical)
            fpath = os.path.join(IMAGE_DIR, fname)

            ok = False
            if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                ok = True
            else:
                session = get_thread_session()
                ok = download_image(session, img_url, fpath)

            if ok:
                row["image_file"] = fname
                row["image_path"] = os.path.abspath(fpath)
            else:
                row["image_file"] = ""
                row["image_path"] = ""

    return row


# =========================
# 크롤러
# =========================
def crawl(start_ts, download_images=True):
    # ✅ 리스트 API는 단일 세션로 순차 호출
    list_session = requests.Session()
    list_session.headers.update(HEADERS)
    list_session.cookies.update(COOKIES)

    ensure_dir(IMAGE_DIR)

    seen = set()
    out = []

    ts = start_ts
    page = 0

    # ✅ 상세/이미지 멀티스레드 풀
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    try:
        while True:
            page += 1
            data = fetch(list_session, ts)
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

            # ✅ 이번 페이지에서 유효 row 선별
            candidates = []
            i = 0
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

                candidates.append((r, dt, key))

            # ✅ 병렬 처리 (articleBody + image)
            futures = []
            for (r, dt, key) in candidates:
                # 여기서 seen 처리하면, 스레드에서 실패해도 중복은 막힘
                seen.add(key)
                futures.append(pool.submit(enrich_row, r, dt, download_images))

            added = 0
            for fut in as_completed(futures):
                r2 = None
                try:
                    r2 = fut.result()
                except Exception:
                    continue

                if not isinstance(r2, dict):
                    continue

                out.append(r2)
                added += 1

                # === 결과 로그 ===
                print(
                    "  [ADD]",
                    r2.get("id"),
                    "|",
                    r2.get("publishTime"),
                    "|",
                    r2.get("title"),
                    "|",
                    r2.get("canonical"),
                    "|",
                    "body_len=" + str(len(r2.get("articleBody") or "")),
                    "|",
                    r2.get("image_file")
                )

            print("[PAGE]", page, "added=", added, "total=", len(out))

            if stop:
                print("[STOP] reached cutoff:", CUTOFF_DT.isoformat())
                break

            if oldest_ts is None:
                print("[STOP] no publishTs")
                break

            ts = oldest_ts - 1
            time.sleep(0.5)

    finally:
        pool.shutdown(wait=True)

    return out


# =========================
# main
# =========================
def main():
    # ✅ START_DT_UTC가 있으면 날짜로 start_ts 계산
    if START_DT_UTC is not None:
        start_ts = dt_to_ts_ms(START_DT_UTC)
    else:
        start_ts = START_TS

    rows = crawl(start_ts, download_images=True)
    write_csv(OUT_CSV, rows)
    print("[DONE]", OUT_CSV, "rows=", len(rows), "| image_dir=", os.path.abspath(IMAGE_DIR))


if __name__ == "__main__":
    main()
