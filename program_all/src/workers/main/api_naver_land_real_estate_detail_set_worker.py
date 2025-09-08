import json
import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.type_utils import _as_dict, _as_list, _s, ensure_list_attr

from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


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

        # 매물/거래 코드
        self.RLET_TYPE_MAP = {
            "A01": "아파트", "A02": "오피스텔", "C02": "빌라",
            "B01": "아파트 분양권", "B02": "오피스텔분양권",
            "A04": "재건축", "C04": "전원주택", "C03": "단독/다가구",
            "D05": "상가주택", "C06": "한옥주택", "F01": "재개발",
            "C01": "원룸", "D02": "상가", "D01": "사무실",
            "E02": "공장/창고", "D03": "건물", "E03": "토지", "E04": "지식산업센터", "D04": "상가건물", "Z00": "기타"
        }
        self.TRADE_TYPE_MAP = {"A1": "매매", "B1": "전세", "B2": "월세", "B3": "단기임대"}

    # ========== 초기화/종료 ==========
    def init(self):
        ensure_list_attr(self, "region")
        ensure_list_attr(self, "columns")  # ← columns도 보장
        self.driver_set(False)
        self.log_signal_func(f"선택 항목 : {self.columns}")
        return True


    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(2)
        # 드라이버 정리
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            self.log_signal_func(f"[WARN] 드라이버 종료 실패: {e}")
        self.log_signal_func("=============== 크롤링 종료")
        if self.running:
            self.progress_end_signal.emit()

    def stop(self):
        self.running = False

    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)
        self.driver = self.selenium_driver.start_driver(1200)

    # ========== 실행 ==========
    def main(self):
        self.log_signal_func("시작합니다.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)

        df = pd.DataFrame(columns=self.columns or [])
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

        self.naver_loc_all_real_detail = self.file_driver.read_json_array_from_resources("naver_real_estate_data.json")
        self.loc_all_detail_list_set()

        for index, article in enumerate(self.detail_region_article_list, start=1):
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            self.fetch_same_article_detail_list_by_article(article)

            self.log_signal_func(f"진행 ({index} / {self.total_cnt}) ==============================")
            pro_value = (index / max(self.total_cnt, 1)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

        try:
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
        except Exception as e:
            self.log_signal_func(f"[WARN] 엑셀 변환 실패: {e}")

        return True

    # ========== 유틸 ==========

    
    # 지역에 맞는 데이터 매핑
    def find_location_detail(self, sido, sigungu, eupmyeondong):
        for item in self.naver_loc_all_real_detail:
            if sido == item.get("시도") and sigungu == item.get("시군구") and eupmyeondong == item.get("읍면동"):
                return item
        return None

    # 지역 데이터 세팅
    def loc_all_detail_list_set(self):
        self.total_cnt = len(self.region or [])
        self.log_signal_func(f"전체 지역 수 {self.total_cnt} 개")
        for loc in self.region or []:
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            d = self.find_location_detail(loc.get("시도"), loc.get("시군구"), loc.get("읍면동"))
            if d:
                self.detail_region_article_list.append(d)
            else:
                self.log_signal_func(f"[WARN] 지역 매핑 실패: {loc}")

    # ========== 목록/동일주소 ==========
    def fetch_same_article_detail_list_by_article(self, article):
        """
        - 페이지를 순회하며 atclNo만 모은 뒤(중복 제거), while 루프 종료 후 일괄 처리
        - 처리 순서는 '처음 등장한 순서'를 보장
        """
        url = _s((article or {}).get("articleList"))
        if not url:
            self.log_signal_func("[WARN] article['articleList'] 없음, 스킵")
            return

        page = 1
        # 순서를 유지하며 중복 제거를 위한 자료구조
        unique_atcl_nos = []
        seen = set()

        while True:
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            try:
                self.log_signal_func(f"page : {page}, url : {url}&page={page}")
                resp = self.api_client.get(url, headers=self.headers, params={"page": page})
            except Exception as e:
                self.log_signal_func(f"[ERROR] 목록 요청 실패: {e}")
                # 지금까지 모은 것만으로 후처리 진행
                break

            time.sleep(random.uniform(1, 2))
            body = _as_list((resp or {}).get("body"))
            if not body:
                self.log_signal_func(f"[STOP] page={page} 결과 없음")
                break

            # 이번 페이지에서 atclNo 수집 + 중복 제거
            deduped_page_atcl_nos = []
            for r in body:
                no = _s(r.get("atclNo"))
                if no and no not in seen:
                    seen.add(no)
                    unique_atcl_nos.append(no)
                    deduped_page_atcl_nos.append(no)

            self.log_signal_func(
                f"[COLLECT] page={page}, 매물 번호 수집 - 이번페이지={len(deduped_page_atcl_nos)}, 누계={len(unique_atcl_nos)}"
            )

            # ──────────────── 상세 조회 ────────────────
            for idx, s in enumerate(deduped_page_atcl_nos, start=1):
                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                try:
                    self.get_same_addr_article(s, article)
                    self.log_signal_func(f"[atcl] {idx}/{len(deduped_page_atcl_nos)} [{len(unique_atcl_nos)}] atclNo={s}")
                except Exception as e:
                    self.log_signal_func(f"[ERROR] atclNo={s} 처리 중 오류: {e}")
            self.log_signal_func("[PROCESS] atclNo 처리 완료")

            # 다음 페이지 여부 판단
            if not (resp or {}).get("more"):
                self.log_signal_func(f"[DONE] more=False, last_page={page}")
                break
            page += 1


    def get_same_addr_article(self, atcl_no, article):
        url = f"{self.same_addr_article_url}?articleNo={_s(atcl_no)}"
        try:
            rows = self.api_client.get(url, headers=self.headers)
        except Exception as e:
            self.log_signal_func(f"[ERROR] same-addr 요청 실패: {e}")
            return
        time.sleep(random.uniform(1, 2))

        rows = _as_list(rows)
        if not rows:
            self.log_signal_func(f"[same-addr] base={atcl_no} 결과 없음")
            return

        first = _as_dict(rows[0])
        atcl_list = []
        for r in rows:
            d = _as_dict(r)
            n = _s(d.get("atclNo"))
            if n:
                atcl_list.append(n)

        result_list = []
        for idx, same_no in enumerate(atcl_list, start=1):
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            self.log_signal_func(f"{same_no} {_s(first.get('atclNm'))} {_s(first.get('bildNm'))} : {idx}/{len(atcl_list)}")
            detail_url = f"{self.fin_land_article_url}/{same_no}"
            data = self.fetch_fin_land_detail_data(detail_url, first, same_no, article)
            time.sleep(random.uniform(1, 2))
            if isinstance(data, dict) and data:
                result_list.append(data)

        if result_list:
            self.result_data_list.append(result_list)
            self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns or [])


    def is_error_page(self, soup):
        """
        네이버 부동산 오류 페이지(404 등) 여부 판정
        - class 이름 뒤 해시 값은 변경 가능성이 있으므로 'Error_article' 포함 여부로만 체크
        """
        err_div = soup.select_one("div[class*='Error_article']")
        if err_div:
            title = err_div.find("h2")
            if title and "요청하신 페이지를 찾을 수 없어요" in title.get_text(strip=True):
                return True
        return False


    # ========== 상세 ==========
    def extract_addr(self, s):
        ns = s.select('div[class^="ArticleComplexInfo_area-data"]')
        if not ns:
            return ""
        node = ns[1] if len(ns) > 1 else ns[0]
        return ("".join(node.find_all(string=True, recursive=False))).strip()


    def fetch_fin_land_detail_data(self, url, parent, article_number, article):
        try:
            self.driver.get(url)
        except Exception as e:
            self.log_signal_func(f"[ERROR] 드라이버 이동 실패: {e}")
            return {}

        # 1) 문서 로드 완료(느릴 수 있으니 타임아웃 완만하게)
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            self.log_signal_func("[WARN] document.readyState='complete' 대기 타임아웃 — 계속 진행")


        # 2) 주소 블록 등장 대기 (없으면 넘어감)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class^="ArticleComplexInfo_area"]'))
            )
        except TimeoutException:
            self.log_signal_func("[INFO] 주소 요소 미등장 — 주소 파싱은 스킵하고 다음 단계 진행")


        # 3. 파싱
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        if self.is_error_page(soup):
            self.log_signal_func(f"[INFO] url={url} 오류 페이지 — 스킵")
            result_data = {
                "게시번호": _s(article_number),
                "URL": _s(url),
                "결과": 'Fail',
                "에러로그": "오류 페이지 — 스킵"
            }
            return result_data

        full_addr = self.extract_addr(soup)

        data_obj = None
        tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
        if tag and tag.string:
            try:
                data_obj = json.loads(tag.string)
            except Exception:
                data_obj = None

        if data_obj is None:
            m = re.search(r'<script\s+id=["\']__NEXT_DATA__["\']\s+type=["\']application/json["\'][^>]*>(\{.*?\})</script>',
                          html, flags=re.DOTALL | re.IGNORECASE)
            if m:
                try:
                    data_obj = json.loads(m.group(1))
                except Exception:
                    self.log_signal_func(f"[detail] json 파싱 에러")
                    data_obj = None

        if not isinstance(data_obj, dict):
            self.log_signal_func(f"[detail] url={url}, __NEXT_DATA__ 없음/파싱 실패")
            return {}

        queries = _as_list(
            _as_dict(_as_dict(data_obj.get("props")).get("pageProps"))
            .get("dehydratedState", {})
            .get("queries", [])
        )

        results_by_key = {}
        for q in queries:
            qk = (_as_list(_as_dict(q).get("queryKey")) or [None])[0]
            st = _as_dict(_as_dict(q).get("state"))
            dt = _as_dict(st.get("data"))
            if dt.get("isSuccess") is True and qk:
                results_by_key[qk] = dt.get("result")

        parts = [_s((article or {}).get("시도")), _s((article or {}).get("시군구")), _s((article or {}).get("읍면동"))]
        result_data = {
            "게시번호": _s(article_number),
            "URL": _s(url),
            "상위매물명": _s(parent.get("atclNm")),
            "상위매물동": _s(parent.get("bildNm")),
            "상위매물게시번호": _s(parent.get("atclNo")),
            "검색 주소": " ".join([p for p in parts if p]),
            "전체 주소": _s(full_addr),
        }

        self.get_article_agent(result_data, results_by_key)
        self.get_complex(result_data, results_by_key)
        self.get_basic_info(result_data, results_by_key)
        self.get_article_key(result_data, results_by_key)
        
        full = _s(result_data.get("전체 주소"))
        if full:
            parts = full.split()
        
            # 시도 / 시군구 / 읍면동은 비어있을 때만 채움
            if len(parts) >= 1 and not _s(result_data.get("시도")):
                result_data["시도"] = parts[0]
            if len(parts) >= 2 and not _s(result_data.get("시군구")):
                result_data["시군구"] = parts[1]
            if len(parts) >= 3 and not _s(result_data.get("읍면동")):
                result_data["읍면동"] = parts[2]


        self.log_signal_func(f"상세 데이터 : {result_data}")
        return result_data

    # ========== 파트 파서 ==========
    def get_basic_info(self, out_obj, results_by_key):
        basic = _as_dict(results_by_key.get("GET /article/basicInfo"))
        if not basic:
            self.log_signal_func("[detail] basicInfo 없음/타입불일치")
            return

        priceInfo = _as_dict(basic.get("priceInfo"))
        communal = _as_dict(basic.get("communalComplexInfo"))
        detailInfo = _as_dict(basic.get("detailInfo"))
        sizeInfo = _as_dict(basic.get("sizeInfo") or _as_dict(detailInfo.get("sizeInfo")))

        out_obj["단지명"] = _s(communal.get("complexName"))
        out_obj["동이름"] = _s(communal.get("dongName"))

        if not out_obj.get("단지명"):
            ad = _as_dict(detailInfo.get("articleDetailInfo"))
            nm = _s(ad.get("articleName"))
            if nm:
                out_obj["단지명"] = nm

        out_obj["매매가"] = _s(priceInfo.get("price"))
        out_obj["보증금"] = _s(priceInfo.get("warrantyAmount"))
        out_obj["월세"] = _s(priceInfo.get("rentAmount"))
        out_obj["공급면적"] = _s(sizeInfo.get("supplySpace"))
        out_obj["평수"] = _s(sizeInfo.get("pyeongArea"))
        out_obj["대지면적"] = _s(sizeInfo.get("landSpace"))
        out_obj["연면적"] = _s(sizeInfo.get("floorSpace"))
        out_obj["건축면적"] = _s(sizeInfo.get("buildingSpace"))
        out_obj["전용면적"] = _s(sizeInfo.get("exclusiveSpace"))


    def get_complex(self, out_obj, results_by_key):
        comp = _as_dict(results_by_key.get("GET /complex"))
        if not comp:
            self.log_signal_func("[detail] complex 없음/타입불일치")
            return

        addr = _as_dict(comp.get("address"))
        out_obj["시도"] = _s(addr.get("city"))
        out_obj["시군구"] = _s(addr.get("division"))
        out_obj["읍면동"] = _s(addr.get("sector"))
        out_obj["번지"] = _s(addr.get("jibun"))
        out_obj["도로명 주소"] = _s(addr.get("roadName"))
        out_obj["우편번호"] = _s(addr.get("zipCode"))


    def get_article_agent(self, out_obj, results_by_key):
        agent = _as_dict(results_by_key.get("GET /article/agent"))
        if not agent:
            self.log_signal_func("[detail] agent 없음/타입불일치")
            return

        phone = _as_dict(agent.get("phone"))
        out_obj["중개사무소 이름"] = _s(agent.get("brokerageName"))
        out_obj["중개사 이름"] = _s(agent.get("brokerName"))
        out_obj["중개사무소 주소"] = _s(agent.get("address"))
        out_obj["중개사무소 번호"] = _s(phone.get("brokerage"))
        out_obj["중개사 핸드폰번호"] = _s(phone.get("mobile"))

    def get_article_key(self, out_obj, results_by_key):
        entry = _as_dict(results_by_key.get("GET /article/key"))
        if not entry:
            self.log_signal_func("[detail] key 없음/타입불일치: GET /article/key")
            return

        addr = _as_dict(entry.get("address") or _as_dict(entry.get("result")).get("address"))
        jibun = _s(addr.get("jibun"))
        if not _s(out_obj.get("번지")):
            out_obj["번지"] = jibun

        t = _as_dict(entry.get("type") or _as_dict(entry.get("result")).get("type"))
        rlet = _s(t.get("realEstateType"))
        trade = _s(t.get("tradeType"))

        if rlet:
            out_obj["매물 유형"] = self.RLET_TYPE_MAP.get(rlet, rlet)
        if trade:
            out_obj["거래 유형"] = self.TRADE_TYPE_MAP.get(trade, trade)

    # ========== 코드 라벨러 ==========
    def rlet_label(self, code):
        return self.RLET_TYPE_MAP.get(_s(code), code)

    def trade_label(self, code):
        return self.TRADE_TYPE_MAP.get(_s(code), code)
