import asyncio
import ssl
import threading
import time
from random import random
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path

import pandas as pd
import pyautogui

from src.workers.api_base_worker_sec import BaseApiWorkerSec

ssl._create_default_https_context = ssl._create_unverified_context


class ApiCoupangSetLoadWorker(BaseApiWorkerSec):
    def __init__(self):
        super().__init__()
        self.channel = None
        self.query = None
        self.component = None
        self.base_login_url = "https://login.coupang.com/login/login.pang"
        self.base_main_url = "https://www.coupang.com"

        self.excludeKeywords = ""
        self.includeKeyword = ""
        self.running = True

        self.com_list = []
        self.main_model = None
        self.product_info_list = []

        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0

    async def init(self):
        screen_width, screen_height = pyautogui.size()
        await self.page.set_viewport_size({"width": screen_width // 2, "height": screen_height})

        # 프로필로 시작했으므로 페이지 명시적 이동만 수행
        if self.page.url == "about:blank":
            await self.page.goto(self.base_main_url)
    async def main(self):
        result_list = []
        await self.wait_for_user_confirmation()
        await self.wait_for_select_confirmation()

        self.log_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_func("전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.log_func("전체 회사수 알수없음")
        self.log_func("전체 페이지수 알수없음")

        csv_filename = self.file_driver.get_csv_filename("쿠팡")
        columns = ["상호명", "연락처", "주소", "키워드"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        page = 1
        while True:
            if not self.running:
                self.log_func("크롤링이 중지되었습니다.")
                break

            urls = await self.fetch_product_urls(page)
            if not urls:
                break

            page += 1

            for index, url in enumerate(urls, start=1):
                if not self.running:
                    self.log_func("크롤링이 중지되었습니다.")
                    break

                obj = await self.fetch_product_detail(url)
                result_list.append(obj)

                await asyncio.sleep(1)
                if index % 5 == 0:
                    self.excel_driver.append_to_csv(csv_filename, result_list, columns)
                    result_list.clear()

            if result_list:
                self.excel_driver.append_to_csv(csv_filename, result_list, columns)
                result_list.clear()

    async def wait_for_user_confirmation(self):
        self.log_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
        event = threading.Event()
        self.msg_signal.emit("로그인 후 OK를 눌러주세요", "info", event)
        self.log_func("📢 사용자 입력 대기 중...")
        event.wait()
        self.log_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        # ✅ 로그인 후 상태 저장

        await self.page.goto(self.base_main_url)
        await asyncio.sleep(2)

    async def wait_for_select_confirmation(self):
        event = threading.Event()
        self.msg_signal.emit("쿠팡 검색 후 OK를 눌러주세요 (검색 결과 화면 확인 후)", "info", event)
        self.log_func("📢 사용자 입력 대기 중...")
        event.wait()
        self.log_func("✅ 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        current_url = self.page.url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        self.component = unquote(query_params.get("component", [""])[0])
        self.query = unquote(query_params.get("q", [""])[0])
        self.channel = unquote(query_params.get("channel", [""])[0])

        self.log_func(f"🔍 검색어: {self.query}")
        await asyncio.sleep(2)
        self.log_func("🚀 작업 완료!")

    async def fetch_product_detail(self, url):
        seller_info = {
            "상호명": "",
            "주소": "",
            "연락처": "",
            "키워드": self.query
        }

        print(f"🧭 상품 상세 진입: {url}")
        try:
            await self.page.goto(url)
            await asyncio.sleep(random() * 2 + 2)
            content = await self.page.content()
            if "판매자정보" not in content:
                print("판매자 정보가 표시되지 않음")
                return seller_info

            rows = await self.page.query_selector_all(".prod-delivery-return-policy-table tr")
            for row in rows:
                ths = await row.query_selector_all("th")
                tds = await row.query_selector_all("td")
                for i, th in enumerate(ths):
                    label = (await th.inner_text()).strip()
                    value = (await tds[i].inner_text()).strip() if i < len(tds) else ""
                    if "상호/대표자" in label:
                        seller_info["상호명"] = value
                    elif "사업장 소재지" in label:
                        seller_info["주소"] = value
                    elif "연락처" in label:
                        seller_info["연락처"] = value

        except Exception as e:
            print(f"❌ 판매자 정보 추출 오류: {e}")
        return seller_info

    async def fetch_product_urls(self, page):
        url = f"https://www.coupang.com/np/search?component=&q={self.query}&page={page}&listSize=72"
        print(f"🔍 상품 URL 조회: {url}")
        try:
            await self.page.goto(url)
            await asyncio.sleep(2)
            elements = await self.page.query_selector_all("li.ProductUnit_productUnit")
            print(f"✅ 상품 개수: {len(elements)}")

            urls = set()
            for el in elements:
                a_tag = await el.query_selector("a")
                href = await a_tag.get_attribute("href") if a_tag else None
                if href:
                    if not href.startswith("https://www.coupang.com"):
                        href = "https://www.coupang.com" + href
                    urls.add(href)

            return list(urls)
        except Exception as e:
            print(f"❌ 상품 URL 조회 중 오류 발생: {e}")
            return []
