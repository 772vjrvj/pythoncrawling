# thairath_crawl.py
# -*- coding: utf-8 -*-

import csv
import time
import re
import os
import hashlib
import requests
from datetime import datetime, timezone

# =========================
# 설정
# =========================
BASE_URL = "https://api.thairath.co.th/tr-api/v1.1/thairath-online/search"
OUT_CSV = "thairath_until_2022_05.csv"

# ✅ (1) 시작 날짜를 "날짜"로 지정 가능하게
# - START_DT_UTC: 이 날짜(포함)부터 "과거로 내려가며" 수집 시작
# - None이면 기존 START_TS 값 사용
START_DT_UTC = datetime(2026, 1, 15, 0, 0, 0, tzinfo=timezone.utc)  # 예: 2025-01-01부터 시작
START_TS = 1766124023000  # 최신 ts (START_DT_UTC가 None일 때만 사용)

# ✅ (2) 종료(컷오프) 날짜
CUTOFF_DT = datetime(2026, 1, 14, 0, 0, 0, tzinfo=timezone.utc)

# ✅ 이미지 다운로드 폴더 (실행 경로 기준)
IMAGE_DIR = "image"

# ✅ 이미지 파일명 규칙: YYYYMMDD_기사제목
# 너무 길거나/특수문자/중복 대비 옵션
MAX_TITLE_LEN = 80  # 파일명용 제목 최대 길이(너무 길면 잘라냄)

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

# ✅ CSV 필드 확장 (image_file, image_path 추가)
FIELDS = ["id", "image", "publishTime", "canonical", "title", "image_file", "image_path"]


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

        # content-type 기반 확장자 보정(가능하면)
        ct = (r.headers.get("content-type") or "").lower()
        # 확장자 확인용만 참고 (강제 변경은 안 하고, out_path가 이미 정해졌으면 그대로 저장)
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
                "publishTime": it.get("publishTime"),
                "canonical": it.get("canonical"),
                "title": it.get("title"),
                "image_large": it.get("image_large"),

                # ✅ 신규 필드(초기값)
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
        w = csv.DictWriter(f, fieldnames=FIELDS)
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
# 크롤러
# =========================
def crawl(start_ts, download_images=True):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    # 이미지 요청도 같은 세션 사용
    img_session = session

    ensure_dir(IMAGE_DIR)

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

            # ✅ 이미지 다운로드 및 파일명/경로 저장
            if download_images:
                img_url = pick_image_url(r)  # rows에는 image_large도 들어있음
                ext = guess_ext_from_url(img_url)
                fname = make_image_filename(dt, r.get("title"), ext, canonical=key)
                fpath = os.path.join(IMAGE_DIR, fname)

                ok = False
                # 이미 존재하면 스킵(재실행 대비)
                if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                    ok = True
                else:
                    ok = download_image(img_session, img_url, fpath)

                if ok:
                    r["image_file"] = fname
                    r["image_path"] = os.path.abspath(fpath)
                else:
                    r["image_file"] = ""
                    r["image_path"] = ""

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
                r.get("canonical"),
                "|",
                r.get("image_file")
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
