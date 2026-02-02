import json
import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.type_utils import _as_dict, _as_list, _s, ensure_list_attr
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


class ApiNaverLandRealEstateDetailSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()
        self.search_trade_labels = []
        self.search_rlet_labels = []

        self.csv_filename = None
        self.current_cnt = 0
        self.total_cnt = 0
        self.driver = None

        self.columns = None
        self.region = None
        self.setting_detail = None

        self.site_name = "네이버 공인중개사 번호"
        self.before_pro_value = 0.0

        self.naver_loc_all_real_detail = []
        self.detail_region_article_list = []
        self.result_data_list = []

        self.same_addr_article_url = "https://m.land.naver.com/article/getSameAddrArticle"
        self.fin_land_article_url = "https://fin.land.naver.com/articles"

        self.excel_driver = None
        self.file_driver = None
        self.selenium_driver = None
        self.api_client = None

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://m.land.naver.com/",
        }

        self.RLET_TYPE_MAP = {
            "A01": "아파트", "A02": "오피스텔", "C02": "빌라", "A06": "다세대/연립",
            "B01": "아파트 분양권", "B02": "오피스텔분양권",
            "A04": "재건축", "C04": "전원주택", "C03": "단독/다가구",
            "D05": "상가주택", "C06": "한옥주택", "F01": "재개발",
            "C01": "원룸", "D02": "상가", "D01": "사무실",
            "E02": "공장/창고", "D03": "건물", "E03": "토지",
            "E04": "지식산업센터", "D04": "상가건물", "Z00": "기타"
        }

        self.TRADE_TYPE_MAP = {"A1": "매매", "B1": "전세", "B2": "월세", "B3": "단기임대"}

    def init(self):
        ensure_list_attr(self, "region")
        ensure_list_attr(self, "columns")
        ensure_list_attr(self, "setting_detail")
        self.driver_set(False)
        self.log_signal_func(f"선택 항목 : {self.columns}")
        self.log_signal_func(f"상세 정보 : {self.setting_detail}")
        return True

    def main(self):
        self.log_signal_func("시작합니다.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)

        df = pd.DataFrame(columns=self.columns or [])
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

        self.naver_loc_all_real_detail = self.file_driver.read_json_array_from_resources("naver_real_estate_data.json")
        self._set_region_articles()

        for index, article in enumerate(self.detail_region_article_list, start=1):
            if not self.running:
                self.log_signal_func("중지됨")
                break

            self._crawl_article_list(article)

            pro_value = (index / max(self.total_cnt, 1)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

        try:
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
        except Exception as e:
            self.log_signal_func(f"[WARN] 엑셀 변환 실패: {e}")

        return True

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(1)
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            self.log_signal_func(f"[WARN] 드라이버 종료 실패: {e}")
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False

    def driver_set(self, headless):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)
        self.driver = self.selenium_driver.start_driver(1200)

    def get_basic_info(self, out_obj, results_by_key):
        basic = _as_dict(results_by_key.get("GET /article/basicInfo"))
        if not basic:
            return

        price_info = _as_dict(basic.get("priceInfo"))
        communal = _as_dict(basic.get("communalComplexInfo"))
        detail_info = _as_dict(basic.get("detailInfo"))
        size_info = _as_dict(basic.get("sizeInfo") or _as_dict(detail_info.get("sizeInfo")))

        out_obj["단지명"] = _s(communal.get("complexName"))
        out_obj["동이름"] = _s(communal.get("dongName"))

        ad = _as_dict(detail_info.get("articleDetailInfo"))
        if ad:
            if not out_obj.get("단지명"):
                out_obj["단지명"] = _s(ad.get("articleName"))
            out_obj["매물특징"] = _s(ad.get("articleFeatureDescription"))
            out_obj["매물확인일"] = _s(ad.get("exposureStartDate"))
            out_obj["건축물용도"] = _s(ad.get("buildingPrincipalUse"))

        out_obj["매매가"] = _s(price_info.get("price"))
        out_obj["보증금"] = _s(price_info.get("warrantyAmount"))
        out_obj["월세"] = _s(price_info.get("rentAmount"))
        out_obj["공급면적"] = _s(size_info.get("supplySpace"))
        out_obj["평수"] = _s(size_info.get("pyeongArea"))
        out_obj["대지면적"] = _s(size_info.get("landSpace"))
        out_obj["연면적"] = _s(size_info.get("floorSpace"))
        out_obj["건축면적"] = _s(size_info.get("buildingSpace"))
        out_obj["전용면적"] = _s(size_info.get("exclusiveSpace"))

    def get_complex(self, out_obj, results_by_key):
        comp = _as_dict(results_by_key.get("GET /complex"))
        if not comp:
            return

        addr = _as_dict(comp.get("address"))
        out_obj["시도"] = _s(addr.get("city"))
        out_obj["시군구"] = _s(addr.get("division"))
        out_obj["읍면동"] = _s(addr.get("sector"))
        out_obj["번지"] = _s(addr.get("jibun"))
        out_obj["도로명주소"] = _s(addr.get("roadName"))
        out_obj["우편번호"] = _s(addr.get("zipCode"))

    def get_article_agent(self, out_obj, results_by_key):
        agent = _as_dict(results_by_key.get("GET /article/agent"))
        if not agent:
            return

        phone = _as_dict(agent.get("phone"))
        out_obj["중개사무소이름"] = _s(agent.get("brokerageName"))
        out_obj["중개사이름"] = _s(agent.get("brokerName"))
        out_obj["중개사무소주소"] = _s(agent.get("address"))
        out_obj["중개사무소번호"] = _s(phone.get("brokerage"))
        out_obj["중개사핸드폰번호"] = _s(phone.get("mobile"))

    def get_article_key(self, out_obj, results_by_key):
        entry = _as_dict(results_by_key.get("GET /article/key"))
        if not entry:
            return

        addr = _as_dict(entry.get("address") or _as_dict(entry.get("result")).get("address"))
        jibun = _s(addr.get("jibun"))
        if not _s(out_obj.get("번지")):
            out_obj["번지"] = jibun

        t = _as_dict(entry.get("type") or _as_dict(entry.get("result")).get("type"))
        rlet = _s(t.get("realEstateType"))
        trade = _s(t.get("tradeType"))

        if rlet:
            out_obj["매물유형"] = self.RLET_TYPE_MAP.get(rlet, rlet)
        if trade:
            out_obj["거래유형"] = self.TRADE_TYPE_MAP.get(trade, trade)

    def _set_region_articles(self):
        self.total_cnt = len(self.region or [])
        self.log_signal_func(f"전체 지역 수 {self.total_cnt} 개")

        for loc in self.region or []:
            if not self.running:
                break

            d = self._find_location_detail(loc.get("시도"), loc.get("시군구"), loc.get("읍면동"))
            if d:
                self.detail_region_article_list.append(d)
            else:
                self.log_signal_func(f"[WARN] 지역 매핑 실패: {loc}")

    def _find_location_detail(self, sido, sigungu, eupmyeondong):
        for item in self.naver_loc_all_real_detail:
            if sido == item.get("시도") and sigungu == item.get("시군구") and eupmyeondong == item.get("읍면동"):
                return item
        return None

    def _crawl_article_list(self, article):
        url = _s((article or {}).get("articleList"))
        if not url:
            self.log_signal_func("[WARN] articleList 없음")
            return

        rlet_list, trad_list = self._pick_detail_codes()
        rlet_joined = self._join_codes(rlet_list)
        trad_joined = self._join_codes(trad_list)

        self.search_rlet_labels = [self.RLET_TYPE_MAP.get(c, c) for c in rlet_list]
        self.search_trade_labels = [self.TRADE_TYPE_MAP.get(c, c) for c in trad_list]

        if rlet_joined:
            url = self._replace_query_params(url, rletTpCd=rlet_joined)
        if trad_joined:
            url = self._replace_query_params(url, tradTpCd=trad_joined)

        page = 1
        seen = set()

        while True:
            if not self.running:
                break

            req_url = self._replace_query_params(url, page=str(page))
            self.log_signal_func(f"page={page} url={req_url}")

            try:
                resp = self.api_client.get(req_url, headers=self.headers)
            except Exception as e:
                self.log_signal_func(f"[ERROR] 목록 요청 실패: {e}")
                break

            time.sleep(random.uniform(1, 2))

            body = _as_list((resp or {}).get("body"))
            if not body:
                break

            atcl_nos = []
            for r in body:
                no = _s(r.get("atclNo"))
                if no and no not in seen:
                    seen.add(no)
                    atcl_nos.append(no)

            for i, atcl_no in enumerate(atcl_nos, start=1):
                if not self.running:
                    break
                try:
                    self._crawl_same_addr(atcl_no, article)
                    self.log_signal_func(f"[atcl] {i}/{len(atcl_nos)} atclNo={atcl_no}")
                except Exception as e:
                    self.log_signal_func(f"[ERROR] atclNo={atcl_no} 처리 중 오류: {e}")

            if not (resp or {}).get("more"):
                break

            page += 1

    def _crawl_same_addr(self, atcl_no, article):
        url = f"{self.same_addr_article_url}?articleNo={_s(atcl_no)}"

        try:
            rows = self.api_client.get(url, headers=self.headers)
        except Exception as e:
            self.log_signal_func(f"[ERROR] same-addr 요청 실패: {e}")
            return

        time.sleep(random.uniform(1, 2))

        rows = _as_list(rows)
        if not rows:
            return

        first = _as_dict(rows[0])

        atcl_list = []
        for r in rows:
            d = _as_dict(r)
            n = _s(d.get("atclNo"))
            if n:
                atcl_list.append(n)

        out_rows = []
        for idx, same_no in enumerate(atcl_list, start=1):
            if not self.running:
                break

            detail_url = f"{self.fin_land_article_url}/{same_no}"
            self.log_signal_func(f"{same_no} {_s(first.get('atclNm'))} {_s(first.get('bildNm'))} {idx}/{len(atcl_list)}")

            data = self._fetch_detail(detail_url, first, same_no, article)
            time.sleep(random.uniform(1, 2))

            if isinstance(data, dict) and data:
                out_rows.append(data)

        if out_rows:
            self.result_data_list.append(out_rows)
            self.excel_driver.append_to_csv(self.csv_filename, out_rows, self.columns or [])

    def _fetch_detail(self, url, parent, article_number, article):
        try:
            self.driver.get(url)
        except Exception as e:
            self.log_signal_func(f"[ERROR] 드라이버 이동 실패: {e}")
            return {}

        self._wait_ready_state_complete(7)

        html = self.driver.page_source

        payload_text = self._collect_next_f_payload_text(html)
        if not payload_text:
            return {}

        dehydrated = self._extract_dehydrated_state(payload_text)
        if not dehydrated:
            return {}

        queries = _as_list(_as_dict(dehydrated).get("queries", []))

        results_by_key = {}
        for q in queries:
            q = _as_dict(q)
            qk_list = _as_list(q.get("queryKey"))
            qk0 = qk_list[0] if qk_list else None

            st = _as_dict(q.get("state"))
            dt = _as_dict(st.get("data"))

            if dt.get("isSuccess") is True and qk0:
                results_by_key[qk0] = dt.get("result")

        parts = [_s((article or {}).get("시도")), _s((article or {}).get("시군구")), _s((article or {}).get("읍면동"))]

        result_data = {
            "게시번호": _s(article_number),
            "URL": _s(url),
            "상위매물명": _s((parent or {}).get("atclNm")),
            "상위매물동": _s((parent or {}).get("bildNm")),
            "상위매물게시번호": _s((parent or {}).get("atclNo")),
            "검색주소": " ".join([p for p in parts if p]),
        }

        try:
            self.get_article_agent(result_data, results_by_key)
        except Exception as e:
            self.log_signal_func(f"[WARN] agent 실패: {e}")

        try:
            self.get_complex(result_data, results_by_key)
        except Exception as e:
            self.log_signal_func(f"[WARN] complex 실패: {e}")

        try:
            self.get_basic_info(result_data, results_by_key)
        except Exception as e:
            self.log_signal_func(f"[WARN] basicInfo 실패: {e}")

        try:
            self.get_article_key(result_data, results_by_key)
        except Exception as e:
            self.log_signal_func(f"[WARN] articleKey 실패: {e}")

        if self.search_rlet_labels and result_data.get("매물유형") not in self.search_rlet_labels:
            return {}

        if self.search_trade_labels and result_data.get("거래유형") not in self.search_trade_labels:
            return {}

        if self.search_rlet_labels:
            result_data["검색 매물유형"] = ", ".join(self.search_rlet_labels)
        if self.search_trade_labels:
            result_data["검색 거래유형"] = ", ".join(self.search_trade_labels)

        floor_text = self._parse_floor_text_from_dom(html)
        if floor_text:
            result_data["층정보"] = floor_text

        self._fill_address_from_results(result_data, results_by_key)
        self.log_signal_func(f"상세 데이터 : {result_data}")
        return result_data

    def _wait_ready_state_complete(self, timeout_sec=7):
        try:
            WebDriverWait(self.driver, timeout_sec).until(self._is_ready_state_complete)
        except TimeoutException:
            self.log_signal_func("[WARN] readyState complete 타임아웃")

    def _is_ready_state_complete(self, driver):
        try:
            return driver.execute_script("return document.readyState") == "complete"
        except Exception:
            return False

    def _parse_floor_text_from_dom(self, html: str) -> str:
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")
        for li in soup.select("li"):
            term = li.select_one("div[class*='term']")
            if not term:
                continue
            if term.get_text(strip=True) != "층":
                continue

            defin = li.select_one("div[class*='definition']")
            return defin.get_text(" ", strip=True) if defin else ""

        return ""

    def _collect_next_f_payload_text(self, html: str) -> str:
        pattern = r"self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)\s*;?"
        chunks = re.findall(pattern, html, flags=re.DOTALL)
        if not chunks:
            return ""

        decoded_list = []
        for raw in chunks:
            try:
                decoded_list.append(json.loads(f"\"{raw}\""))
            except Exception:
                decoded_list.append(raw.replace(r"\n", "\n"))

        return "\n".join(decoded_list)

    def _extract_dehydrated_state(self, text: str) -> dict:
        key = '"state":'
        idx = text.find(key)
        if idx < 0:
            return {}

        start = text.find("{", idx + len(key))
        if start < 0:
            return {}

        json_str = self._extract_balanced_braces(text, start)
        if not json_str:
            return {}

        try:
            return json.loads(json_str)
        except Exception as e:
            self.log_signal_func(f"[WARN] state json 파싱 실패: {e}")
            return {}

    def _extract_balanced_braces(self, s: str, start_idx: int) -> str:
        if start_idx < 0 or start_idx >= len(s) or s[start_idx] != "{":
            return ""

        depth = 0
        in_str = False
        esc = False

        for i in range(start_idx, len(s)):
            ch = s[i]

            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue

            if ch == '"':
                in_str = True
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start_idx:i + 1]

        return ""

    def _fill_address_from_results(self, result_data: dict, results_by_key: dict):
        basic = _as_dict(results_by_key.get("GET /article/basicInfo") or {})
        addr = _as_dict(basic.get("address"))

        if not _s(result_data.get("시도")):
            result_data["시도"] = _s(addr.get("cityName") or addr.get("sido") or "")
        if not _s(result_data.get("시군구")):
            result_data["시군구"] = _s(addr.get("divisionName") or addr.get("sigungu") or "")
        if not _s(result_data.get("읍면동")):
            result_data["읍면동"] = _s(addr.get("sectorName") or addr.get("eupmyeondong") or "")

        if not _s(result_data.get("전체주소")):
            legal_info = results_by_key.get("GET /legalDivision/infoList")
            if isinstance(legal_info, dict) and legal_info:
                first = next(iter(legal_info.values()), {})
                first = _as_dict(first)
                result_data["전체주소"] = _s(first.get("fullAddress") or first.get("regionName") or "")

    def _join_codes(self, values):
        values = _as_list(values)
        if not values:
            return ""

        seen = set()
        out = []
        for v in values:
            v = str(v).strip()
            if v and v not in seen:
                seen.add(v)
                out.append(v)
        return ":".join(out)

    def _pick_detail_codes(self):
        rows = _as_list(getattr(self, "setting_detail", None))
        rlet = []
        trad = []

        for row in rows:
            d = _as_dict(row)
            if d.get("checked") is not True:
                continue

            t = _s(d.get("type"))
            code = _s(d.get("code"))
            if not code:
                continue

            if t == "rlet_types":
                rlet.append(code)
            elif t == "trade_types":
                trad.append(code)

        return rlet, trad

    def _replace_query_params(self, url, **repl):
        p = urlparse(url)
        q = dict(parse_qsl(p.query, keep_blank_values=True))

        for k, v in repl.items():
            if v is None or v == "":
                continue
            q[k] = v

        new_query = urlencode(q, doseq=True, safe="")
        return urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))
