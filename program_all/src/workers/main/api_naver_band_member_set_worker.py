import os
import time
import json
import threading
import re
from datetime import datetime
from typing import Any, Dict, List

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

        self.site_name = "naver_band"
        self.site_login_url = "https://auth.band.us/login_page?next_url=https%3A%2F%2Fwww.band.us%2F"
        self.site_url = "https://www.band.us/band"

        self.running = True

        self.csv_filename = None

        self.selenium_driver = None
        self.driver = None

        self.excel_driver = None
        self.file_driver = None
        self.api_client = None

        self.band_name = ""

    # =========================================================
    # phone extract (참고 코드 이식)
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

        found = []

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
    # lifecycle
    # =========================================================
    def init(self):
        self.driver_set()
        return True

    def stop(self):
        self.running = False
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass

    def destroy(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass

        self.progress_signal.emit(0.0, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(0.5)
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()

    def driver_set(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)

        # ✅ 크롬 띄우는 건 유지
        self.selenium_driver = SeleniumUtils(headless=False)
        self.driver = self.selenium_driver.start_driver(1200)

    def main(self):
        self.log_signal_func("시작합니다.")

        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.excel_driver.init_csv(self.csv_filename, self.columns)

        # ✅ 로그인 안내 + 멤버 페이지 이동(유저가 직접 로그인)
        self.wait_for_user_confirmation()

        try:
            self.band_name = self._extract_band_name_from_page() or ""
            if self.band_name:
                self.log_signal_func("✅ 밴드명: " + self.band_name)
            else:
                self.log_signal_func("⚠️ 밴드명 추출 실패(빈값)")
        except Exception:
            self.band_name = ""
            self.log_signal_func("⚠️ 밴드명 추출 실패(예외)")

        # ✅ 후킹 결과 파일 대기(mitmproxy addon이 생성/덮어쓰기)
        inbox_dir = os.path.abspath("./out/inbox")
        json_path = os.path.join(inbox_dir, "naver_band_member.json")
        self.log_signal_func("후킹 JSON 대기: " + json_path)

        data = self._wait_json(json_path, timeout_sec=90)
        if not data:
            self.log_signal_func("❌ 후킹 JSON 수신 실패(시간초과/중지)")
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
            return False

        members = self._extract_members(data)
        self._save_members(members)

        self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
        self.log_signal_func("✅ 완료")
        return True

    # -------------------------------------------------
    # 로그인 유도 + 멤버페이지 진입(요청 유발)
    # -------------------------------------------------
    def wait_for_user_confirmation(self):
        self.log_signal_func("밴드 로그인을 진행해주세요.")
        self.driver.get(self.site_login_url)

        event = threading.Event()
        self.msg_signal_func("로그인 후 OK를 눌러주세요", "info", event)
        event.wait()

        band_id = self.get_setting_value(self.setting, "band_id")
        band_url = f"{self.site_url}/{band_id}/member"

        # ✅ 여기서 실제 API 호출이 발생 → 후킹이 잡힘
        self.driver.get(band_url)
        time.sleep(2.0)

        self.log_signal_func("✅ 멤버 페이지 진입 완료")

    # -------------------------------------------------
    # === 신규 === 밴드명 추출
    # <a href="/band/4877094/post" class="uriText" ...>TEXT</a>
    # -------------------------------------------------
    def _extract_band_name_from_page(self) -> str:
        band_id = self.get_setting_value(self.setting, "band_id")
        if not band_id:
            return ""

        # 우선: 니가 준 스펙 그대로 href + class 매칭
        target_href = f"/band/{band_id}/post"

        # page_source는 Selenium이 있으니 바로 파싱
        html = ""
        try:
            html = self.driver.page_source or ""
        except Exception:
            html = ""

        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        a = soup.select_one(f'a.uriText[href="{target_href}"]')
        if a and a.get_text(strip=True):
            return a.get_text(strip=True)
        return ""


    # -------------------------------------------------
    # out/inbox json 대기
    # -------------------------------------------------
    def _wait_json(self, json_path, timeout_sec=60):
        t0 = time.time()
        last_size = -1

        while self.running and (time.time() - t0 < timeout_sec):
            if not os.path.isfile(json_path):
                time.sleep(0.25)
                continue

            try:
                sz = os.path.getsize(json_path)
                if sz <= 0:
                    time.sleep(0.2)
                    continue

                # 쓰는 중일 수 있으니 size 안정화 체크
                if last_size != -1 and sz != last_size:
                    last_size = sz
                    time.sleep(0.2)
                    continue
                last_size = sz

                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)

            except Exception:
                time.sleep(0.2)

        return None

    # -------------------------------------------------
    # JSON -> members
    # -------------------------------------------------
    def _extract_members(self, data):
        try:
            if data.get("result_code") != 1:
                self.log_signal_func("❌ band api resp: " + str(data)[:500])
                return []
        except Exception:
            pass

        try:
            result_data = data.get("result_data") or {}
            members = result_data.get("members") or []
            return members
        except Exception:
            return []

    # -------------------------------------------------
    # members -> csv
    # -------------------------------------------------
    def _save_members(self, members):
        rows = []

        band_name = self.band_name or ""

        for m in members:
            try:
                name = m.get("name", "") or ""
                desc = m.get("description", "") or ""

                rows.append({
                    "밴드명": band_name,
                    "유저번호": m.get("user_no"),
                    "직책": m.get("role"),
                    "등록일": ms_to_yyyy_mm_dd(m.get("created_at")),
                    "이름": name,
                    "설명": desc,
                    "전화번호": self.pick_phone(name, desc),
                })
            except Exception:
                pass

        if rows:
            self.excel_driver.append_to_csv(self.csv_filename, rows, self.columns)

        self.log_signal_func("✅ 저장 완료")
