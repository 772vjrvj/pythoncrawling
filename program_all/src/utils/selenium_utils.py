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
import winreg  # === 신규 ===
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
    def __init__(self, headless: bool = False, debug: Optional[bool] = None):
        self.headless = headless
        self.driver = None
        self._tmp_profile: Optional[str] = None
        self.last_error: Optional[Exception] = None

        # === 신규 ===
        if debug is None:
            debug = os.environ.get("SELENIUMUTILS_DEBUG", "").strip().lower() in ("1", "true", "y", "yes")
        self.debug = bool(debug)

        # === 신규 === 최근 start_driver 환경 기록
        self.last_start_env = {}

    # ----- 내부 유틸 -----
    def _log(self, *args):
        if self.debug:
            print("[SeleniumUtils]", *args)

    def _new_tmp_profile(self) -> str:
        base = os.path.join(tempfile.gettempdir(), "selenium_profiles")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"profile_{uuid.uuid4().hex}")
        os.makedirs(path, exist_ok=True)
        return path

    def _wipe_locks(self, path: str):
        """
        크롬 프로필 락 관련 파일/디렉토리 제거.
        ⚠️ 프로필이 실제로 사용 중일 때 지우면 손상 위험이 있으니,
        start_driver()에서 in-use 체크 후에만 호출하도록 구성.
        """
        for pat in ["Singleton*", "LOCK", "LockFile", "DevToolsActivePort", "lockfile"]:
            for p in glob.glob(os.path.join(path, pat)):
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception:
                    pass

    # === 신규 === Windows: 크롬 경로 찾기
    def _find_chrome_exe_windows(self) -> Optional[str]:
        """
        PATH에 chrome이 없더라도 레지스트리/기본 설치 위치에서 chrome.exe 경로를 최대한 찾는다.
        """
        # 1) uc 내장 탐색 시도
        try:
            p = uc.find_chrome_executable()
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass

        # 2) 레지스트리 탐색
        reg_candidates = [
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon", "version"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Chrome\BLBeacon", "version"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Google\Chrome\BLBeacon", "version"),
        ]

        # version 키만 있으면 경로가 바로 나오진 않으니, 설치 경로 후보도 함께 본다
        path_candidates = []

        # Program Files 후보
        pf = os.environ.get("ProgramFiles")
        pf86 = os.environ.get("ProgramFiles(x86)")
        local = os.environ.get("LOCALAPPDATA")

        if pf:
            path_candidates.append(os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"))
        if pf86:
            path_candidates.append(os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"))
        if local:
            path_candidates.append(os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"))

        # 3) App Paths
        app_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", ""),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", ""),
        ]
        for hive, subkey, value_name in app_paths:
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    v, _ = winreg.QueryValueEx(k, value_name)
                    if v and os.path.isfile(v):
                        return v
            except Exception:
                pass

        # 4) 후보 경로 직접 확인
        for p in path_candidates:
            if p and os.path.isfile(p):
                return p

        # 5) 레지스트리 확인(버전만) 후에도 못 찾으면 None
        # reg_candidates는 참고용으로만 남김 (필요 시 확장 가능)
        for hive, subkey, value_name in reg_candidates:
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    _v, _ = winreg.QueryValueEx(k, value_name)
                    # version 존재 확인만 (경로는 위에서 처리)
                    break
            except Exception:
                pass

        return None

    # === 신규 === 프로필이 실제로 사용 중인지(락 잡힘) 대략 판단
    def _is_profile_in_use(self, profile_dir: str) -> bool:
        """
        크롬 프로필이 다른 크롬 프로세스에 의해 사용 중일 가능성 체크.
        - SingletonLock 파일이 존재하고, Windows에서 파일을 독점 lock 시도했을 때 실패하면 사용 중으로 간주
        """
        lock_path = os.path.join(profile_dir, "SingletonLock")
        if not os.path.exists(lock_path):
            return False

        try:
            import msvcrt
            f = open(lock_path, "a+b")
            try:
                # 1바이트라도 non-blocking lock 시도
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                # lock 획득 성공 -> 사용 중 아닐 확률 높음
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                return False
            except OSError:
                # lock 실패 -> 사용 중
                return True
            finally:
                try:
                    f.close()
                except Exception:
                    pass
        except Exception:
            # 확실치 않으면 "사용 중"으로 잡아 안전하게 처리
            return True

    def _build_options(self):
        opts = uc.ChromeOptions()

        # 기본
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--lang=ko-KR")
        opts.add_argument("--start-maximized")  # window-size보다 사람 느낌

        # 안정성
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")

        # 프로필
        if self._tmp_profile:
            opts.add_argument(f"--user-data-dir={self._tmp_profile}")

        if self.headless:
            opts.add_argument("--headless=new")
            # Windows에선 --no-sandbox가 큰 의미 없지만, headless 안정성 목적이면 유지 가능
            # opts.add_argument("--no-sandbox")  # 필요 시 주석 해제

        return opts

    def _get_chrome_version_text(self) -> Optional[str]:
        """
        Windows에서 chrome.exe를 찾아 `--version` 결과 문자열을 얻는다.
        """
        chrome_exe = self._find_chrome_exe_windows()
        if not chrome_exe:
            return None

        try:
            out = subprocess.check_output(
                [chrome_exe, "--version"],
                stderr=subprocess.STDOUT,
                text=True,
                shell=False
            )
            return out.strip()
        except Exception:
            return None

    def _detect_chrome_major(self) -> Optional[int]:
        """
        Chrome 버전에서 major만 추출.
        예: 'Google Chrome 121.0.6167.85' -> 121
        """
        try:
            out = self._get_chrome_version_text()
            if not out:
                return None
            m = re.search(r"(\d+)\.", out)
            if m:
                return int(m.group(1))
        except Exception:
            pass
        return None

    def _parse_major_from_error(self, e: Exception) -> Optional[int]:
        msg = str(e)

        # 자주 나오는 패턴들 커버
        # "Current browser version is 121.0.6167.85 with binary path ..."
        m = re.search(r"Current browser version is (\d+)", msg)
        if m:
            return int(m.group(1))

        # 혹시 다른 형태로 나올 때 대비
        m = re.search(r"browser version (\d+)", msg, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None

        return None

    def _wipe_uc_driver_cache(self):
        candidates = [
            os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "undetected_chromedriver"),
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "undetected_chromedriver"),
        ]
        for base in candidates:
            try:
                if os.path.isdir(base):
                    for p in glob.glob(os.path.join(base, "**", "chromedriver*.exe"), recursive=True):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                    for p in glob.glob(os.path.join(base, "**", "chromedriver*"), recursive=True):
                        if os.path.isfile(p):
                            try:
                                os.remove(p)
                            except Exception:
                                pass
            except Exception:
                pass

    def _get_driver_path_for_major(self, major: int) -> str:
        patcher = Patcher(version_main=major)
        patcher.auto()
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

    # === 신규 === 드라이버 생성 공통
    def _create_uc_driver(self, opts, major: Optional[int]):
        if major:
            driver_path = self._get_driver_path_for_major(major)
            self._log("using driver major:", major, "| driver_path:", driver_path)
            return uc.Chrome(options=opts, driver_executable_path=driver_path)
        else:
            self._log("using driver major: None (uc auto)")
            return uc.Chrome(options=opts)

    # ----- 외부에서 쓰는 함수 -----
    def start_driver(self, timeout: int = 30):
        """
        Windows 기준 안정화 버전:
        - chrome.exe 경로 탐색 + --version으로 major 확보
        - 고정 프로필 기본 사용(캡차/로그인 유지)
        - 프로필이 사용 중으로 판단되면 임시 프로필로 안전 fallback
        - SessionNotCreatedException 시 UC 캐시 wipe + major 재시도
        """

        # ✅ 고정 프로필(권장) : 캡차/로그인 유지
        fixed_profile_dir = os.path.join(
            os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
            "MyCrawlerProfile",
            "selenium_profile"
        )
        os.makedirs(fixed_profile_dir, exist_ok=True)

        # === 신규 === start 환경 기록
        self.last_start_env = {
            "headless": self.headless,
            "timeout": timeout,
            "fixed_profile_dir": fixed_profile_dir,
        }

        # 1) 고정 프로필이 다른 크롬에서 사용 중이면 임시 프로필로 fallback
        use_profile = fixed_profile_dir
        if self._is_profile_in_use(fixed_profile_dir):
            tmp = self._new_tmp_profile()
            self._log("fixed profile seems in-use -> fallback tmp profile:", tmp)
            use_profile = tmp
            self.last_start_env["profile_fallback"] = True
        else:
            self.last_start_env["profile_fallback"] = False

        self._tmp_profile = use_profile

        # 2) 사용 중이 아닌 경우에만 lock 파일 정리 (손상 방지)
        if self._tmp_profile == fixed_profile_dir:
            self._wipe_locks(self._tmp_profile)
            time.sleep(SLEEP_AFTER_PROFILE)

        major = self._detect_chrome_major()
        self.last_start_env["chrome_major"] = major
        self.last_start_env["chrome_version_text"] = self._get_chrome_version_text()

        last = None

        try:
            opts = self._build_options()
            self.driver = self._create_uc_driver(opts, major)

            try:
                self.driver.set_page_load_timeout(timeout)
            except Exception:
                pass

            self._place_left_half()
            return self.driver

        except SessionNotCreatedException as e:
            last = e
            self._safe_quit_driver()

            # 꼬인 드라이버 캐시 정리 후 재시도
            self._wipe_uc_driver_cache()

            parsed = self._parse_major_from_error(e) or major
            self.last_start_env["session_not_created_parsed_major"] = parsed

            if parsed:
                try:
                    opts = self._build_options()
                    self.driver = self._create_uc_driver(opts, parsed)

                    try:
                        self.driver.set_page_load_timeout(timeout)
                    except Exception:
                        pass

                    self._place_left_half()
                    return self.driver
                except Exception as e2:
                    self.last_error = e2
                    raise e2

            self.last_error = last
            raise last

        except Exception as e:
            last = e
            self._safe_quit_driver()
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
