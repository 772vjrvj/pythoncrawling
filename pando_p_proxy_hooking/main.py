# -*- coding: utf-8 -*-
"""
Selenium으로 fin.land.naver.com 기사 페이지 로드 -> 전체 HTML 수집
-> BeautifulSoup 파싱 -> __NEXT_DATA__의 dehydratedState.queries[*].state.data.result 배열 추출

pip install selenium beautifulsoup4
(크롬은 Selenium Manager가 자동으로 드라이버 처리)
"""

import json
import re
import time
from typing import List, Dict, Any, Callable, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class NaverFinCrawler:
    def __init__(self, headless: bool = False, log: Optional[Callable[[str], None]] = None):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.running = True
        self.log_signal_func = log or (lambda msg: print(msg))

    # --- Selenium setup/teardown ---
    def _build_driver(self) -> webdriver.Chrome:
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--lang=ko-KR")
        # 브라우저 UA를 requests와 최대한 유사하게
        opts.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        )
        return webdriver.Chrome(options=opts)

    def start(self):
        if self.driver is None:
            self.driver = self._build_driver()

    def stop(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    # --- Navigation & fetch ---
    def fetch_html(self, url: str, timeout: int = 15) -> str:
        """
        fin.land.naver.com 홈 먼저 접근(쿠키 세팅) 후, 기사 URL 이동.
        __NEXT_DATA__ 스크립트가 보일 때까지 대기하고 전체 HTML 반환.
        """
        assert self.driver is not None, "driver가 시작되지 않았습니다. start()를 먼저 호출하세요."

        # 1) 홈 선접속(쿠키 세팅)
        home = "https://fin.land.naver.com/"
        self.driver.get(home)
        # 홈이 404로 보일 때가 있어도 쿠키만 셋되면 됨. 0.5 ~ 1초 정도 대기
        time.sleep(0.8)

        # 2) 기사 페이지 이동
        self.driver.get(url)

        # 3) __NEXT_DATA__ 기다리기 (없으면 body 로 폴백)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'script#\\__NEXT_DATA__'))
            )
        except Exception:
            # 폴백: body가 있을 때까지 대기
            WebDriverWait(self.driver, max(5, timeout // 3)).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

        # 필요 시 작은 스크롤로 lazy load 유도
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
        except Exception:
            pass

        html = self.driver.page_source
        return html

    # --- __NEXT_DATA__ 파서 (질문에 주신 로직 그대로) ---
    def parse_next_queries_results(self, html: str) -> List[Dict]:
        """
        HTML 문자열에서 <script id="__NEXT_DATA__" type="application/json">...</script>
        내부의 JSON을 파싱하여, dehydratedState.queries[*].state.data.result 만 배열로 반환.

        반환: List[dict]  (각 dict가 'result' 객체)
        """
        if not isinstance(html, str) or not html:
            return []

        # 1) __NEXT_DATA__ 스크립트 블록 추출
        m = re.search(
            r'<script\s+id=["\']__NEXT_DATA__["\']\s+type=["\']application/json["\'][^>]*>(\{.*?\})</script>',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not m:
            return []

        # 2) JSON 로드
        try:
            data = json.loads(m.group(1))
        except Exception:
            return []

        # 3) dehydratedState.queries 접근
        dstate = (data.get("props") or {}).get("pageProps", {}).get("dehydratedState", {})
        queries = dstate.get("queries") or []
        results: List[Dict] = []

        for q in queries:
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            try:
                st = (q or {}).get("state", {})
                dt = (st or {}).get("data", {})
                if dt.get("isSuccess") is True and isinstance(dt.get("result"), dict):
                    results.append(dt["result"])  # 그대로 수집
            except Exception:
                # 한 항목 파싱 실패는 건너뜀
                continue

        return results


if __name__ == "__main__":
    ARTICLE_URL = "https://fin.land.naver.com/articles/2547502653"

    crawler = NaverFinCrawler(headless=False)
    try:
        crawler.start()
        html = crawler.fetch_html(ARTICLE_URL, timeout=15)

        # (선택) BeautifulSoup으로 전체 HTML을 한번 핸들링할 수 있음
        soup = BeautifulSoup(html, "html.parser")
        print("[INFO] title:", (soup.title.string if soup.title else "").strip())

        # __NEXT_DATA__에서 dehydratedState.queries[*].state.data.result 추출
        results = crawler.parse_next_queries_results(html)
        print(f"[INFO] extracted result: {results}")

    finally:
        crawler.stop()
