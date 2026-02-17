# ApiNaverBandMemberSetLoadWorker.py
# -*- coding: utf-8 -*-

import os
import time
import json
import threading
import re
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

        self._driver_closed = False  # === 신규 === stop/destroy 중복 quit 방지

    # =========================================================
    # lifecycle
    # =========================================================
    def init(self):
        self.driver_set()
        return True

    def _close_driver_once(self):
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

    def stop(self):
        self.running = False
        self._close_driver_once()

    def destroy(self):
        self._close_driver_once()

        self.progress_signal.emit(0.0, 1000000)
        self.log_signal_func("크롤링 종료중...")
        time.sleep(0.5)
        self.log_signal_func("크롤링 종료")
        self.progress_end_signal.emit()

    def driver_set(self):
        # === 신규 === 환경 프록시 잔재 제거(원치않게 requests/chrome에 영향 주는 케이스 방지)
        for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            os.environ.pop(k, None)

        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)

        # ✅ 셀레니움은 프록시/후킹 모르고 그냥 띄움
        # === 신규 === CDP/이미지차단 토글은 "필요할 때만" ON
        self.selenium_driver = SeleniumUtils(headless=False)

        # === 신규 ===
        # 배포 환경에서 CDP(performance log) ON 상태로 처음부터 띄우면 "사이트 로드 실패"가 나는 케이스가 있어
        # 1) 최초 드라이버는 CDP OFF로 띄워서 로그인/페이지 진입까지 안정화
        # 2) 멤버 페이지 진입 직후에만 CDP ON으로 재기동(같은 고정 프로필 유지)해서 응답 캡처
        self.selenium_driver.set_capture_options(enabled=False, block_images=True)

        self.driver = self.selenium_driver.start_driver(1200)

        self.log_signal_func("CDP 네트워크 캡처: OFF(로그인/진입 안정화 모드)")

        # === 신규 === 현재 profile_dir 로그(초기)
        try:
            self.log_signal_func("DEBUG profile_dir(init): " + str(getattr(self.selenium_driver, "_profile_dir", None)))
        except Exception:
            pass

    def main(self):
        self.log_signal_func("시작합니다.")

        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.excel_driver.init_csv(self.csv_filename, self.columns)

        # 로그인 + 멤버 페이지 이동
        self.wait_for_user_confirmation()

        # === 신규 ===
        # 멤버 페이지까지 정상 진입 후에만 CDP ON 재기동(프로필 유지)
        try:
            band_id = self.get_setting_value(self.setting, "band_id")
            if band_id:
                self._restart_driver_for_cdp_and_reopen_member(band_id)
        except Exception as e:
            # === 신규 === 재기동 실패 원인 로그를 반드시 남김
            try:
                self.log_signal_func("⚠️ CDP ON 재기동 실패 사유: " + str(e))
            except Exception:
                pass
            self.log_signal_func("⚠️ CDP ON 재기동 실패 → 기존 드라이버로 계속 진행")

        try:
            self.band_name = self._extract_band_name_from_page() or ""
            if self.band_name:
                self.log_signal_func("✅ 밴드명: " + self.band_name)
            else:
                self.log_signal_func("⚠️ 밴드명 추출 실패(빈값)")
        except Exception as e:
            self.band_name = ""
            self.log_signal_func("⚠️ 밴드명 추출 실패(예외): " + str(e))

        # === 핵심 === CDP로 get_members_of_band 응답 JSON 직접 획득
        data = self._fetch_members_via_cdp()

        if not data:
            self.log_signal_func("❌ CDP로 멤버 API 응답을 못 잡음")
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
            return False

        members = self._extract_members(data)
        self._save_members(members)

        self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
        self.log_signal_func("✅ 완료")
        return True

    # =========================================================
    # === 신규 === CDP 안정화: 로그인 후에만 CDP ON 재기동 + 멤버 페이지 재진입
    # =========================================================
    def _restart_driver_for_cdp_and_reopen_member(self, band_id: str):
        if not self.selenium_driver:
            return
        if not self.driver:
            return
        if not band_id:
            return

        try:
            self.selenium_driver.drain_performance_logs()
        except Exception:
            pass

        try:
            # === 신규 === CDP ON으로 옵션 변경(성능로그 활성은 driver 생성 시점에 반영됨)
            self.selenium_driver.set_capture_options(enabled=True, block_images=True)

            # 같은 프로필(user-data-dir)을 유지한 채 드라이버만 재시작
            self.driver = self.selenium_driver.restart_driver_keep_profile(1200)

            # === 신규 === 재기동 직후 디버그
            try:
                self.log_signal_func("DEBUG profile_dir(after_restart): " + str(getattr(self.selenium_driver, "_profile_dir", None)))
            except Exception:
                pass
            try:
                self.log_signal_func("DEBUG current_url(after_restart): " + str(self.driver.current_url))
            except Exception:
                pass

            try:
                ok = self.selenium_driver.enable_capture_now()
                self.log_signal_func("CDP 네트워크 캡처: " + ("ON" if ok else "OFF(미지원/차단)"))
            except Exception as e:
                self.log_signal_func("CDP 네트워크 캡처: OFF(예외): " + str(e))

            # 재기동 후 멤버 페이지 재진입(요청 유발)
            band_url = f"{self.site_url}/{band_id}/member"
            try:
                self.selenium_driver.drain_performance_logs()
            except Exception:
                pass

            self.driver.get(band_url)
            self.log_signal_func("✅ (CDP ON) 멤버 페이지 재진입 완료")

            # === 신규 === 재진입 후 URL 확인(로그인 페이지로 튀면 여기서 잡힘)
            try:
                cur = str(self.driver.current_url or "")
                self.log_signal_func("DEBUG current_url(after_get_member): " + cur)
                if "login_page" in cur or "auth.band.us" in cur:
                    self.log_signal_func("⚠️ 재기동 후 로그인 페이지로 이동됨(세션 유지 실패 가능)")
            except Exception:
                pass

        except Exception as e:
            # === 신규 === 예외 원인 로깅(삼키지 말기)
            try:
                self.log_signal_func("⚠️ CDP ON 재기동 실패 사유(inside): " + str(e))
            except Exception:
                pass
            self.log_signal_func("⚠️ CDP ON 재기동 실패 → 기존 드라이버로 계속 진행")

    # =========================================================
    # === CDP 방식: getResponseBody로 JSON 잡기
    # =========================================================
    def _fetch_members_via_cdp(self) -> Optional[Dict[str, Any]]:
        band_id = self.get_setting_value(self.setting, "band_id")

        req = self.selenium_driver.wait_api_request(
            url_contains="api-kr.band.us/v2.0.0/get_members_of_band",
            query_contains=f"band_no={band_id}",
            timeout_sec=10,
        )

        if req:
            self.log_signal_func(f"req ==> {req}")

        if not band_id:
            self.log_signal_func("❌ band_id 없음")
            return None

        # 캡처 토글이 꺼져있으면 여기서 켜도 됨(방어)
        # === 신규 ===
        try:
            if self.selenium_driver and not getattr(self.selenium_driver, "capture_enabled", False):
                self.selenium_driver.set_capture_options(enabled=True, block_images=None)
                self.selenium_driver.enable_capture_now()
        except Exception:
            pass

        # 1) 멤버 페이지 진입 직후 대기(가장 잘 잡힘)
        self.log_signal_func("CDP 응답 대기 중(get_members_of_band)...")
        data = self._wait_members_api_json(band_id=band_id, timeout_sec=12.0)
        if data:
            return data

        # 2) 마지막 수단: refresh 1회 + 로그 드레인 후 재시도
        self.log_signal_func("⚠️ 미검출 → refresh 1회 후 재시도")
        try:
            if self.selenium_driver:
                self.selenium_driver.drain_performance_logs()  # === 신규 === 과거 이벤트 오염 제거
            if self.driver:
                self.driver.refresh()
            time.sleep(0.9)
        except Exception:
            pass

        data = self._wait_members_api_json(band_id=band_id, timeout_sec=12.0)
        return data

    def _wait_members_api_json(self, band_id: str, timeout_sec: float = 12.0) -> Optional[Dict[str, Any]]:
        if not self.selenium_driver:
            return None

        return self.selenium_driver.wait_api_json(
            url_contains="api-kr.band.us/v2.0.0/get_members_of_band",
            query_contains=f"band_no={band_id}",
            timeout_sec=timeout_sec,
            poll=0.2,
            require_status_200=True,
        )

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

        try:
            if self.selenium_driver:
                self.selenium_driver.drain_performance_logs()
        except Exception:
            pass

        self.driver.get(band_url)
        self.log_signal_func("✅ 멤버 페이지 진입 완료")

    def _extract_band_name_from_page(self) -> str:
        band_id = self.get_setting_value(self.setting, "band_id")
        if not band_id:
            return ""

        target_href = f"/band/{band_id}/post"

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

        return list(dict.fromkeys(found))

    def pick_phone(self, name: str, desc: str) -> str:
        phones = self.extract_phones(name, desc)
        return phones[0] if phones else ""

    # -------------------------------------------------
    # json 대기(기존 유지)
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
