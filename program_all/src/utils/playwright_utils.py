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
        selenium의 start_driver()처럼 main에서 바로 쓸 수 있게 page를 반환
        """
        self._tmp_profile = self._new_tmp_profile()
        self._wipe_locks(self._tmp_profile)
        time.sleep(SLEEP_AFTER_PROFILE)

        try:
            self._pw = sync_playwright().start()

            # ✅ chromium 사용
            # - user_data_dir 사용하면 'persistent context'로 뜸
            # - headless, window-size 설정 가능
            args = [
                f"--window-size={DEFAULT_WIDTH},{DEFAULT_HEIGHT}",
                "--lang=ko-KR",
            ]
            if self.headless:
                args += ["--no-sandbox", "--disable-dev-shm-usage"]

            self.context = self._pw.chromium.launch_persistent_context(
                user_data_dir=self._tmp_profile,
                headless=self.headless,
                viewport={"width": DEFAULT_WIDTH, "height": DEFAULT_HEIGHT},
                args=args,
            )

            self.page = self.context.new_page()
            self.page.set_default_timeout(timeout * 1000)

            # 화면 배치(좌측 반) - headless면 의미 없음
            if not self.headless:
                try:
                    sw, sh = self._get_screen_size()
                    # playwright는 set_window_rect 같은 API가 없어서 viewport로만 충분히 처리
                    # (실제 윈도우 위치 제어는 OS별로 번거로워서 생략)
                except Exception:
                    pass

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
        네이버 블로그는 networkidle + selector 대기 조합이 안정적
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
            # frame(name='mainFrame') 또는 frame with url includes 'PostView' 등의 케이스가 있음
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
