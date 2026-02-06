# -*- coding: utf-8 -*-
import json
import random
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError

PROFILE_DIR = Path("./chrome_profile_naver")
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://msearch.shopping.naver.com/search/all?vertical=search&query="


def build_search_url(keyword: str) -> str:
    return BASE_URL + quote(keyword)


def is_captcha_like(html: str) -> bool:
    h = (html or "").lower()
    return ("wtmcaptcha" in h) or ("captcha" in h) or ("보안 확인" in html)


def get_next_data(page) -> dict:
    # script는 visible이 아니라 attached로 기다려야 안정적
    page.wait_for_selector("#__NEXT_DATA__", state="attached", timeout=60000)
    raw = page.locator("#__NEXT_DATA__").text_content()
    raw = (raw or "").strip()
    if not raw:
        raise RuntimeError("__NEXT_DATA__ 내용이 비어있음")
    return json.loads(raw)


def print_category_names(keyword: str, data: dict) -> None:
    try:
        category = data["props"]["pageProps"]["categoryNames"]
        print(f"\n✅ [{keyword}] categoryNames")
        for k, v in category.items():
            print(f"{k}: {v}")
    except Exception:
        print(f"\n❌ [{keyword}] categoryNames 없음")


def run(keywords):
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=False,
            viewport=None,
            args=["--start-maximized"],
            locale="ko-KR",
        )
        page = ctx.new_page()

        # ==========================
        # 1) 첫 검색(첫 키워드)에서만 캡챠 처리
        # ==========================
        first_kw = keywords[0]
        first_url = build_search_url(first_kw)

        print(f"\n🚀 (첫 검색) {first_kw} 접속")
        page.goto(first_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        if is_captcha_like(page.content()):
            print("\n🛡️ 캡챠/보안확인 발생(첫 검색에서만).")
            print("👉 브라우저에서 캡챠 해결 + '확인' 버튼 클릭까지 완료한 뒤 Enter 치세요.\n")
            input()

            # 캡챠 통과 후 같은 URL로 다시 진입 (확실히)
            page.goto(first_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

        data = get_next_data(page)
        print_category_names(first_kw, data)

        # 딜레이
        delay = random.uniform(2.0, 4.0)
        print(f"\n⏳ {delay:.2f}초 대기...\n")
        time.sleep(delay)

        # ==========================
        # 2) 이후 키워드는 캡챠 체크 없이 쭉 진행
        # ==========================
        for kw in keywords[1:]:
            url = build_search_url(kw)
            print(f"\n🚀 {kw} 접속")

            # networkidle로 바꿔도 됨. 여기선 domcontentloaded + NEXT_DATA 대기로 충분
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(1200)

            data = get_next_data(page)
            print_category_names(kw, data)

            delay = random.uniform(2.0, 4.0)
            print(f"\n⏳ {delay:.2f}초 대기...\n")
            time.sleep(delay)

        ctx.close()


if __name__ == "__main__":
    keywords = ["코카콜라", "펩시", "환타", "사이다", "웰치스"]
    run(keywords)
