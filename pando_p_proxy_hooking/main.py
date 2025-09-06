# -*- coding: utf-8 -*-
"""
SeleniumUtils (최종)
- 기본 동작(안정 모드): 새 임시 프로필 + undetected-chromedriver(UC)
  * 1차: 숨김(오프스크린) 시도 → 성공 시 화면 복귀
  * 2차: 같은 에러(SessionNotCreated)면 보이는 창으로 1회 재시도
- user=True일 때: 실제 유저 프로필(로그인/쿠키 그대로)로 크롬 실행 후 attach
  * 기존에 크롬이 떠 있으면 충돌 가능 → force_close=True로 모두 종료 후 실행 권장
  * attach 실패 시 안전하게 "안정 모드"로 폴백 (기존 동작 보존)
"""

import os
import ssl
import time
import shutil
import tempfile
import glob
import traceback
import psutil
import uuid
import subprocess
import socket
import platform

from selenium import webdriver
from selenium.common import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException,
    ElementClickInterceptedException, ElementNotInteractableException, InvalidSelectorException
)
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc

# 네트워크 검사 회피(일부 환경)
ssl._create_default_https_context = ssl._create_unverified_context

# 튜닝 파라미터
SLEEP_AFTER_KILL    = 0.8   # 크롬/드라이버 프로세스 정리 직후 대기
SLEEP_AFTER_PROFILE = 0.5   # 새 프로필 생성 직후 대기 (EDR/락 완화)
DEFAULT_WIDTH       = 1200
DEFAULT_HEIGHT      = 800


class SeleniumUtils:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.last_error = None
        self._temp_profile_dir = None
        self._launched_proc = None  # user=True attach 모드로 띄운 크롬 프로세스 보관

    # ----------------- 내부 공통 -----------------
    def _new_profile_dir(self):
        """
        고유 임시 프로필 디렉터리 생성.
        환경변수 SEL_PROFILES_DIR 지정 시 해당 경로 하위에 생성.
        """
        base = os.environ.get("SEL_PROFILES_DIR") or os.path.join(tempfile.gettempdir(), "selenium_profiles")
        os.makedirs(base, exist_ok=True)
        d = os.path.join(base, f"profile_{uuid.uuid4().hex}")
        os.makedirs(d, exist_ok=True)
        return d

    def _wipe_singleton_locks(self, pdir):
        """크롬 프로필 락 파일 제거"""
        for pat in ["Singleton*", "lockfile", "LOCK", "LockFile"]:
            for f in glob.glob(os.path.join(pdir, pat)):
                try:
                    if os.path.isdir(f):
                        shutil.rmtree(f, ignore_errors=True)
                    else:
                        os.remove(f)
                except Exception:
                    pass

    def _close_chrome_processes(self):
        """남아있는 크롬/드라이버 강제 종료"""
        targets = {"chrome.exe", "chromedriver.exe"}
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                n = (p.info.get("name") or "").lower()
                if n in targets:
                    p.kill()
            except Exception:
                pass

    def _cleanup_profile(self):
        """임시 프로필 정리"""
        if self._temp_profile_dir and os.path.isdir(self._temp_profile_dir):
            try:
                shutil.rmtree(self._temp_profile_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_profile_dir = None

    def _free_port(self):
        with socket.socket() as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def _is_any_chrome_running(self):
        for p in psutil.process_iter(["name"]):
            try:
                if (p.info.get("name") or "").lower() == "chrome.exe":
                    return True
            except Exception:
                continue
        return False

    def _default_chrome_binary(self):
        """
        기본 크롬 바이너리 경로 탐색.
        - CFT_BINARY 환경변수 우선
        - OS별 기본 경로
        - 마지막으로 'chrome'(PATH)
        """
        env = os.environ.get("CFT_BINARY")
        if env and os.path.exists(env):
            return env

        system = platform.system().lower()
        candidates = []
        if system == "windows":
            candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
        elif system == "darwin":
            candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        else:
            candidates = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/snap/bin/chromium"]

        for c in candidates:
            if os.path.exists(c):
                return c
        return "chrome"  # PATH 의존

    # ----------------- 드라이버 빌드 -----------------
    def _try_build_uc(self, hidden=False):
        """
        undetected-chromedriver로 생성 (항상 새 프로필).
        hidden=True면 1차 시도를 오프스크린/최소화로 띄워 사용자 깜빡임 제거.
        """
        self.last_error = None
        self._temp_profile_dir = self._new_profile_dir()
        self._wipe_singleton_locks(self._temp_profile_dir)
        time.sleep(SLEEP_AFTER_PROFILE)  # 프로필 락/EDR 스캔 완화

        try:
            o = uc.ChromeOptions()
            o.add_argument("--disable-blink-features=AutomationControlled")
            o.add_argument(f"--user-data-dir={self._temp_profile_dir}")

            if self.headless:
                o.add_argument("--headless=new")
                o.add_argument("--no-sandbox")
                o.add_argument("--disable-dev-shm-usage")

            # 1차 시도는 사용자에게 안 보이게 띄우고, 성공 시 바로 위치/크기 복구
            if hidden and not self.headless:
                o.add_argument("--start-minimized")
                o.add_argument("--window-position=-32000,-32000")

            # 드라이버 생성
            self.driver = uc.Chrome(options=o)

            # hidden으로 띄웠다면 성공 직후 화면 안으로 즉시 복귀
            if hidden and not self.headless:
                try:
                    self.driver.set_window_position(0, 0)
                    self.driver.set_window_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)
                except Exception:
                    pass

            return True

        except SessionNotCreatedException as e:
            # 초기 락/EDR 타이밍으로 실패 가능 → 상위에서 조건부 1회 재시도
            self.last_error = e
            self._cleanup_profile()
            self.driver = None
            return False

        except Exception as e:
            self.last_error = e
            self._cleanup_profile()
            self.driver = None
            return False

    def _try_attach_user_profile(self, timeout, user_profile_dir, profile_name, headless):
        """
        실제 사용자 프로필(로그인/쿠키 유지)로 크롬을 직접 실행 후 Selenium attach.
        실패 시 False 반환(상위에서 안전 폴백).
        """
        try:
            # 크롬 기동 (원격 디버깅 ON, 실제 유저 프로필)
            port = self._free_port()
            chrome_bin = self._default_chrome_binary()

            args = [
                chrome_bin,
                f"--remote-debugging-port={port}",
                f"--user-data-dir={user_profile_dir}",
                f"--profile-directory={profile_name}",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--new-window",
                "--window-position=0,0",
                f"--window-size={DEFAULT_WIDTH},{DEFAULT_HEIGHT}",
            ]
            if headless:
                # 실제 유저 프로필을 headless로 쓰는 건 의미가 적지만, 옵션은 허용
                args += ["--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]

            # 먼저 크롬을 직접 띄움(한 번만 뜸)
            self._launched_proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.8)  # 초기화 대기

            # Selenium은 새 창을 만들지 않고, 지금 뜬 크롬에 'attach'
            opts = webdriver.ChromeOptions()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            self.driver = webdriver.Chrome(options=opts)

            try:
                self.driver.set_page_load_timeout(timeout)
            except Exception as e:
                print(f"⚠️ set_page_load_timeout 실패(무시): {e}")

            return True

        except Exception as e:
            self.last_error = e
            # attach 모드 실패 시 띄운 프로세스 정리
            try:
                if self._launched_proc:
                    self._launched_proc.terminate()
            except Exception:
                pass
            self._launched_proc = None
            self.driver = None
            return False

    # ----------------- 시작/종료 -----------------
    def start_driver(self, timeout=30, user=None, mode="default", **kwargs):
        """
        기존 시그니처 보존(start_driver(timeout, user, mode)):
        - user가 True로 전달되면 "실제 유저 프로필" 사용 시도로 해석.
          * 옵션(kw):
            - user_profile_dir: 사용자 프로필 루트 경로
              · Win 기본: %LOCALAPPDATA%\\Google\\Chrome\\User Data
              · macOS 기본: ~/Library/Application Support/Google/Chrome
              · Linux 기본: ~/.config/google-chrome
            - profile_name: 'Default', 'Profile 1' 등 (기본값 'Default')
            - force_close: True면 기존 크롬 모두 종료 후 시작(권장)
        - user가 False/None이면 "안정 모드"(임시 프로필 + UC, 조건부 1회 재시도)
        """
        use_user_profile = bool(user)
        force_close = bool(kwargs.get("force_close", False))
        profile_name = kwargs.get("profile_name", "Default")
        headless = self.headless if kwargs.get("headless") is None else bool(kwargs.get("headless"))

        # 사용자 프로필 기본 경로
        user_profile_dir = kwargs.get("user_profile_dir")
        if not user_profile_dir and use_user_profile:
            system = platform.system().lower()
            if system == "windows":
                user_profile_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
            elif system == "darwin":
                user_profile_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            else:
                user_profile_dir = os.path.expanduser("~/.config/google-chrome")

        # --- user=True: 실제 유저 프로필 attach 모드 ---
        if use_user_profile:
            # 충돌 방지: 기존 크롬 떠 있으면 종료하거나(권장) 폴백
            if self._is_any_chrome_running():
                if force_close:
                    self._close_chrome_processes()
                    time.sleep(SLEEP_AFTER_KILL)
                else:
                    print("⚠️ Chrome이 이미 실행 중 → user 프로필 attach 건너뛰고 안정 모드로 폴백합니다.")
                    # 아래에서 안정 모드로 진행

            else:
                # attach 시도
                ok_attach = self._try_attach_user_profile(timeout, user_profile_dir, profile_name, headless)
                if ok_attach:
                    # 버전 로그(진단용)
                    try:
                        caps = getattr(self.driver, "capabilities", {}) or {}
                        print("✅ (user attach)",
                              "Chrome", caps.get("browserVersion"),
                              "| chromedriver", (caps.get("chrome", {}) or {}).get("chromedriverVersion"))
                    except Exception:
                        pass
                    return self.driver
                else:
                    print("⚠️ user 프로필 attach 실패 → 안정 모드로 폴백합니다.")

        # --- 안정 모드: 임시 프로필 + UC (기존 동작) ---
        self._close_chrome_processes()
        time.sleep(SLEEP_AFTER_KILL)

        # 1차: 오프스크린(깜빡임 제거)
        ok = self._try_build_uc(hidden=True)

        # 2차: 같은 에러(SessionNotCreated)일 때만 보이는 창으로 1회 재시도
        if not ok and isinstance(self.last_error, SessionNotCreatedException):
            time.sleep(SLEEP_AFTER_PROFILE)
            ok = self._try_build_uc(hidden=False)

        if not ok:
            raise RuntimeError(f"Chrome driver init failed: {self.last_error}")

        # 세션 체크
        try:
            _ = self.driver.current_window_handle
        except Exception as e:
            self.quit()
            raise RuntimeError(f"Driver session invalid after init: {e}")

        # 타임아웃 설정
        try:
            self.driver.set_page_load_timeout(timeout)
        except Exception as e:
            print(f"⚠️ set_page_load_timeout 실패(무시): {e}")

        # 버전 로그 (진단용)
        try:
            caps = getattr(self.driver, "capabilities", {}) or {}
            print("✅",
                  "Chrome", caps.get("browserVersion"),
                  "| chromedriver", (caps.get("chrome", {}) or {}).get("chromedriverVersion"))
        except Exception:
            pass

        return self.driver

    def quit(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None
            # attach 모드로 띄운 실제 크롬 종료
            if self._launched_proc:
                try:
                    self._launched_proc.terminate()
                except Exception:
                    pass
                self._launched_proc = None
            self._cleanup_profile()  # 임시 프로필 모드일 때만 의미 있음

    # ----------------- 유틸 -----------------
    def wait_element(self, driver, by, selector, timeout=10):
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        except Exception as e:
            self.handle_selenium_exception(f"wait_element: [{selector}] timeout {timeout}s", e)
            return None

    def handle_selenium_exception(self, context, exception):
        if isinstance(exception, NoSuchElementException): return f"❌ {context} - 요소 없음"
        if isinstance(exception, StaleElementReferenceException): return f"❌ {context} - Stale 요소"
        if isinstance(exception, TimeoutException): return f"⏱️ {context} - 로딩 시간 초과"
        if isinstance(exception, ElementClickInterceptedException): return f"🚫 {context} - 클릭 방해"
        if isinstance(exception, ElementNotInteractableException): return f"🚫 {context} - 비활성 요소"
        if isinstance(exception, InvalidSelectorException): return f"🚫 {context} - 선택자 오류"
        if isinstance(exception, WebDriverException): return f"⚠️ {context} - WebDriver 오류"
        return f"❗ {context} - 알 수 없는 오류"


# ---- 간단 자가 테스트 ----
if __name__ == "__main__":
    # 1) 기본(안정 모드)
    # u = SeleniumUtils(headless=False)
    # d = None
    # try:
    #     d = u.start_driver(timeout=20)  # user 인자 없이 → 안정 모드
    #     d.get("https://example.com")
    #     print("TITLE:", d.title)
    # finally:
    #     u.quit()

    # 2) 실제 유저 프로필 attach (원할 때 테스트)
    u2 = SeleniumUtils(headless=False)
    d2 = None
    try:
        d2 = u2.start_driver(timeout=20, user=True, force_close=True, profile_name="Default")
        d2.get("https://example.com")
        print("TITLE(user):", d2.title)
    finally:
        u2.quit()
