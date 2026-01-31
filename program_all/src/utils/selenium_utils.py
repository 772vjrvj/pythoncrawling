# SeleniumUtils.py
# -*- coding: utf-8 -*-

import os
import time
import glob
import shutil
import tempfile
import uuid
import subprocess
import re
from typing import Optional, Tuple

import undetected_chromedriver as uc
from undetected_chromedriver.patcher import Patcher  # === 신규 ===

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    InvalidSelectorException,
    WebDriverException,
    SessionNotCreatedException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DEFAULT_WIDTH  = 1280
DEFAULT_HEIGHT = 800
SLEEP_AFTER_PROFILE = 0.3


class SeleniumUtils:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self._tmp_profile: Optional[str] = None
        self.last_error: Optional[Exception] = None

    # ----- 내부 유틸 -----
    def _new_tmp_profile(self) -> str:
        base = os.path.join(tempfile.gettempdir(), "selenium_profiles")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"profile_{uuid.uuid4().hex}")
        os.makedirs(path, exist_ok=True)
        return path

    def _wipe_locks(self, path: str):
        for pat in ["Singleton*", "LOCK", "LockFile", "DevToolsActivePort", "lockfile"]:
            for p in glob.glob(os.path.join(path, pat)):
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception:
                    pass

    def _build_options(self):
        opts = uc.ChromeOptions()
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--lang=ko-KR")
        opts.add_argument(f"--window-size={DEFAULT_WIDTH},{DEFAULT_HEIGHT}")
        if self._tmp_profile:
            opts.add_argument(f"--user-data-dir={self._tmp_profile}")
        if self.headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
        return opts

    def _detect_chrome_major(self) -> Optional[int]:
        try:
            out = subprocess.check_output(
                ["chrome", "--version"],
                stderr=subprocess.STDOUT,
                shell=True,
                text=True
            )
            m = re.search(r"(\d+)\.", out)
            if m:
                return int(m.group(1))
        except Exception:
            pass
        return None

    def _parse_major_from_error(self, e: Exception) -> Optional[int]:
        msg = str(e)
        m = re.search(r"Current browser version is (\d+)", msg)
        if m:
            return int(m.group(1))
        return None

    # === 신규 === uc 캐시 폴더에서 드라이버 정리(꼬였을 때)
    def _wipe_uc_driver_cache(self):
        # 보통 여기들 중 하나에 깔림(환경마다 다름)
        candidates = [
            os.path.join(os.path.expanduser("~"), ".local", "share", "undetected_chromedriver"),
            os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "undetected_chromedriver"),
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "undetected_chromedriver"),
        ]
        for base in candidates:
            try:
                if os.path.isdir(base):
                    # chromedriver* 파일들만 정리 (폴더 전체 삭제는 부담될 수 있어 최소만)
                    for p in glob.glob(os.path.join(base, "**", "chromedriver*.exe"), recursive=True):
                        try: os.remove(p)
                        except Exception: pass
                    for p in glob.glob(os.path.join(base, "**", "chromedriver*"), recursive=True):
                        # mac/linux도 대비
                        if os.path.isfile(p):
                            try: os.remove(p)
                            except Exception: pass
            except Exception:
                pass

    # === 신규 === 원하는 메이저로 패치해서 "드라이버 경로를 강제 확보"
    def _get_driver_path_for_major(self, major: int) -> str:
        patcher = Patcher(version_main=major)
        patcher.auto()  # 드라이버 다운로드/패치
        return patcher.executable_path

    # --- 화면 배치 ---
    def _get_screen_size(self) -> Tuple[int, int]:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            w = root.winfo_screenwidth()
            h = root.winfo_screenheight()
            root.destroy()
            if w and h:
                return int(w), int(h)
        except Exception:
            pass
        return 1920, 1080

    def _place_left_half(self):
        if not self.driver or self.headless:
            return
        sw, sh = self._get_screen_size()
        try:
            self.driver.set_window_rect(x=0, y=0, width=max(600, sw // 2), height=max(600, sh))
        except Exception:
            pass

    def _safe_quit_driver(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None

    # ----- 외부에서 쓰는 함수 -----
    def start_driver(self, timeout: int = 30):
        self._tmp_profile = self._new_tmp_profile()
        self._wipe_locks(self._tmp_profile)
        time.sleep(SLEEP_AFTER_PROFILE)

        major = self._detect_chrome_major()
        try_chain = []
        if major:
            try_chain.append(major)
        try_chain.append(None)  # fallback

        last = None

        for m in try_chain:
            try:
                opts = self._build_options()  # ✅ 매 시도마다 새 options

                if m:
                    driver_path = self._get_driver_path_for_major(m)
                    self.driver = uc.Chrome(
                        options=opts,
                        driver_executable_path=driver_path
                    )
                else:
                    self.driver = uc.Chrome(options=opts)

                try:
                    self.driver.set_page_load_timeout(timeout)
                except Exception:
                    pass

                self._place_left_half()
                return self.driver

            except SessionNotCreatedException as e:
                last = e

                # ✅ 신규: 실패한 드라이버/크롬 잔여 정리 후 재시도
                self._safe_quit_driver()

                parsed = self._parse_major_from_error(e)
                if parsed:
                    try:
                        opts = self._build_options()  # ✅ 재시도도 새 options
                        self._wipe_uc_driver_cache()

                        driver_path = self._get_driver_path_for_major(parsed)
                        self.driver = uc.Chrome(
                            options=opts,
                            driver_executable_path=driver_path
                        )

                        try:
                            self.driver.set_page_load_timeout(timeout)
                        except Exception:
                            pass

                        self._place_left_half()
                        return self.driver

                    except Exception as e2:
                        last = e2
                        # ✅ 신규: 재시도 실패도 정리
                        self._safe_quit_driver()
                        continue

            except Exception as e:
                last = e
                # ✅ 신규: 기타 예외도 정리
                self._safe_quit_driver()
                continue

        self.last_error = last
        raise last


    def quit(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None
            if self._tmp_profile and os.path.isdir(self._tmp_profile):
                try:
                    shutil.rmtree(self._tmp_profile, ignore_errors=True)
                except Exception:
                    pass
            self._tmp_profile = None

    # ----- 헬퍼 -----
    def wait_element(self, by, selector: str, timeout: int = 10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except Exception as e:
            self.last_error = e
            return None

    @staticmethod
    def explain_exception(context: str, e: Exception) -> str:
        if isinstance(e, NoSuchElementException):           return f"❌ {context}: 요소 없음"
        if isinstance(e, StaleElementReferenceException):   return f"❌ {context}: Stale 요소"
        if isinstance(e, TimeoutException):                 return f"⏱️ {context}: 시간 초과"
        if isinstance(e, ElementClickInterceptedException): return f"🚫 {context}: 클릭 방해"
        if isinstance(e, ElementNotInteractableException):  return f"🚫 {context}: 비활성 요소"
        if isinstance(e, InvalidSelectorException):         return f"🚫 {context}: 선택자 오류"
        if isinstance(e, WebDriverException):               return f"⚠️ {context}: WebDriver 오류"
        return f"❗ {context}: 알 수 없는 오류"
