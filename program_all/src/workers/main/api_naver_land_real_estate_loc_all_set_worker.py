import json
import random
import re
import threading
import time
from urllib.parse import urlparse, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

from src.utils.config import NAVER_LOC_ALL
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url  # 서버 URL 및 설정 정보
from src.utils.chrome_macro import ChromeMacro

class ApiNaverLandRealEstateLocAllSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()

        self.current_cnt = 0
        self.total_cnt = 0
        self.driver = None
        self.columns = None
        self.excel_filename = None
        self.keyword_list = None
        self.site_name = "네이버 부동산 공인중개사 번호"
        self.before_pro_value = 0
        self.file_driver = None
        self.complex_result_list = []
        self.article_result_list = []
        self.real_state_result_list = []
        self.excel_driver = None
        self.selenium_driver = None
        self.loc_all = NAVER_LOC_ALL
        self.chrome_macro = None
        self.seen_numbers: set = set()  # complexNumber 전역 중복 방지

    # 초기화
    def init(self):
        keyword_str = self.get_setting_value(self.setting, "keyword")
        self.keyword_list = split_comma_keywords(keyword_str)
        self.driver_set(False)
        self.log_signal_func(f"선택 항목 : {self.columns}")
        return True

    # 프로그램 실행
    def main(self):
        self.seen_numbers.clear()  # ✅ 실행마다 초기화
        self.log_signal_func("시작합니다.")
        self.excel_filename = self.file_driver.get_excel_filename(self.site_name)
        df = pd.DataFrame(columns=self.columns)
        df.to_excel(self.excel_filename, index=False)  # 인코딩 인자 제거
        self.loc_all_keyword_list()
        for index, cmplx in enumerate(self.complex_result_list, start=1):
            self.log_signal_func(f"데이터 {index}: {cmplx}")
            self.fetch_article_by_complex(cmplx)

        for ix, article in enumerate(self.article_result_list, start=1):
            self.fetch_article_detail_by_article(article)


         # 전역 누적

        return True


    # 전국 키워드 조회
    def loc_all_keyword_list(self):
        loc_all_len = len(self.region)
        keyword_list_len = len(self.keyword_list)

        if keyword_list_len:
            self.total_cnt = loc_all_len * keyword_list_len
        else:
            self.total_cnt = loc_all_len

        self.log_signal_func(f"전체 수 {self.total_cnt} 개")

        for index, loc in enumerate(self.region, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            name = f'{loc["시도"]} {loc["시군구"]} {loc["읍면동"]} '

            if self.keyword_list:
                for idx, query in enumerate(self.keyword_list, start=1):
                    if not self.running:  # 실행 상태 확인
                        self.log_signal_func("크롤링이 중지되었습니다.")
                        break
                    full_name = name + query
                    self.log_signal_func(f"전국: {index} / {loc_all_len}, 키워드: {idx} / {keyword_list_len}, 검색어: {full_name}")
                    self.fetch_complex(full_name)
                    self.set_pro_value()
            else:
                self.log_signal_func(f"전국: {index} / {loc_all_len}, 검색어: {name}")
                self.fetch_complex(name)
                self.set_pro_value()


    def set_pro_value(self):
        self.current_cnt = self.current_cnt + 1
        pro_value = (self.current_cnt / self.total_cnt) * 1000000
        self.progress_signal.emit(self.before_pro_value, pro_value)
        self.before_pro_value = pro_value


    def wait_ready(self, timeout_sec: float = 5.0) -> None:
        end = time.time() + timeout_sec
        while time.time() < end:
            try:
                state = self.driver.execute_script("return document.readyState")
                if state == "complete":
                    return
            except Exception:
                pass
            time.sleep(0.05)


    def fetch_complex(self, kw: str) -> None:
        """
        네이버 금융 부동산 '자동완성 단지' API를 키워드 배열로 순회하며
        page=1..N을 돌고, 데이터가 없을 때 다음 키워드로 넘어가며,
        모든 결과를 하나의 리스트로 통합해 반환한다.

        - 전역 중복 제거 기준: item[complexNumber]
        - 각 아이템에는 _meta = {keyword, page} 를 부가한다.
        """

        self.driver.get(self.build_search_url(kw))
        self.wait_ready()         # ✅ 추가
        time.sleep(0.15)           # 쿠키/토큰 안정화 짧은 유예

        page = 1
        size = 10
        page_count = 0
        while True:

            api_url = self.build_api_url(kw, size=size, page=page)

            # API 호출
            data = self.execute_fetch(api_url)

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
                raw_num = it.get("complexNumber")
                num = str(raw_num) if raw_num is not None else None  # ✅ 통일

                if num is not None:
                    if num in self.seen_numbers:
                        continue
                    self.seen_numbers.add(num)

                # 추적 메타
                it.setdefault("_meta", {})
                it["_meta"].update({"keyword": kw, "page": page})

                self.complex_result_list.append(it)
                new_count += 1
                page_count += 1

            tc = result.get("totalCount")
            self.log_signal_func(f"    · 수집: {page_count}건 / totalCount={tc}, 누적={len(self.complex_result_list)}")

            page += 1
            time.sleep(0.35)


    def build_search_url(self, keyword: str) -> str:
        """
        네이버 금융 부동산 검색 페이지(동일 출처 확보용).
        Same-Origin + credentials 포함 fetch가 가능하도록 먼저 이 페이지를 연다.
        """
        # "https://fin.land.naver.com/search?q=<encoded>"
        return "https://fin.land.naver.com/search?q=" + urlencode({"q": keyword})[2:]


    def execute_fetch(self, api_url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
        js = r"""
            const url = arguments[0];
            const timeoutMs = arguments[1];
            const done = arguments[2];
    
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), timeoutMs);
    
            fetch(url, {
                method: "GET",
                credentials: "include",
                headers: {
                    "Accept": "application/json, text/plain, */*"
                },
                signal: controller.signal
            })
            .then(r => r.json())
            .then(data => done({ ok: true, data }))
            .catch(err => done({ ok: false, error: String(err) }))
            .finally(() => clearTimeout(timer));
        """
        result = self.driver.execute_async_script(js, api_url, timeout_ms)
        if not isinstance(result, dict) or not result.get("ok"):
            return {}
        data = result.get("data") or {}
        return data if isinstance(data, dict) else {}


    def build_api_url(self, keyword: str, size: int, page: int) -> str:
        """
        자동완성 단지 API URL 생성.
        예) https://fin.land.naver.com/front-api/v1/search/autocomplete/complexes?keyword=...&size=...&page=...
        """
        params = {"keyword": keyword, "size": str(size), "page": str(page)}
        return "https://fin.land.naver.com/front-api/v1/search/autocomplete/complexes?" + urlencode(params)


    def fetch_article_by_complex(self, row: Dict[str, Any]) -> None:
        cn = row.get("complexNumber")
        if cn is None:
            return

        # ✅ 핵심 수정: complexNumber를 문자열로 강제
        complex_number = str(cn)
        complex_name = row.get("complexName") or row.get("name")

        html_url_tpl = "https://fin.land.naver.com/complexes/{complexNumber}?tab=article"
        api_url = "https://fin.land.naver.com/front-api/v1/complex/article/list"
    
        default_payload_base = {
            "tradeTypes": [],
            "pyeongTypes": [],
            "dongNumbers": [],
            "userChannelType": "PC",
            "articleSortType": "RANKING_DESC",
            "seed": "",
            "lastInfo": [],   # 단지별 첫 호출 시 반드시 []로 초기화
            "size": 100,
        }

        # Same-Origin 컨텍스트 확보
        html_url = html_url_tpl.format(complexNumber=complex_number)
        self.driver.get(html_url)
        self.wait_ready()          # 페이지 로드 대기
        time.sleep(0.15)             # 토큰/쿠키 세팅 여유

        # 단지별 최초 payload (lastInfo는 반드시 빈 배열)
        payload = dict(default_payload_base)
        payload["complexNumber"] = complex_number
        payload["size"] = 100
        payload["lastInfo"] = []     # ⭐ 단지마다 리셋

        page = 1
        while True:
            data = self.execute_post_json(api_url, payload)

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
                rep = it.get("representativeArticleInfo") or {}

                new_item = {
                    "_meta": {
                        "complexNumber": str(complex_number),
                        "complexName": complex_name,
                        "page": page,
                    },
                    "representativeArticleInfo": rep,
                }

                # 안전 로그 (키 없을 때도 에러 안 나게)
                art_no = rep.get("articleNumber") or rep.get("id")
                self.log_signal_func(f"articleNumber={art_no}")

                self.article_result_list.append(new_item)

            # 페이지네이션 플래그는 기존 그대로
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
                time.sleep(0.25)
                continue

            break

        time.sleep(0.25)


    def execute_post_json(self, url: str, body: Dict[str, Any], timeout_ms: int = 15000) -> Dict[str, Any]:
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
        result = self.driver.execute_async_script(js, url, body, timeout_ms)
        if not isinstance(result, dict) or not result.get("ok"):
            raise RuntimeError(f"fetch error: {result.get('error') if isinstance(result, dict) else result}")
        data = result.get("data") or {}
        if not isinstance(data, dict):
            raise RuntimeError("Invalid JSON response")
        return data


    def parse_next_queries_results(self, html: str) -> list[dict]:
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
        results: list[dict] = []

        for q in queries:
            try:
                st = (q or {}).get("state", {})
                dt = (st or {}).get("data", {})
                if dt.get("isSuccess") is True and isinstance(dt.get("result"), dict):
                    results.append(dt["result"])  # 그대로 수집
            except Exception:
                # 한 항목 파싱 실패는 건너뜀
                continue

        return results


    def is_target_broker_result(self, obj: Dict[str, Any]) -> bool:
        """
        우리가 원하는 '중개사 정보' 스키마를 만족하는 result 인지 검사.
        - result 딕셔너리 내부에 required_result_keys 모두 존재
        - result['phone']는 dict 이고 REQUIRED_PHONE_KEYS 모두 존재
        """
        if not isinstance(obj, dict):
            return False

        required_result_keys = {
            "brokerageName",
            "brokerName",
            "address",
            "businessRegistrationNumber",
            "profileImageUrl",
            "brokerId",
            "ownerConfirmationSaleCount",
            "phone",
        }

        required_phone_keys = {"brokerage", "mobile"}

        # 1) 1차 키 존재 여부
        if not required_result_keys.issubset(obj.keys()):
            return False

        # 2) phone 구조 검사
        phone = obj.get("phone")
        if not isinstance(phone, dict):
            return False
        if not required_phone_keys.issubset(phone.keys()):
            return False

        # (선택) 타입 검증이 필요하면 아래 주석 해제해서 더 엄격히 체크 가능
        # if not isinstance(obj["brokerageName"], str): return False
        # if not isinstance(obj["ownerConfirmationSaleCount"], (int, float)): return False
        # if not isinstance(phone["brokerage"], str) or not isinstance(phone["mobile"], str): return False

        return True


    def parse_target_broker_results(self, html: str) -> List[Dict[str, Any]]:
        """
        HTML에서 __NEXT_DATA__ → dehydratedState.queries[*].state.data.result 들을 얻고,
        그 중 _is_target_broker_result 를 만족하는 것만 반환.
        (이 함수는 'parse_next_queries_results'가 이미 존재한다고 가정하고 재사용)
        """
        all_results = self.parse_next_queries_results(html)  # 이전 단계에서 만든 함수 재사용
        return [r for r in all_results if self.is_target_broker_result(r)]


    def fetch_article_detail_by_article(self, article):
        article_url = "https://fin.land.naver.com/articles/"

        rep = (article or {}).get("representativeArticleInfo") or {}
        article_number = rep.get("articleNumber") or rep.get("id")
        if not article_number:
            self.log_signal_func("[경고] articleNumber가 없어 상세 조회를 건너뜁니다.")
            return

        # 1) 새 탭으로 열고(첫 건은 기존 탭 없음 → False), 이전 탭 닫기(둘째부터 True)
        url = f"{article_url}{article_number}"
        self.chrome_macro.open_url(url, replace_previous=True)
        time.sleep(0.6)  # 환경에 따라 조절 (0.5~1.2)

        # 2) 현재 탭(=방금 연 컨텐츠 탭)의 원본 HTML 소스 가져오기
        html = self.chrome_macro.copy_page_html_via_view_source()

        # 3) __NEXT_DATA__에서 result 배열만 추출
        real_states = self.parse_target_broker_results(html)  # 원하는 스키마만 필터링
        for ix, rs in enumerate(real_states, start=1):
            self.log_signal_func(f"rs({ix}): {rs}")

        self.real_state_result_list.extend(real_states)

    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)

        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)

        self.chrome_macro = ChromeMacro(default_settle=1.0)


    # 마무리
    def destroy(self):

        # 엑셀 후처리 및 진행률 마무리
        self.excel_driver.save_obj_list_to_excel(
            self.excel_filename,
            self.real_state_result_list,
            columns=self.columns
        )

        # 크롬 정리 (선택)
        try:
            if getattr(self, "chrome_macro", None):
                self.chrome_macro.close_all()
        except Exception as e:
            self.log_signal_func(f"[경고] 크롬 종료 중 예외: {e}")


        # 드라이버 먼저 닫기 (가능하면)
        try:
            if getattr(self, "driver", None):
                self.driver.quit()
        except Exception as e:
            self.log_signal_func(f"[경고] 드라이버 종료 중 예외: {e}")

        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        if self.running:
            self.progress_end_signal.emit()

    # 정지
    def stop(self):
        self.running = False

