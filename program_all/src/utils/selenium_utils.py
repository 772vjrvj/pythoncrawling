# -*- coding: utf-8 -*-
"""
SeleniumUtils (2025-09-07 수정판)
- 기존 인터페이스(start_driver 등) 그대로 유지
- 항상 새로운 브라우저(임시 프로필)
- 창을 왼쪽 절반으로 배치(set_window_rect)
"""

import os, time, glob, shutil, tempfile, uuid
from typing import Optional, Tuple

import undetected_chromedriver as uc
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException,
    ElementClickInterceptedException, ElementNotInteractableException,
    InvalidSelectorException, WebDriverException, SessionNotCreatedException,
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

    # --- 화면 해상도 감지 & 배치 ---
    def _get_screen_size(self) -> Tuple[int, int]:
        """
        기본/대체 순서:
        1) tkinter로 해상도 조회
        2) 실패 시 보편적 1920x1080 가정
        """
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
        return 1920, 1080  # fallback

    def _place_left_half(self):
        """
        브라우저 창을 왼쪽 절반으로 이동/리사이즈
        (headless면 위치 개념이 없으므로 건너뜀)
        """
        if not self.driver or self.headless:
            return
        sw, sh = self._get_screen_size()
        # Windows DPI 스케일링 환경에서도 안정적인 set_window_rect 사용
        try:
            self.driver.set_window_rect(x=0, y=0, width=max(600, sw // 2), height=max(600, sh))
        except Exception:
            # 일부 환경에서 set_window_rect 미지원이면 size/position 별도 호출
            try:
                self.driver.set_window_position(0, 0)
                self.driver.set_window_size(max(600, sw // 2), max(600, sh // 2))
            except Exception:
                pass

    # ----- 외부에서 쓰는 함수 -----
    def start_driver(self, timeout: int = 30, **kwargs):
        """
        기존 코드 호환용 함수
        - 항상 새 브라우저(임시 프로필)만 실행
        - user, persist_profile_dir 같은 파라미터는 무시
        - 생성 직후 창을 왼쪽 절반으로 배치
        """
        # 임시 프로필 생성
        self._tmp_profile = self._new_tmp_profile()
        self._wipe_locks(self._tmp_profile)
        time.sleep(SLEEP_AFTER_PROFILE)

        opts = uc.ChromeOptions()
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument(f"--user-data-dir={self._tmp_profile}")
        opts.add_argument(f"--window-size={DEFAULT_WIDTH},{DEFAULT_HEIGHT}")
        opts.add_argument("--lang=ko-KR")
        if self.headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = uc.Chrome(options=opts)
            try:
                self.driver.set_page_load_timeout(timeout)
            except Exception:
                pass

            # 👉 여기서 창을 왼쪽 절반으로 배치
            self._place_left_half()

            return self.driver
        except SessionNotCreatedException as e:
            self.last_error = e
            time.sleep(0.5)
            self.driver = uc.Chrome(options=opts)
            # 재시작 후에도 배치 적용
            self._place_left_half()
            return self.driver
        except Exception as e:
            self.last_error = e
            self.quit()
            raise

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
