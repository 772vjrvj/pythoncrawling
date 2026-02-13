# PlaywrightUtils.py
# -*- coding: utf-8 -*-

import os
import time
import glob
import shutil
import tempfile
import uuid
from typing import Optional, Tuple

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


DEFAULT_WIDTH  = 1280
DEFAULT_HEIGHT = 800
SLEEP_AFTER_PROFILE = 0.2

# ✅ 밴드/네이버 계열 로그인 안정용 UA (네가 준 UA 그대로)
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"


class PlaywrightUtils:
    def __init__(self, headless: bool = False):
        self.headless = headless

        self._pw = None
        self.browser = None
        self.context = None
        self.page = None

        self._tmp_profile: Optional[str] = None
        self.last_error: Optional[Exception] = None

    # ----- 내부 유틸 -----
    def _new_tmp_profile(self) -> str:
        base = os.path.join(tempfile.gettempdir(), "playwright_profiles")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"profile_{uuid.uuid4().hex}")
        os.makedirs(path, exist_ok=True)
        return path

    def _wipe_locks(self, path: str):
        # chromium user-data-dir 잔여 락 파일 정리(드물지만 방어)
        for pat in ["Singleton*", "LOCK", "LockFile", "DevToolsActivePort", "lockfile"]:
            for p in glob.glob(os.path.join(path, pat)):
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception:
                    pass

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

    # ----- 외부에서 쓰는 함수 -----
    def start_driver(self, timeout: int = 30):
        """
        ✅ 고수 세팅(밴드/네이버 로그인 안정 최우선)
        - 로컬 Chrome 사용(channel="chrome")
        - 자동화 전용 "고정 프로필"을 LOCALAPPDATA에 저장 (내 크롬 프로필 아님)
          → 캡차/재로그인 빈도 크게 감소, 앱 재설치/업데이트해도 로그인 유지
        - start-maximized + viewport=None (사람 브라우저 느낌)
        - AutomationControlled 등 탐지 완화 옵션
        """
        # === 신규 === 자동화 전용 고정 프로필(로컬 크롬 프로필과 완전 별개)
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        profile_dir = os.path.join(base, "MyCrawlerProfile", "pw_profile")
        os.makedirs(profile_dir, exist_ok=True)

        self._tmp_profile = profile_dir
        self._wipe_locks(self._tmp_profile)
        time.sleep(SLEEP_AFTER_PROFILE)

        try:
            self._pw = sync_playwright().start()

            args = [
                "--start-maximized",  # 창 최대화(사람 느낌)
                "--lang=ko-KR",
                "--disable-blink-features=AutomationControlled",  # 자동화 탐지 완화
                "--disable-dev-shm-usage",  # 로딩 멈춤/스핀 방지(안정)
                "--no-first-run",  # 첫 실행 안내 제거
                "--no-default-browser-check",  # 기본 브라우저 확인 제거
            ]
            if self.headless:
                args += ["--no-sandbox"]

            self.context = self._pw.chromium.launch_persistent_context(
                user_data_dir=self._tmp_profile,
                headless=self.headless,
                viewport=None,  # 최대화 적용 위해 고정 viewport 제거
                args=args,

                channel="chrome",  # ✅ 로컬 Chrome 사용(밴드/네이버 로그인 호환 최강)

                locale="ko-KR",
                timezone_id="Asia/Seoul",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            )

            self.page = self.context.new_page()
            self.page.set_default_timeout(timeout * 1000)
            return self.page

        except Exception as e:
            self.last_error = e
            self.quit()
            raise


    def quit(self):
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        finally:
            self._pw = None
            self.browser = None
            self.context = None
            self.page = None

            if self._tmp_profile and os.path.isdir(self._tmp_profile):
                try:
                    shutil.rmtree(self._tmp_profile, ignore_errors=True)
                except Exception:
                    pass
            self._tmp_profile = None

    # ----- 헬퍼 -----
    def goto(self, url: str, wait_until: str = "networkidle"):
        """
        wait_until: 'load' | 'domcontentloaded' | 'networkidle'
        """
        try:
            self.page.goto(url, wait_until=wait_until)
            return True
        except Exception as e:
            self.last_error = e
            return False

    def wait_selector(self, selector: str, timeout: int = 10):
        try:
            self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except PWTimeoutError as e:
            self.last_error = e
            return False
        except Exception as e:
            self.last_error = e
            return False

    def get_html(self) -> str:
        try:
            return self.page.content()
        except Exception as e:
            self.last_error = e
            return ""

    def get_html_from_mainframe(self) -> str:
        """
        네이버 블로그 구형/일부 스킨에서 본문이 iframe#mainFrame에 들어감
        - 있으면 frame html 반환
        - 없으면 그냥 page html 반환
        """
        try:
            frame = None

            # 1) name 기준
            try:
                frame = self.page.frame(name="mainFrame")
            except Exception:
                frame = None

            # 2) id=mainFrame 요소 기반
            if frame is None:
                try:
                    el = self.page.query_selector("iframe#mainFrame")
                    if el:
                        frame = el.content_frame()
                except Exception:
                    frame = None

            if frame:
                return frame.content()
            return self.page.content()

        except Exception as e:
            self.last_error = e
            try:
                return self.page.content()
            except Exception:
                return ""

    @staticmethod
    def explain_exception(context: str, e: Exception) -> str:
        msg = str(e)
        if "Timeout" in msg:
            return f"⏱️ {context}: 시간 초과"
        return f"❗ {context}: {msg}"
