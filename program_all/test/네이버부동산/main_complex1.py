
# pip install selenium
from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


KEY_FIELD = "complexNumber"  # 전역 중복 제거 기준


def _build_search_url(keyword: str) -> str:
    """
    네이버 금융 부동산 검색 페이지(동일 출처 확보용).
    Same-Origin + credentials 포함 fetch가 가능하도록 먼저 이 페이지를 연다.
    """
    # "https://fin.land.naver.com/search?q=<encoded>"
    return "https://fin.land.naver.com/search?q=" + urlencode({"q": keyword})[2:]


def _build_api_url(keyword: str, size: int, page: int) -> str:
    """
    자동완성 단지 API URL 생성.
    예) https://fin.land.naver.com/front-api/v1/search/autocomplete/complexes?keyword=...&size=...&page=...
    """
    params = {"keyword": keyword, "size": str(size), "page": str(page)}
    return "https://fin.land.naver.com/front-api/v1/search/autocomplete/complexes?" + urlencode(params)


def _execute_fetch(driver: webdriver.Chrome, api_url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
    """
    동일 출처 컨텍스트에서 fetch를 실행하여 JSON을 반환.
    타임아웃(ms)까지 응답이 없으면 abort.
    """
    js = f"""
        const url = {json.dumps(api_url)};
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), {timeout_ms});
        return fetch(url, {{
            method: "GET",
            credentials: "include",
            headers: {{
                "Accept": "application/json, text/plain, */*"
            }},
            signal: controller.signal
        }})
        .then(r => r.json())
        .finally(() => clearTimeout(timeout));
    """
    return driver.execute_script(js)


def fetch_complexes_all(
        keywords: Iterable[str],
        *,
        size: int = 10,
        start_page: int = 1,
        per_request_delay: float = 0.35,   # 과호출 대비 지연(초)
        headless: bool = False
) -> List[Dict[str, Any]]:
    """
    네이버 금융 부동산 '자동완성 단지' API를 키워드 배열로 순회하며
    page=1..N을 돌고, 데이터가 없을 때 다음 키워드로 넘어가며,
    모든 결과를 하나의 리스트로 통합해 반환한다.

    - 전역 중복 제거 기준: item[complexNumber]
    - 각 아이템에는 _meta = {keyword, page} 를 부가한다.

    Returns:
        List[Dict[str, Any]] : 통합 결과 리스트
    """
    # ── Selenium Driver 준비
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=opts)

    collected: List[Dict[str, Any]] = []
    seen_numbers: set = set()  # complexNumber 전역 중복 방지

    try:
        for kw in keywords:
            # same-origin 확보를 위해 검색 페이지 먼저 진입
            driver.get(_build_search_url(kw))

            page = start_page
            while True:

                api_url = _build_api_url(kw, size=size, page=page)

                # API 호출
                data = _execute_fetch(driver, api_url)

                # 성공/형식 체크
                if not isinstance(data, dict) or not data.get("isSuccess"):
                    # 이 키워드는 중단하고 다음 키워드로
                    break

                result = data.get("result") or {}
                items: List[Dict[str, Any]] = result.get("list") or []

                # 종료 조건: 더 이상 데이터가 없으면 다음 키워드로
                if not items:
                    break

                # 수집 및 complexNumber 기준 중복 제거
                new_count = 0
                for it in items:
                    num = it.get(KEY_FIELD)

                    # complexNumber가 있으면 전역 중복 제거
                    if num is not None:
                        if num in seen_numbers:
                            continue
                        seen_numbers.add(num)

                    # 추적 메타
                    it.setdefault("_meta", {})
                    it["_meta"].update({"keyword": kw, "page": page})

                    collected.append(it)
                    new_count += 1

                tc = result.get("totalCount")
                print(f"    · 수집: {new_count}건 / totalCount={tc}, 누적={len(collected)}")

                page += 1
                time.sleep(per_request_delay)

    finally:
        driver.quit()

    return collected


# ──────────────────────────────────────────────
# 실행 예시
# ──────────────────────────────────────────────
if __name__ == "__main__":
    keywords = [
        "경기도 수원시 영통구",
        # "경기도 수원시 팔달구",
        # 필요 키워드 더 추가
    ]

    all_list = fetch_complexes_all(
        keywords,
        size=10,
        start_page=1,
        per_request_delay=0.35,
        headless=False       # 서버/CI면 True 추천
    )

    print("\n=== 최종 수집 개수:", len(all_list))
    # 샘플 출력 (앞 5개)
    for i, row in enumerate(all_list[:5], 1):
        print(row)
        # print(
        #     f"[{i}] complexNumber={row.get('complexNumber')}, "
        #     f"name={row.get('complexName') or row.get('name')}, "
        #     f"_meta={row.get('_meta')}"
        # )
