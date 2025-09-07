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

        # 매물 대분류(realEstateType)
        self.RLET_TYPE_MAP = {
            "A01": "아파트",
            "A02": "오피스텔",
            "A06": "빌라",
            "B01": "아파트 분양권",
            "B02": "오피스텔분양권",
            "A04": "재건축",
            "C04": "전원주택",
            "C03": "단독/다가구",
            "D05": "상가주택",
            "C06": "한옥주택",
            "F01": "재개발",
            "C01": "원룸",
            "D02": "상가",
            "D01": "사무실",
            "E02": "공장/창고",
            "D03": "건물",
            "E03": "토지",
            "E04": "지식산업센터",
        }

        # 거래유형(tradeType)
        self.TRADE_TYPE_MAP = {
            "A1": "매매",
            "B1": "전세",
            "B2": "월세",
            "B3": "단기임대",
        }



    def init(self):
        self.driver_set(False)
        self.log_signal_func(f"선택 항목 : {self.columns}")
        return True


    def main(self):
        self.log_signal_func("시작합니다.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        df = pd.DataFrame(columns=self.columns)
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

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

        self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)

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
                self.get_same_addr_article(s, article)
                self.log_signal_func(f"[atcl] page={page}, atclNo={s}")

            if not resp.get("more", False):
                self.log_signal_func(f"[DONE] more=False, last_page={page}")
                break
            page += 1


    def get_same_addr_article(self, atcl_no, article):
        url = f"{self.same_addr_article_url}?articleNo={atcl_no}"
        rows = self.api_client.get(url, headers=self.headers)
        time.sleep(random.uniform(1, 2))
        if not rows:
            self.log_signal_func(f"[same-addr] base={atcl_no} 결과 없음")
            return

        first_parent_data = rows[0] if isinstance(rows[0], dict) else {}

        #atcl_list = {str(r["atclNo"]) for r in rows if isinstance(r, dict) and r.get("atclNo")}

        result_list = []

        atcl_list = []

        for index, same_no in enumerate(atcl_list, start=1):
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            self.log_signal_func(f"{first_parent_data["atclNm"]} {first_parent_data["bildNm"]} : {index}/{len(atcl_list)}")
            detail_url = f"{self.fin_land_article_url}/{same_no}"
            data = self.fetch_fin_land_detail_data(detail_url, first_parent_data, same_no, article)
            time.sleep(random.uniform(1, 2))
            if data is not None:
                result_list.append(data)

        if result_list:
            # {} 같은 빈 dict 제거
            cleaned = [row for row in result_list if row]
            if cleaned:  # 다 비어있으면 append_to_csv는 안 함
                self.result_data_list.append(cleaned)
                self.excel_driver.append_to_csv(self.csv_filename, cleaned, self.columns)



    def extract_addr(self, soup):
        nodes = soup.find_all(class_=re.compile(r"^ArticleComplexInfo_area-data"))
        if len(nodes) < 2:
            return ""
        target = nodes[1]
        # 자식(span/a 등) 텍스트 제외하고, div에 직접 붙은 텍스트만
        direct_txt = "".join(s.strip() for s in target.find_all(string=True, recursive=False))
        return direct_txt.strip()


    def fetch_fin_land_detail_data(self, url, first_parent_data, article_number, article):
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(5)

            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            # 전체주소
            full_addr = extract_addr(soup)


            # 1) __NEXT_DATA__ 우선 시도
            data_obj = None
            tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
            if tag and tag.string:
                try:
                    data_obj = json.loads(tag.string)
                except Exception:
                    data_obj = None

            # 2) 실패 시 정규식으로 보조 파싱
            if data_obj is None:
                m = re.search(
                    r'<script\s+id=["\']__NEXT_DATA__["\']\s+type=["\']application/json["\'][^>]*>(\{.*?\})</script>',
                    html,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                if m:
                    try:
                        data_obj = json.loads(m.group(1))
                    except Exception:
                        data_obj = None

            if not isinstance(data_obj, dict):
                self.log_signal_func(f"[detail] url={url}, __NEXT_DATA__ 없음/파싱 실패")
                return {}  # 원하는 스타일대로: 비워서 반환

            # dehydratedState.queries 탐색
            queries = (
                          data_obj.get("props", {})
                          .get("pageProps", {})
                          .get("dehydratedState", {})
                          .get("queries", [])
                      ) or []

            results_by_key = {}

            # GET /article/key
            # GET /article/galleryImages
            # GET /article/basicInfo
            # GET /article/maintenanceFee
            # GET /article/oldMaintenanceFee
            # GET /complex
            # GET /development
            # GET /article/agent

            for q in queries:
                qkey = (q.get("queryKey") or [None])[0]
                st = (q.get("state") or {})
                dt = (st.get("data") or {})
                if dt.get("isSuccess") is True and qkey:
                    results_by_key[qkey] = dt.get("result")

            parts = [
                (article or {}).get("시도", ""),
                (article or {}).get("시군구", ""),
                (article or {}).get("읍면동", "")
            ]

            # 필요에 따라 채워갈 출력 객체
            result_data = {
                "게시번호":  article_number,
                "상위매물명": first_parent_data["atclNm"],
                "상위매물동": first_parent_data["bildNm"],
                "상위매물게시번호": first_parent_data["atclNo"],
                "검색 주소": " ".join([p for p in parts if p]),
                "전체 주소": full_addr
            }

            # ── 여기서 원하는 섹션만 호출해서 채움 ──
            self.get_article_agent(result_data, results_by_key)
            self.get_complex(result_data, results_by_key)
            self.get_basic_info(result_data, results_by_key)
            self.get_article_key(result_data, results_by_key)


            self.log_signal_func(f"상세 데이터 : {result_data}")

            return result_data

        except Exception as e:
            self.log_signal_func(f"[ERROR] {url} JSON 추출 실패: {e}")
            return None  # 실패 시도 동일 스타일로 빈 dict


    def _as_dict(self, x):
        return x if isinstance(x, dict) else {}

    def _as_list(self, x):
        return x if isinstance(x, list) else []

    # 기본 정보
    def get_basic_info(self, out_obj, results_by_key):
        basic = results_by_key.get("GET /article/basicInfo")
        if not isinstance(basic, dict):
            self.log_signal_func("[detail] basicInfo 없음/타입불일치")
            return
        basic = self._as_dict(basic)

        # 하위 블록 안전 추출
        priceInfo = self._as_dict(basic.get("priceInfo"))
        communalComplexInfo = self._as_dict(basic.get("communalComplexInfo"))
        detailInfo = self._as_dict(basic.get("detailInfo"))
        # sizeInfo는 basic에 없으면 detailInfo에서 폴백
        sizeInfo = self._as_dict(basic.get("sizeInfo") or detailInfo.get("sizeInfo"))

        # 단지/동 기본값
        out_obj["단지명"] = (communalComplexInfo.get("complexName") or "").strip()
        out_obj["동이름"] = (communalComplexInfo.get("dongName") or "").strip()

        # 단지명이 비어있으면 detailInfo.articleDetailInfo.articleName로 보충
        if not out_obj["단지명"]:
            articleDetailInfo = self._as_dict(detailInfo.get("articleDetailInfo"))
            articleName = (articleDetailInfo.get("articleName") or "").strip()
            if articleName:
                out_obj["단지명"] = articleName

        # 가격/면적
        out_obj["매매가"]   = priceInfo.get("price") or ""
        out_obj["보증금"]   = priceInfo.get("warrantyAmount") or ""
        out_obj["월세"]     = priceInfo.get("rentAmount") or ""
        out_obj["공급면적"] = sizeInfo.get("supplySpace") or ""
        out_obj["평수"]     = sizeInfo.get("pyeongArea") or ""



    # 종합 정보 (주소)
    def get_complex(self, out_obj, results_by_key):
        complex_obj = results_by_key.get("GET /complex")
        if not isinstance(complex_obj, dict):
            self.log_signal_func("[detail] complex 없음/타입불일치")
            return

        address = self._as_dict(complex_obj.get("address"))
        out_obj["시도"] = address.get("city") or ""
        out_obj["시군구"] = address.get("division") or ""
        out_obj["읍면동"] = address.get("sector") or ""
        out_obj["번지"] = address.get("jibun") or ""
        out_obj["도로명주소"] = address.get("roadName") or ""
        out_obj["우편번호"] = address.get("zipCode") or ""

        # ▶ fallback: 4개 값 중 비어있으면 '전체 주소'를 공백 기준으로 잘라 0/1/2/3을 매핑
        if any(not (out_obj.get(k) or "").strip() for k in ("시도", "시군구", "읍면동", "번지")):
            full = (out_obj.get("전체 주소") or "").strip()
            if full:
                parts = full.split()  # 공백으로 분리
                if not (out_obj.get("시도") or "").strip()   and len(parts) >= 1:
                    out_obj["시도"] = parts[0]
                if not (out_obj.get("시군구") or "").strip() and len(parts) >= 2:
                    out_obj["시군구"] = parts[1]
                if not (out_obj.get("읍면동") or "").strip() and len(parts) >= 3:
                    out_obj["읍면동"] = parts[2]
                if not (out_obj.get("번지") or "").strip()   and len(parts) >= 4:
                    # 번지는 4번째 이후 토큰이 붙을 수 있어 안전하게 합침(예: '산 10-3')
                    out_obj["번지"] = " ".join(parts[3:])

    # 중개사 정보
    def get_article_agent(self, out_obj, results_by_key):
        agent = results_by_key.get("GET /article/agent")
        if not isinstance(agent, dict):
            self.log_signal_func("[detail] agent 없음/타입불일치")
            return

        phone = self._as_dict(agent.get("phone"))
        out_obj["중개사무소 이름"] = agent.get("brokerageName") or ""
        out_obj["중개사 이름"] = agent.get("brokerName") or ""
        out_obj["중개사무소 주소"] = agent.get("address") or ""
        out_obj["중개사무소 번호"] = phone.get("brokerage") or ""
        out_obj["중개사 헨드폰번호"] = phone.get("mobile") or ""


    # 번지 추가 확인
    def get_article_key(self, out_obj, results_by_key) -> None:
        entry = results_by_key.get("GET /article/key")
        if not isinstance(entry, dict):
            self.log_signal_func("[detail] key 없음/타입불일치: GET /article/key")
            return

        addr = entry.get("address") or entry.get("result", {}).get("address") or {}
        addr = self._as_dict(addr)
        jibun = (addr.get("jibun") or "").strip()

        if not (out_obj.get("번지") or "").strip():
            out_obj["번지"] = jibun

        t = entry.get("type") or entry.get("result", {}).get("type") or {}
        t = self._as_dict(t)

        rlet = (t.get("realEstateType") or "").strip()
        trade = (t.get("tradeType") or "").strip()

        if rlet:
            out_obj["매물 유형"] = self.RLET_TYPE_MAP.get(rlet, rlet)
        if trade:
            out_obj["거래 유형"] = self.TRADE_TYPE_MAP.get(trade, trade)



    def rlet_label(self, code):
        return self.RLET_TYPE_MAP.get((code or "").strip(), code)

    def trade_label(self, code):
        return self.TRADE_TYPE_MAP.get((code or "").strip(), code)



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
