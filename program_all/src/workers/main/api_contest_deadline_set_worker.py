import json
import random
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from bs4 import BeautifulSoup

from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.file_utils import FileUtils
from src.core.global_state import GlobalState
from src.utils.excel_utils import ExcelUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiContestDealineSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()
        self.columns: Optional[List[str]] = None
        self.sites: Optional[List[str]] = None
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

        # WEVITY 크롤링용 상수
        self.WEVITY_BASE = "https://www.wevity.com/"
        self.WEVITY_LIST_TPL = self.WEVITY_BASE + "?c=find&s=1&mode=soon&gub=1&gp={gp}"

    # 초기화
    def init(self):
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
                    self.fetch_linkareer()
                elif site == '올콘':
                    self.fetch_all_con()
                elif site == 'Thinkgood':
                    self.fetch_thinkcontest()
                else:
                    self.log_signal_func(f"[SKIP] 미지원 사이트: {site}")
            except Exception as e:
                self.log_signal_func(f"[ERROR] {site} 수집 중 오류: {e}")

            self.log_signal_func(f"진행 ({index} / {total_len}) : {site} ==============================")
            pro_value = (index / total_len) * 1_000_000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            time.sleep(0.2)

        self.data_asc_set()

    # ──────────────── WEVITY ────────────────
    def fetch_wevity(self, start_gp: int = 1, max_gp: Optional[int] = None):
        """
        - WEVITY '마감임박(soon)' 리스트를 페이지 끝까지 순회하며 수집
        - 결과를 self.result_list에 누적
        """
        self.log_signal_func("WEVITY ========================================")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        }

        collected = 0
        gp = start_gp
        while getattr(self, "running", True):
            if max_gp is not None and gp > max_gp:
                break

            url = self.WEVITY_LIST_TPL.format(gp=gp)

            # [MODIFY] APIClient로 GET (문자열 HTML 또는 None 반환)
            html = self.api_client.get(url, headers=headers)
            if not html:
                self.log_signal_func(f"[WEVITY] 응답 없음 또는 오류 발생 (gp={gp})")
                break

            # [MODIFY] 파싱 함수가 html 문자열을 받도록 변경
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


    # [MODIFY] 시그니처: (session, gp) → (html, gp)
    def _wevity_fetch_page(self, html: str, gp: int) -> List[Dict[str, Any]]:
        """HTML 한 페이지에서 공모전 정보 목록 반환"""
        soup = BeautifulSoup(html, "html.parser")
        ul = soup.select_one("ul.list")
        if not ul:
            return []

        rows: List[Dict[str, Any]] = []
        for li in ul.find_all("li", recursive=False):
            if "top" in (li.get("class") or []):
                continue

            a = li.select_one("div.tit a")
            if not a:
                continue

            title = a.get_text(strip=True)
            href = (a.get("href") or "").strip()
            full_url = href if href.startswith("http") else f"{self.WEVITY_BASE}{href}"

            organ_el = li.select_one("div.organ")
            organ = organ_el.get_text(strip=True) if organ_el else ""

            day_el = li.select_one("div.day")
            day_raw = day_el.get_text(" ", strip=True) if day_el else ""
            deadline = self._wevity_parse_deadline(day_raw)

            rows.append({
                "사이트": "WEVITY",
                "공모전명": title,
                "주최사": organ,
                "URL": full_url,
                "마감일": deadline,   # YYYY-MM-DD 또는 ""
                "페이지": gp
            })
        return rows


    def _wevity_parse_deadline(self, day_text: str) -> str:
        """'D-8' → 오늘+8일, '오늘' 포함 → 오늘 날짜, 그 외 → 빈 문자열"""
        today = datetime.now().date()
        m = re.search(r"D-(\d+)", day_text)
        if m:
            try:
                return (today + timedelta(days=int(m.group(1)))).isoformat()
            except Exception:
                return ""
        if "오늘" in day_text:
            return today.isoformat()
        return ""

    # ──────────────── 자리만듦(추후 구현) ────────────────
    def fetch_linkareer(self):
        self.log_signal_func("LINKareer ========================================")

    def fetch_all_con(self):
        self.log_signal_func("올콘 ========================================")

    def fetch_thinkcontest(self):
        self.log_signal_func("Thinkgood ========================================")

    # 후처리(정렬 등)
    def data_asc_set(self):
        """마감일 오름차순 정렬(날짜 형식 가능한 것만 우선 정렬)"""
        if not self.result_list:
            return
        def _key(o: Dict[str, Any]):
            v = o.get("마감일") or ""
            try:
                return datetime.strptime(v, "%Y-%m-%d")
            except Exception:
                # 날짜 없거나 형식 아님 → 뒤로
                return datetime.max
        self.result_list.sort(key=_key)
        self.log_signal_func("정렬 완료(마감일 오름차순)")

    # 드라이버 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # api
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

