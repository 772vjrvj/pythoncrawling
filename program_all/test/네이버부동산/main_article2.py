# pip install selenium
from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

HTML_URL_TPL = "https://fin.land.naver.com/complexes/{complexNumber}?tab=article"
API_URL = "https://fin.land.naver.com/front-api/v1/complex/article/list"

DEFAULT_PAYLOAD_BASE = {
    "tradeTypes": [],
    "pyeongTypes": [],
    "dongNumbers": [],
    "userChannelType": "PC",
    "articleSortType": "RANKING_DESC",
    "seed": "",
    "lastInfo": [],   # 단지별 첫 호출 시 반드시 []로 초기화
    "size": 100,
}

def _wait_ready(driver: webdriver.Chrome, timeout_sec: float = 5.0) -> None:
    """document.readyState가 complete될 때까지 대기"""
    end = time.time() + timeout_sec
    while time.time() < end:
        state = driver.execute_script("return document.readyState")
        if state == "complete":
            return
        time.sleep(0.05)

def _execute_post_json(driver: webdriver.Chrome, url: str, body: Dict[str, Any], timeout_ms: int = 15000) -> Dict[str, Any]:
    js = r"""
        const url = arguments[0];
        const body = arguments[1];
        const timeoutMs = arguments[2];
        const done = arguments[3];

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        fetch(url, {
            method: "POST",
            credentials: "include",
            headers: {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body),
            signal: controller.signal
        })
        .then(r => r.json())
        .then(data => done({ ok: true, data }))
        .catch(err => done({ ok: false, error: String(err) }))
        .finally(() => clearTimeout(timer));
    """
    result = driver.execute_async_script(js, url, body, timeout_ms)
    if not isinstance(result, dict) or not result.get("ok"):
        raise RuntimeError(f"fetch error: {result.get('error') if isinstance(result, dict) else result}")
    data = result.get("data") or {}
    if not isinstance(data, dict):
        raise RuntimeError("Invalid JSON response")
    return data

def fetch_articles_by_complexes(
        rows: Iterable[Dict[str, Any]],
        *,
        size: int = 100,
        headless: bool = False,
        per_request_delay: float = 0.25,
        use_pagination: bool = True,
) -> List[Dict[str, Any]]:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=opts)
    collected: List[Dict[str, Any]] = []

    try:
        for row in rows:
            cn = row.get("complexNumber")
            if cn is None:
                continue

            # ✅ 핵심 수정: complexNumber를 문자열로 강제
            complex_number = str(cn)
            complex_name = row.get("complexName") or row.get("name")

            # Same-Origin 컨텍스트 확보
            html_url = HTML_URL_TPL.format(complexNumber=complex_number)
            driver.get(html_url)
            _wait_ready(driver)          # 페이지 로드 대기
            time.sleep(0.15)             # 토큰/쿠키 세팅 여유

            # 단지별 최초 payload (lastInfo는 반드시 빈 배열)
            payload = dict(DEFAULT_PAYLOAD_BASE)
            payload["complexNumber"] = complex_number
            payload["size"] = size
            payload["lastInfo"] = []     # ⭐ 단지마다 리셋

            page = 1
            while True:
                data = _execute_post_json(driver, API_URL, payload)

                if data.get("isSuccess") is not True:
                    break

                result = data.get("result") or {}
                items: List[Dict[str, Any]] = (
                        result.get("list")
                        or result.get("articles")
                        or result.get("contents")
                        or []
                )
                if not items:
                    break

                for it in items:
                    it.setdefault("_meta", {})
                    it["_meta"].update({
                        "complexNumber": complex_number,
                        "complexName": complex_name,
                        "page": page
                    })
                    collected.append(it)

                if not use_pagination:
                    break

                next_cursor = result.get("lastInfo")
                has_more = (
                        result.get("hasMore")
                        or result.get("isNext")
                        or result.get("hasNext")
                )

                # 다음 페이지 커서 설정
                if next_cursor:
                    payload["lastInfo"] = next_cursor

                # 다음 호출 여부 판단:
                # 1) has_more flag가 있으면 그에 따름
                # 2) flag가 없는 경우에도 next_cursor가 있고 이번에 items가 찼으면 한 번 더 시도
                if has_more or (next_cursor and len(items) > 0):
                    page += 1
                    time.sleep(per_request_delay)
                    continue

                break

            time.sleep(per_request_delay)

    finally:
        driver.quit()

    return collected

# ── 테스트 예시
if __name__ == "__main__":
    input_rows = [
        {'complexName': '광교더로프트',  'complexNumber': 105334},  # int여도 OK (문자열로 캐스팅됨)
        {'complexName': '광교파인렉스I', 'complexNumber': "105340"}, # 문자도 OK
    ]
    articles = fetch_articles_by_complexes(
        input_rows,
        size=100,
        headless=False,
        per_request_delay=0.25,
        use_pagination=True,
    )
    print("=== 최종 수집 건수:", len(articles))
    for i, a in enumerate(articles[:5], 1):
        print(f"[{i}] articleId={a.get('articleNumber') or a.get('id')}, "
              f"title={a.get('title')}, _meta={a.get('_meta')}")
