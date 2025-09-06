# -*- coding: utf-8 -*-
import json
import random
import re
import threading
import time
from urllib.parse import urlparse, unquote, urlencode

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.chrome_macro import ChromeMacro
from src.utils.config import NAVER_LOC_ALL_REAL_DETAIL


class ApiNaverLandRealEstateDetailSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()

        self.csv_filename = None
        self.current_cnt = 0
        self.total_cnt = 0
        self.driver = None
        self.columns = None
        self.site_name = "네이버 공인중개사 번호"
        self.before_pro_value = 0.0
        self.file_driver = None
        self.naver_loc_all_real_detail = NAVER_LOC_ALL_REAL_DETAIL
        self.detail_region_article_list = []
        self.result_data_list = []
        self.same_addr_article_url = "https://m.land.naver.com/article/getSameAddrArticle"
        self.fin_land_article_url = "https://fin.land.naver.com/articles"

        self.excel_driver = None
        self.selenium_driver = None
        self.api_client = None
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

    def init(self):
        self.driver_set(False)
        self.log_signal_func(f"선택 항목 : {self.columns}")
        return True

    def main(self):
        self.log_signal_func("시작합니다.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        df = pd.DataFrame(columns=self.columns)
        df.to_csv(self.csv_filename, index=False)

        self.loc_all_detail_list_set()

        for index, article in enumerate(self.detail_region_article_list, start=1):
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            self.fetch_same_article_detail_list_by_article(article)

            self.log_signal_func(f"진행 ({index} / {self.total_cnt}) ==============================")
            pro_value = (index / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
        return True

    def find_location_detail(self, sido, sigungu, eupmyeondong):
        for item in self.naver_loc_all_real_detail:
            if (sido == item["시도"]) and (sigungu == item["시군구"]) and (eupmyeondong == item["읍면동"]):
                return item
        return None

    def loc_all_detail_list_set(self):
        self.total_cnt = len(self.region)
        self.log_signal_func(f"전체 지역 수 {self.total_cnt} 개")
        for _, loc in enumerate(self.region, start=1):
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            loc_detail = self.find_location_detail(loc["시도"], loc["시군구"], loc["읍면동"])
            if loc_detail:
                self.detail_region_article_list.append(loc_detail)
            else:
                self.log_signal_func(f"[WARN] 지역 매핑 실패: {loc}")

    def fetch_same_article_detail_list_by_article(self, article):
        url = (article or {}).get("articleList")
        if not url:
            self.log_signal_func("[WARN] article['articleList'] 없음, 스킵")
            return

        page = 1
        while True:
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            resp = self.api_client.get(url, headers=self.headers, params={"page": page})
            time.sleep(random.uniform(1, 2))
            if not resp:
                self.log_signal_func(f"[STOP] page={page} 응답 없음")
                break

            body = resp.get("body") or []
            if not body:
                self.log_signal_func(f"[STOP] page={page} 결과 없음")
                break

            atcl_nos = {str(row.get("atclNo")) for row in body if row.get("atclNo")}
            for s in atcl_nos:
                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                self.get_same_addr_article(s)
                self.log_signal_func(f"[atcl] page={page}, atclNo={s}")

            if not resp.get("more", False):
                self.log_signal_func(f"[DONE] more=False, last_page={page}")
                break
            page += 1


    def get_same_addr_article(self, atcl_no):
        url = f"{self.same_addr_article_url}?articleNo={atcl_no}"
        resp = self.api_client.get(url, headers=self.headers)
        time.sleep(random.uniform(1, 2))

        rows = resp if isinstance(resp, list) else (list(resp) if isinstance(resp, dict) else [])
        if not rows:
            self.log_signal_func(f"[same-addr] base={atcl_no} 결과 없음")
            return

        first_parent_data = rows[0] if isinstance(rows[0], dict) else {}

        atcl_list = {str(r["atclNo"]) for r in rows if isinstance(r, dict) and r.get("atclNo")}

        result_list = []
        for same_no in atcl_list:
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            detail_url = f"{self.fin_land_article_url}/{same_no}"
            data = self.fetch_fin_land_detail_data(detail_url, first_parent_data)
            time.sleep(random.uniform(1, 2))
            if data is not None:
                result_list.append(data)
            self.log_signal_func(f"data : {data}")

        if result_list:
            self.result_data_list.append(result_list)
            self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns)

    
    # 최종 상세 데이터
    def fetch_fin_land_detail_data(self, url, first_parent_data):
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(5)

            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
            raw_json = tag.string if (tag and tag.string) else None

            if not raw_json:
                m = re.search(
                    r'<script\s+id=["\']__NEXT_DATA__["\']\s+type=["\']application/json["\'][^>]*>(\{.*?\})</script>',
                    html,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                if m:
                    raw_json = m.group(1)

            if not raw_json:
                self.log_signal_func(f"[WARN] __NEXT_DATA__ 없음: {url}")
                return None

            data = json.loads(raw_json)
            self.log_signal_func(f"[detail] url={url}, JSON 로드 성공")





            return data

        except Exception as e:
            self.log_signal_func(f"[ERROR] {url} JSON 추출 실패: {e}")
            return None

    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)
        self.driver = self.selenium_driver.start_driver(1200)

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        if self.running:
            self.progress_end_signal.emit()

    def stop(self):
        self.running = False
