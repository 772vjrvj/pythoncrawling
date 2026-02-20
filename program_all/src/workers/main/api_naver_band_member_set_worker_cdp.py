# ApiNaverBandMemberSetLoadWorker.py
# -*- coding: utf-8 -*-

import os
import time
import threading
import re
import json
from typing import List, Optional, Dict, Any

from bs4 import BeautifulSoup

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.time_utils import ms_to_yyyy_mm_dd


class ApiNaverBandMemberSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()

        self.site_name: str = "naver_band"
        self.site_login_url: str = "https://auth.band.us/login_page?next_url=https%3A%2F%2Fwww.band.us%2F"
        self.site_url: str = "https://www.band.us/band"

        self.running: bool = True
        self.csv_filename: Optional[str] = None

        self.selenium_driver: Optional[SeleniumUtils] = None
        self.driver: Any = None  # selenium webdriver (타입 힌트 최소화)
        self.excel_driver: Optional[ExcelUtils] = None
        self.file_driver: Optional[FileUtils] = None
        self.api_client: Optional[APIClient] = None

        self.band_name: str = ""
        self._driver_closed: bool = False

    # =========================================================
    # lifecycle
    # =========================================================
    def init(self) -> bool:
        self.driver_set()
        return True

    def driver_set(self) -> None:
        # 이전 프록시/후킹 도구(예: mitmproxy, Fiddler) 사용으로 남은 HTTP(S)_PROXY 환경변수를 제거해
        # Chrome/requests가 의도치 않게 프록시를 타는 문제를 방지한다.
        for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            os.environ.pop(k, None)

        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)

        self.selenium_driver = SeleniumUtils(headless=False)
        self.selenium_driver.set_capture_options(enabled=True, block_images=False)

        self.driver = self.selenium_driver.start_driver(1200)
        self.log_signal_func("CDP 준비: perf log capability=ON, Network.enable=로그인 전/후 ON(드라이버 재기동 없음)")

    def _close_driver_once(self) -> None:
        # Selenium driver를 여러 번 종료하는 문제를 방지하기 위해 quit()를 한 번만 실행하도록 한다.
        if self._driver_closed:
            return
        self._driver_closed = True

        try:
            if self.selenium_driver:
                self.selenium_driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None
            self.selenium_driver = None

    def stop(self) -> None:
        self.running = False
        self._close_driver_once()

    def destroy(self) -> None:
        self._close_driver_once()

        self.progress_signal.emit(0.0, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(2.5)
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()

    # =========================================================
    # main
    # =========================================================
    def main(self) -> bool:
        self.log_signal_func("크롤링 시작합니다.")

        if not self.file_driver or not self.excel_driver or not self.selenium_driver:
            self.log_signal_func("❌ 초기화 실패(driver_set 누락)")
            return False

        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.excel_driver.init_csv(self.csv_filename, self.columns)

        band_id = self.get_setting_value(self.setting, "band_id")
        if not band_id:
            self.log_signal_func("❌ band_id 없음")
            return False

        # 로그인(유저 OK 대기) + 멤버 페이지로 이동
        # === 신규 === 캡처 ON 타이밍을 멤버페이지 진입 '이전'으로 당기기 위해, 내부에서 enable/drain 수행
        self.wait_for_user_confirmation(band_id)

        # === 신규 ===
        # 기존 performance 로그를 비워 이후 발생하는 API만 정확히 캡처하도록 한다. (큐 pop)
        drained = self.selenium_driver.drain_performance_logs()
        self.log_signal_func(f"perf log drain={drained}")

        # API 요청을 다시 발생시키기 위해 refresh
        self.driver.refresh()
        time.sleep(2)

        # get_members_of_band 응답 JSON 캡처
        self.log_signal_func("CDP 응답 대기 중(get_members_of_band)...")
        data = self.selenium_driver.wait_api_json(
            url_contains="api-kr.band.us/v2.0.0/get_members_of_band",
            query_contains=f"band_no={band_id}",
            timeout_sec=12.0,
            poll=0.2,
            require_status_200=True,
        )

        if not data:
            self.log_signal_func("❌ CDP로 멤버 API 응답을 못 잡음")
            return False

        # 밴드명은 옵션(없어도 진행)
        self._extract_band_name_from_page(band_id)

        members = self._extract_members(data)
        self._save_members(members)

        self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
        self.log_signal_func("✅ 완료")
        return True

    # =========================================================
    # login (simple)
    # =========================================================
    def wait_for_user_confirmation(self, band_id: str) -> None:
        # 로그인 페이지로 이동
        self.driver.get(self.site_login_url)

        # 사용자가 로그인 완료 후 OK 누를 때까지 대기
        event = threading.Event()
        self.msg_signal_func("로그인 완료 후 OK를 눌러주세요", "info", event)
        event.wait()

        # === 신규 ===
        # 멤버 페이지 진입 직후 API가 바로 나가서 놓치는 경우가 있어,
        # 진입 전에 Network.enable + perf drain을 먼저 수행한다.
        ok = self.selenium_driver.enable_capture_now()
        if ok:
            drained = self.selenium_driver.drain_performance_logs()
            self.log_signal_func(f"CDP 네트워크 캡처 선활성화 완료 (drain={drained})")
        else:
            self.log_signal_func("⚠️ CDP 네트워크 캡처 선활성화 실패(이후 refresh로 재시도)")

        # 로그인 완료 -> 멤버 페이지로 이동
        member_url = f"{self.site_url}/{band_id}/member"
        self.driver.get(member_url)

        self.log_signal_func("✅ 멤버 페이지 진입 완료")

    # =========================================================
    # band name (optional)
    # =========================================================
    def _extract_band_name_from_page(self, band_id: str) -> None:
        """멤버 페이지에서 밴드명을 추출하여 self.band_name에 저장 (옵션값)."""
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        el = soup.select_one(f'a.uriText[href="/band/{band_id}/post"]')
        self.band_name = el.get_text(strip=True) if el else ""

    # =========================================================
    # phone extract
    # =========================================================
    _SEP = r"[^\d]*"
    _RE_MOBILE = re.compile(rf"(01[016789]){_SEP}(\d{{3,4}}){_SEP}(\d{{3,4}})")
    _RE_070 = re.compile(rf"(070){_SEP}(\d{{3,4}}){_SEP}(\d{{4}})")
    _RE_AREA = re.compile(rf"(0(?:2|[3-6]\d))" + _SEP + r"(\d{3,4})" + _SEP + r"(\d{4})")
    _RE_SPECIAL = re.compile(rf"(1\d{{3}}){_SEP}(\d{{4}})")
    _RE_LOCAL = re.compile(r"(?<!\d)(\d{3,4})" + _SEP + r"(\d{4})(?!\d)")

    def _clean_text_for_scan(self, s: str) -> str:
        if not s:
            return ""
        s = s.replace("\u00A0", " ")
        s = re.sub(r"[()]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _fmt_mobile(self, a: str, b: str, c: str) -> str:
        if len(c) == 3:
            c = "0" + c
        return f"{a}-{b}-{c}"

    def extract_phones(self, name: str, desc: str) -> List[str]:
        hay = self._clean_text_for_scan(f"{name or ''} {desc or ''}")
        if not hay:
            return []

        found: List[str] = []
        for m in self._RE_MOBILE.finditer(hay):
            found.append(self._fmt_mobile(m.group(1), m.group(2), m.group(3)))
        for m in self._RE_070.finditer(hay):
            found.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        for m in self._RE_AREA.finditer(hay):
            found.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        for m in self._RE_SPECIAL.finditer(hay):
            found.append(f"{m.group(1)}-{m.group(2)}")
        for m in self._RE_LOCAL.finditer(hay):
            if m.group(1).startswith("0"):
                continue
            found.append(f"{m.group(1)}-{m.group(2)}")

        # 중복 제거(순서 유지)
        return list(dict.fromkeys(found))

    def pick_phone(self, name: str, desc: str) -> str:
        phones = self.extract_phones(name, desc)
        return phones[0] if phones else ""

    # =========================================================
    # members
    # =========================================================
    def _extract_members(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """band API 응답에서 members 배열만 꺼낸다(실패/형식 불일치 시 빈 리스트)."""
        if not data or data.get("result_code") != 1:
            return []
        return (data.get("result_data") or {}).get("members") or []

    def _save_members(self, members: List[Dict[str, Any]]) -> None:
        """members 배열을 CSV rows로 변환해 저장한다."""
        rows: List[Dict[str, Any]] = [{
            "밴드명": self.band_name or "",
            "유저번호": m.get("user_no"),
            "직책": m.get("role"),
            "등록일": ms_to_yyyy_mm_dd(m.get("created_at")),
            "이름": (m.get("name") or ""),
            "설명": (m.get("description") or ""),
            "전화번호": self.pick_phone((m.get("name") or ""), (m.get("description") or "")),
        } for m in (members or [])]

        if rows:
            self.excel_driver.append_to_csv(self.csv_filename, rows, self.columns)

