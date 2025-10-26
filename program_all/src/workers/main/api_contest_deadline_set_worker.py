import json
import re
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
from bs4 import BeautifulSoup

from src.utils.api_utils import APIClient
from src.utils.file_utils import FileUtils
from src.utils.excel_utils import ExcelUtils
from src.utils.time_utils import parse_yy_mm_dd, parse_date_yyyy_mm_dd, parse_finish_dt
from src.workers.api_base_worker import BaseApiWorker
from difflib import SequenceMatcher  # [ADD]

class ApiContestDealineSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()
        self.excel_filename: Optional[str] = None
        self.site_name = "공모전 마감"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver: Optional[FileUtils] = None
        self.excel_driver: Optional[ExcelUtils] = None
        self.api_client: Optional[APIClient] = None
        self.result_list: List[Dict[str, Any]] = []

        self.dup = True

        # ── WEVITY ───────────────────────────────────────────────────────────────
        self.WEVITY_BASE = "https://www.wevity.com/"
        self.WEVITY_HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        }
        self.WEVITY_LIST_TPL = self.WEVITY_BASE + "?c=find&s=1&mode=soon&gub=1&gp={gp}"

        # [ADD] ALL-CON 상수
        self.ALLCON_URL = "https://www.all-con.co.kr/page/ajax.contest_list.php"
        self.ALLCON_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.all-con.co.kr",
            "Referer": "https://www.all-con.co.kr/list/contest/1/3?sortname=cl_end_date&sortorder=asc&stx=&sfl=&t=1&ct=&sc=&tg=",
            "X-Requested-With": "XMLHttpRequest",
        }

        # [ADD] LINKAREER 상수
        self.LINK_URL = "https://api.linkareer.com/graphql"
        self.LINK_HEADERS = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://linkareer.com/",
        }
        self.LINK_HASH = "f59df641666ef9f55c69ed6a14866bfd2f87fb32c89a80038a466b201ee11422"

        # [ADD] THINKCONTEST 상수
        self.THINK_URL = "https://www.thinkcontest.com/thinkgood/user/contest/subList.do"
        self.THINK_DETAIL_URL = "https://www.thinkcontest.com/thinkgood/user/contest/view.do"
        self.THINK_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://www.thinkcontest.com",
            "Referer": "https://www.thinkcontest.com/thinkgood/user/contest/index.do",
            "X-Requested-With": "XMLHttpRequest",
        }
        # 네트워크 탭에서 확보한 값 (사이트 상황에 따라 달라질 수 있음)
        self.THINK_QUERYSTR = "Y_lDUDfEFsFTgLsbFt-VyefFa_wNrqLAoJIolxPo8ycVd6GOlgXVj7ap50cJxtWOLgFMFsM1kbLnzIZm-i9SszImy2-ricuLrjl9bQDJNig"

        # ──────────────── 정규식 Precompile ────────────────────────────────────────────
        self._WRAP_CHARS = r"""'"`“”‘’‹›«»()[]{}<>「」『』【】〈〉《》¡¿‐-–—―·•∙‧"""
        self._WRAP_RE = re.compile(f"[{re.escape(self._WRAP_CHARS)}]")
        self._SPACE_RE = re.compile(r"\s+", re.UNICODE)


    # 초기화
    def init(self):

        self.LINK_HASH = self.get_setting_value(self.setting, "linkareer")
        self.THINK_QUERYSTR = self.get_setting_value(self.setting, "thinkgood")
        self.dup = self.get_setting_value(self.setting, "dup")

        self.driver_set()
        self.log_signal_func(f"선택 항목 : {self.columns}")
        self.log_signal_func(f"선택 사이트 : {self.sites}")
        return True

    # 프로그램 실행
    def main(self):
        self.log_signal_func("크롤링 시작.")
        self.excel_filename = self.file_driver.get_excel_filename(self.site_name)

        # 엑셀 헤더 생성
        df = pd.DataFrame(columns=self.columns or [])
        df.to_excel(self.excel_filename, index=False)

        # 결과 리스트 초기화
        self.result_list = []

        self.contest_list()
        return True

    # 사이트 라우팅
    def contest_list(self):
        sites = self.sites or []
        total_len = len(sites)
        if total_len == 0:
            self.log_signal_func("선택된 사이트가 없습니다.")
            return

        for index, site in enumerate(sites, start=1):
            try:
                if site == 'WEVITY':
                    self.fetch_wevity()
                elif site == 'LINKareer':
                    self.fetch_linkareer()  # [ADD]
                elif site == '올콘':
                    self.fetch_all_con()    # [ADD]
                elif site == 'Thinkgood':
                    self.fetch_thinkcontest()  # [ADD]
                else:
                    self.log_signal_func(f"[SKIP] 미지원 사이트: {site}")
            except Exception as e:
                self.log_signal_func(f"[ERROR] {site} 수집 중 오류: {e}")

            self.log_signal_func(f"진행 ({index} / {total_len}) : {site} ==============================")
            pro_value = (index / total_len) * 1_000_000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            time.sleep(0.2)


        if self.dup:
            self.log_signal_func(f"중복 제거 시작==============================")
            self.data_asc_set()

    # ──────────────── 공통 HTTP 유틸 ─────────────────────────────────────────────
    # [ADD] APIClient를 일관되게 사용하는 JSON/HTML fetch 헬퍼
    def _to_text(self, resp: Any) -> str:
        """Response/bytes/dict/str 어떤 형태든 안전하게 문자열 본문으로 변환"""
        if resp is None:
            return ""
        # 이미 문자열
        if isinstance(resp, str):
            return resp
        # 바이트류
        if isinstance(resp, (bytes, bytearray)):
            try:
                return resp.decode("utf-8", errors="ignore")
            except Exception:
                return ""
        # requests.Response 유사체
        if hasattr(resp, "text"):
            try:
                return resp.text
            except Exception:
                pass
        # dict/list → 보기 좋게 json 문자열
        if isinstance(resp, (dict, list)):
            try:
                return json.dumps(resp, ensure_ascii=False)
            except Exception:
                return str(resp)
        # 그 외
        return str(resp)


    def _to_json(self, resp: Any) -> Dict[str, Any]:
        """Response/str/bytes/dict 어떤 형태든 안전하게 dict로 변환"""
        if resp is None:
            return {}
        # 이미 dict/list
        if isinstance(resp, (dict, list)):
            return resp  # dict 그대로, list는 상위에서 사용 시 주의
        # requests.Response 유사체 → .json() 시도
        if hasattr(resp, "json"):
            try:
                return resp.json()
            except Exception:
                # fallback: text 파싱
                pass
        # 문자열/바이트 → json.loads
        text = self._to_text(resp)
        if not text:
            return {}
        try:
            return json.loads(text)
        except Exception:
            return {}


    def _http_get_text(self, url: str, headers: Optional[Dict[str, str]] = None,
                       params: Optional[Dict[str, Any]] = None) -> str:
        try:
            resp = self.api_client.get(url, headers=headers or {}, params=params)
            return self._to_text(resp)
        except Exception as e:
            self.log_signal_func(f"[HTTP][GET][ERR] {url} → {e}")
            return ""


    def _http_get_json(self, url: str, headers: Optional[Dict[str, str]] = None,
                       params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            resp = self.api_client.get(url, headers=headers or {}, params=params)
            return self._to_json(resp)
        except Exception as e:
            self.log_signal_func(f"[JSON][GET][ERR] {url} → {e}")
            return {}


    def _http_post_text(self, url: str, headers: Optional[Dict[str, str]] = None,
                        data: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> str:
        try:
            resp = self.api_client.post(url, headers=headers or {}, data=data, json=json_body)
            return self._to_text(resp)
        except Exception as e:
            self.log_signal_func(f"[HTTP][POST][ERR] {url} → {e}")
            return ""


    def _http_post_json(self, url: str, headers: Optional[Dict[str, str]] = None,
                        data: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            resp = self.api_client.post(url, headers=headers or {}, data=data, json=json_body)
            return self._to_json(resp)
        except Exception as e:
            self.log_signal_func(f"[JSON][POST][ERR] {url} → {e}")
            return {}

    # ──────────────── 공통 Date 유틸 ────────────────────────────────────────────
    # ──────────────── WEVITY ───────────────────────────────────────────────────
    def fetch_wevity(self, start_gp: int = 1, max_gp: Optional[int] = None):
        """
        - WEVITY '마감임박(soon)' 리스트를 페이지 끝까지 순회하며 수집
        - 결과를 self.result_list에 누적
        """
        self.log_signal_func("WEVITY ========================================")

        collected = 0
        gp = start_gp
        while getattr(self, "running", True):
            if max_gp is not None and gp > max_gp:
                break

            url = self.WEVITY_LIST_TPL.format(gp=gp)

            # [MODIFY] APIClient 사용
            html = self._http_get_text(url, headers=self.WEVITY_HEADERS)
            if not html:
                self.log_signal_func(f"[WEVITY] 응답 없음 또는 오류 발생 (gp={gp})")
                break

            rows = self._wevity_fetch_page(html, gp)

            if not rows:
                self.log_signal_func(f"[WEVITY] 더 이상 페이지 없음. gp={gp}")
                break

            self.result_list.extend(rows)
            collected += len(rows)
            self.log_signal_func(f"[WEVITY] gp={gp} 수집 {len(rows)}건 (누적 {collected}건)")

            gp += 1
            time.sleep(0.2)

        self.log_signal_func(f"[WEVITY] 최종 수집 {collected}건")

    def _wevity_fetch_page(self, html: str, gp: int) -> List[Dict[str, Any]]:
        """HTML 한 페이지에서 공모전 정보 목록 반환"""
        soup = BeautifulSoup(html, "html.parser")
        ul = soup.select_one("ul.list")
        if not ul:
            return []

        rows: List[Dict[str, Any]] = []
        for idx, li in enumerate(ul.find_all("li", recursive=False), start=1):
            if "top" in (li.get("class") or []):
                continue

            a = li.select_one("div.tit a")
            if not a:
                continue

            title = a.get_text(strip=True)
            href = (a.get("href") or "").strip()
            full_url = href if href.startswith("http") else f"{self.WEVITY_BASE}{href}"


            # [MODIFY] 상세 페이지에서 접수기간 종료일 추출
            detail_html = self._http_get_text(full_url, headers=self.WEVITY_HEADERS)
            deadline = ""
            if detail_html:
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                dday_area = detail_soup.select_one("li.dday-area")
                if dday_area:
                    text = dday_area.get_text(" ", strip=True)
                    # "2025-08-26 ~ 2025-09-07" → 끝 날짜만 추출
                    m = re.search(r"~\s*(\d{4}-\d{2}-\d{2})", text)
                    if m:
                        deadline = m.group(1)

            organ_el = li.select_one("div.organ")
            organ = organ_el.get_text(strip=True) if organ_el else ""

            obj = {
                "사이트": "WEVITY",
                "공모전명": title,
                "주최사": organ,
                "URL": full_url,
                "마감일": deadline,   # YYYY-MM-DD 또는 ""
                "페이지": gp
            }
            self.log_signal_func(f"[WEVITY] WEVITY_obj {gp}/{idx} : {obj}")

            rows.append(obj)
        return rows

    # ──────────────── ALL-CON ──────────────────────────────────────────────────
    # [ADD] 올콘 페이지 페치 + 파싱
    def fetch_all_con(self, start_page: int = 1):
        self.log_signal_func("ALL-CON ========================================")
        page = start_page
        total_collected = 0

        while getattr(self, "running", True):
            payload = {
                "sortorder": "asc",
                "page": str(page),
                "sortname": "cl_end_date",
                "stx": "",
                "sfl": "",
                "rows": "15",
                "t": "1"
            }
            data = self._http_post_json(self.ALLCON_URL, headers=self.ALLCON_HEADERS, data=payload)
            if not data:
                self.log_signal_func(f"[ALL-CON] 페이지 {page} 응답 없음 → 종료")
                break

            rows = self._alcon_parse_rows(data, page)
            if not rows:
                self.log_signal_func(f"[ALL-CON] 페이지 {page} 데이터 없음 → 종료")
                break

            self.result_list.extend(rows)
            total_collected += len(rows)
            self.log_signal_func(f"[ALL-CON] page={page} 수집 {len(rows)}건 (누적 {total_collected}건)")

            total_page = int(data.get("totalPage", page))
            if page >= total_page:
                self.log_signal_func("[ALL-CON] 마지막 페이지 도달")
                break
            page += 1
            time.sleep(0.2)

        self.log_signal_func(f"[ALL-CON] 최종 수집 {total_collected}건")

    def _alcon_parse_rows(self, data: Dict[str, Any], page: int) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for idx, item in enumerate(data.get("rows", []), start=1):
            # cl_title HTML에서 <a> 추출
            soup = BeautifulSoup(item.get("cl_title", "") or "", "html.parser")
            a_tag = soup.find("a")
            title = a_tag.get_text(strip=True) if a_tag else ""
            url_path = a_tag["href"] if a_tag and a_tag.has_attr("href") else ""
            full_url = f"https://www.all-con.co.kr{url_path}" if url_path else ""

            organ = (item.get("cl_host", "") or "").strip()

            # [ADD] 제목/주최사가 잘린 경우 상세 페이지 조회
            if (title.endswith("…") or organ.endswith("…")) and full_url:
                try:
                    detail_html = self._http_get_text(full_url, headers=self.ALLCON_HEADERS)
                    if detail_html:
                        detail_soup = BeautifulSoup(detail_html, "html.parser")
                        # 제목 h1
                        h1 = detail_soup.select_one("div.contest_title_wrap h1")
                        if h1:
                            title = h1.get_text(strip=True)
                        # 주최사 td.desc_host
                        host_td = detail_soup.select_one("td.desc_host")
                        if host_td:
                            organ = host_td.get_text(strip=True)
                except Exception as e:
                    self.log_signal_func(f"[ALL-CON][상세조회실패] {full_url} → {e}")

            date_text = item.get("cl_date", "") or ""
            deadline = ""
            if "~" in date_text:
                end_raw = date_text.split("~")[-1]
                deadline = parse_yy_mm_dd(end_raw)
            obj = {
                "사이트": "ALL-CON",
                "공모전명": title,
                "주최사": organ,
                "URL": full_url,
                "마감일": deadline,
                "페이지": int(data.get("currentPage", page) or page),
            }
            items.append(obj)
            self.log_signal_func(f"[ALL-CON] ALL-CON_obj {page}/{idx} : {obj}")
        return items



    # ──────────────── LINKAREER ────────────────────────────────────────────────
    # [ADD] 링크리어 마감 오름차순 페치
    def fetch_linkareer(self, start_page: int = 1):
        self.log_signal_func("LINKAREER ========================================")
        page = start_page
        total_collected = 0

        while getattr(self, "running", True):
            params = {
                "operationName": "ActivityList_Activities",
                "variables": json.dumps({
                    "filterBy": {"status": "OPEN", "activityTypeID": "3"},
                    "pageSize": 20,
                    "page": page,
                    "activityOrder": {"field": "RECRUIT_CLOSE_AT", "direction": "ASC"},
                }, ensure_ascii=False),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self.LINK_HASH
                    }
                }, ensure_ascii=False),
            }

            data = self._http_get_json(self.LINK_URL, headers=self.LINK_HEADERS, params=params)
            if not data:
                self.log_signal_func(f"[LINKAREER] 페이지 {page} 응답 없음 → 종료")
                break

            rows = self._link_parse_nodes(data, page)
            if not rows:
                self.log_signal_func(f"[LINKAREER] 페이지 {page} 데이터 없음 → 종료")
                break

            self.result_list.extend(rows)
            total_collected += len(rows)
            self.log_signal_func(f"[LINKAREER] page={page} 수집 {len(rows)}건 (누적 {total_collected}건)")

            # 다음 페이지가 없으면 종료
            nodes = (((data.get("data") or {}).get("activities") or {}).get("nodes") or [])
            if not nodes:
                self.log_signal_func("[LINKAREER] 마지막 페이지 도달(또는 더 이상 노드 없음)")
                break

            page += 1
            time.sleep(0.2)

        self.log_signal_func(f"[LINKAREER] 최종 수집 {total_collected}건")

    def _link_parse_nodes(self, data: Dict[str, Any], page: int) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            nodes = data["data"]["activities"]["nodes"]
        except Exception:
            nodes = []

        for idx, node in enumerate(nodes, start=1):
            title = node.get("title")
            organ = node.get("organizationName")
            act_id = node.get("id")
            full_url = f"https://linkareer.com/activity/{act_id}" if act_id else ""
            deadline_ts = node.get("recruitCloseAt")
            deadline = ""
            if deadline_ts:
                try:
                    dt = datetime.fromtimestamp(deadline_ts / 1000)
                    deadline = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            obj = {
                "사이트": "LINKAREER",
                "공모전명": title or "",
                "주최사": organ or "",
                "URL": full_url,
                "마감일": deadline,
                "페이지": page
            }
            rows.append(obj)
            self.log_signal_func(f"[LINKAREER] LINKAREER_obj {page}/{idx} : {obj}")
        return rows

    # ──────────────── THINKCONTEST ─────────────────────────────────────────────
    # [ADD] 씽크콘테스트 페이징 수집
    def fetch_thinkcontest(self, start_page: int = 1, records_per_page: int = 10):
        self.log_signal_func("THINKCONTEST ====================================")
        page = start_page
        total_collected = 0

        while getattr(self, "running", True):
            payload = {
                "querystr": self.THINK_QUERYSTR,
                "recordsPerPage": records_per_page,
                "currentPageNo": page,
                "contest_field": "",
                "host_organ": "",
                "enter_qualified": "",
                "award_size": "",
                "searchStatus": "Y",
                "sidx": "d_day",
                "sord": "ASC"
            }

            data = self._http_post_json(self.THINK_URL, headers=self.THINK_HEADERS, json_body=payload)
            if not data:
                self.log_signal_func(f"[THINKCONTEST] 페이지 {page} 응답 없음 → 종료")
                break

            rows = self._think_parse_rows(data, page)
            if not rows:
                self.log_signal_func(f"[THINKCONTEST] 페이지 {page} 데이터 없음 → 종료")
                break

            self.result_list.extend(rows)
            total_collected += len(rows)
            self.log_signal_func(f"[THINKCONTEST] page={page} 수집 {len(rows)}건 (누적 {total_collected}건)")

            total = int(data.get("totalcnt", 0) or 0)
            per_page = int(data.get("recordsPerPage", records_per_page) or records_per_page)
            total_pages = (total + per_page - 1) // per_page if per_page > 0 else page

            if page >= total_pages:
                self.log_signal_func("[THINKCONTEST] 마지막 페이지 도달")
                break

            page += 1
            time.sleep(0.2)

        self.log_signal_func(f"[THINKCONTEST] 최종 수집 {total_collected}건")

    def _think_parse_rows(self, data: Dict[str, Any], page: int) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for idx, item in enumerate(data.get("listJsonData", []), start=1):  # [MODIFY] enumerate 추가
            title = (item.get("program_nm", "") or "").strip()
            organ = (item.get("host_company", "") or "").strip()

            val = item.get("contest_pk")
            contest_pk = str(val).strip() if val is not None else ""

            deadline = parse_finish_dt(item.get("finish_dt", ""))

            obj = {
                "사이트": "THINKCONTEST",
                "공모전명": title,
                "주최사": organ,
                "URL": f"{self.THINK_DETAIL_URL}?contest_pk={contest_pk}",
                "마감일": deadline,
                "페이지": int(item.get("currentPageNo", page) or page)
            }
            items.append(obj)

            # [ADD] 로그 출력 (WEVITY 형식 맞춤)
            self.log_signal_func(f"[THINKCONTEST] think_obj {page}/{idx} : {obj}")
        return items


    def _norm(self, s: str) -> str:
        s = (s or "").lower()
        s = self._WRAP_RE.sub("", s)   # ← 전역에서 컴파일된 것 사용
        s = self._SPACE_RE.sub("", s)
        return s

    # [ADD] 포함 매칭 유틸 (정규화 포함)
    def _includes_match(self, a: Optional[str], b: Optional[str], threshold: float = 0.90) -> bool:
        if not a or not b:
            return False

        na, nb = self._norm(a), self._norm(b)
        if not na or not nb:
            return False

        if na in nb or nb in na:
            return True

        sim = SequenceMatcher(None, na, nb).ratio()
        return sim >= threshold


    # 후처리(정렬 등)
    # ──────────────── 정렬 + 중복 제거 (유사도 0.9) ─────────────────────────────
    def data_asc_set(self):
        """마감일 오름차순 정렬 후, (동일 마감일 & 주최사/공모전명 유사도≥0.9) 중복 제거
           + [ADD] 어제 이전(≤ 어제) 마감 데이터 제거
        """
        if not self.result_list:
            return

        # [ADD] 0) 어제 이전(≤ 어제) 마감 데이터 제거
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        before_len = len(self.result_list)
        filtered = []
        for row in self.result_list:
            v = (row.get("마감일") or "").strip()
            d = parse_date_yyyy_mm_dd(v)
            self.log_signal_func(f"DEBUG: raw={v}, parsed={d}, yesterday={yesterday}")  # ← 추가
            if not v:
                # 비어있는 마감일은 유지 (원하시면 아래 한 줄로 제거 가능)
                # continue  # ← 주석 해제 시, 마감일 비어있는 항목도 제거
                filtered.append(row)
                continue
            d = parse_date_yyyy_mm_dd(v)
            if d is None:
                # 파싱 불가한 형식은 유지 (원하시면 제거로 바꿔도 됨)
                filtered.append(row)
                continue
            if d <= yesterday:
                # 어제 이전(<= 어제) → 제거
                continue
            filtered.append(row)

        removed_old_cnt = before_len - len(filtered)
        if removed_old_cnt > 0:
            self.log_signal_func(f"지난 마감 제거: {removed_old_cnt}건 제거(≤ {yesterday.isoformat()})")
        self.result_list = filtered

        # ── 1) 날짜 정렬 (유효 날짜만 오름차순, 무효/빈 날짜는 뒤로) ───────────────
        valid_with_dt = []
        invalid = []
        for o in self.result_list:
            v = (o.get("마감일") or "").strip()
            try:
                dt = datetime.strptime(v, "%Y-%m-%d")
                valid_with_dt.append((dt, o))
            except Exception:
                invalid.append(o)

        valid_with_dt.sort(key=lambda x: x[0])
        self.result_list = [o for _, o in valid_with_dt] + invalid
        self.log_signal_func("정렬 완료(마감일 오름차순, 무효/빈 날짜는 뒤로)")

        # ── 2) 중복 제거 (동일 마감일 + 제목 포함매칭) ────────────────────────────
        deduped: List[Dict[str, Any]] = []
        for cur in self.result_list:
            cur_deadline = (cur.get("마감일") or "").strip()
            cur_title = cur.get("공모전명")
            cur_organ = cur.get("주최사")

            if not cur_deadline:
                # 마감일 없는 건은 보수적으로 유지 (원 정책 유지)
                deduped.append(cur)
                continue

            is_dup = False
            for prev in deduped:
                if (prev.get("마감일") or "").strip() != cur_deadline:
                    continue

                prev_title = prev.get("공모전명")
                prev_organ = prev.get("주최사")

                # 제목 포함 매칭 필수
                title_dup = self._includes_match(prev_title, cur_title)
                if title_dup:
                    self.log_signal_func(
                        f"[중복제거] '{cur_title}' ({cur_organ}) → '{prev_title}' ({prev_organ}) 동일 마감일 {cur_deadline}"
                    )
                    is_dup = True
                    break

            if not is_dup:
                deduped.append(cur)

        removed_dup_cnt = len(self.result_list) - len(deduped)
        self.result_list = deduped
        self.log_signal_func(f"중복 제거 완료: {removed_dup_cnt}건 제거")


    # 드라이버 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # api
        # [MODIFY] 캐시 사용 여부는 필요 시 옵션으로
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)

    # 마무리
    def destroy(self):
        # 엑셀 후처리 및 진행률 마무리
        try:
            self.excel_driver.save_obj_list_to_excel(
                self.excel_filename,
                self.result_list or [],
                columns=self.columns
            )
        except Exception as e:
            self.log_signal_func(f"[ERROR] 엑셀 저장 실패: {e}")

        self.progress_signal.emit(self.before_pro_value, 1_000_000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(1)
        self.log_signal_func("=============== 크롤링 종료")
        if getattr(self, "running", True):
            self.progress_end_signal.emit()

    # 정지
    def stop(self):
        self.running = False
