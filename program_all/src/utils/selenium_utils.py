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
import json
import base64  # CDP getResponseBody가 base64로 오는 케이스 대응
import winreg
from typing import Optional, Dict, Any, List

import undetected_chromedriver as uc
from undetected_chromedriver.patcher import Patcher  # 배포 PC 크롬버전 mismatch 방지(자동 패치)

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


# 기본 윈도우 크기(참고용)
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 800

# 고정 프로필 락 파일 정리 후 약간 대기(Chrome이 lock 재생성 타이밍이 있어 필요)
SLEEP_AFTER_PROFILE = 0.3


class SeleniumUtils:
    def __init__(self, headless: bool = False, debug: Optional[bool] = None):
        """
        headless : True면 브라우저 UI 없이 실행
        debug    : True면 내부 로그 출력

        [빌드/배포 주의]
        - PyInstaller onefile/onedir 모두에서 동작 가능하도록
          chrome.exe 위치 탐색/driver mismatch 대응을 내부에서 처리한다.
        """
        self.headless: bool = headless
        self.driver: Any = None  # selenium webdriver (타입 힌트 최소화)
        self.last_error: Optional[Exception] = None

        # debug 인자 없으면 환경변수로도 켤 수 있게
        if debug is None:
            debug = os.environ.get("SELENIUMUTILS_DEBUG", "").strip().lower() in ("1", "true", "y", "yes")
        self.debug: bool = bool(debug)

        # 실행 시 사용할 프로필 폴더(고정 or 임시)
        self._profile_dir: Optional[str] = None

        # capture_enabled=True : perf log 기반으로 requestId를 잡고 Network.getResponseBody로 응답 JSON을 가져온다.
        # block_images=True   : 이미지 로딩 차단(성능/트래픽 감소) - driver 시작 전에만 적용됨
        self.capture_enabled: bool = False
        self.block_images: bool = False

        # 내부 상태(캡처/지원 여부)
        self._net_enabled: bool = False
        self._perf_supported: Optional[bool] = None

        # start_driver 당시 환경 기록(고객PC 디버깅용)
        self.last_start_env: Dict[str, Any] = {}

    # =========================================================
    # log
    # =========================================================
    def _log(self, *args: Any) -> None:
        if self.debug:
            print("[SeleniumUtils]", *args)

    # =========================================================
    # capture options
    # =========================================================
    def set_capture_options(self, enabled: bool, block_images: Optional[bool] = None) -> None:
        """
        CDP 네트워크 캡처 사용 여부와 이미지 차단 옵션을 설정한다.

        - enabled=True
          driver 생성 시 performance log 수집을 켜서, 네트워크 이벤트(요청/응답)에서 requestId를 잡을 수 있게 한다.
        - block_images=True
          이미지 로딩을 차단해 속도/트래픽을 줄인다. (Chrome prefs라 driver 시작 전에만 적용됨)
        """
        self.capture_enabled = bool(enabled)
        if block_images is not None:
            self.block_images = bool(block_images)

    def enable_capture_now(self) -> bool:
        """CDP Network.enable을 실행하여 네트워크 캡처를 시작한다(실패 시 False)."""
        try:
            self.driver.execute_cdp_cmd("Network.enable", {})
            self._net_enabled = True
            self._log("CDP Network.enable 성공")
            return True
        except Exception as e:
            self._net_enabled = False
            self._log("❌ CDP Network.enable 실패:", str(e))
            return False

    # =========================================================
    # profile
    # =========================================================
    def _new_tmp_profile(self) -> str:
        """
        임시 프로필 생성:
        - 고정 프로필이 사용 중(다른 크롬/다른 자동화)일 때 fallback용
        - tempfile 아래 생성 -> 종료 시 삭제 가능
        """
        base = os.path.join(tempfile.gettempdir(), "selenium_profiles")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"profile_{uuid.uuid4().hex}")
        os.makedirs(path, exist_ok=True)
        return path

    def _wipe_locks(self, path: str) -> None:
        """
        고정 프로필 사용 시 남아있는 lock 파일 제거
        - DevToolsActivePort가 남아있으면 크롬이 즉시 종료되거나 연결 실패하는 케이스가 있다.
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

    def _is_profile_in_use(self, profile_dir: str) -> bool:
        """
        프로필 사용 중 추정:
        - SingletonLock 존재로 빠르게 판단
        """
        lock_path = os.path.join(profile_dir, "SingletonLock")
        return os.path.exists(lock_path)

    def _wait_profile_unlock(self, profile_dir: str, timeout_sec: float = 6.0, poll: float = 0.2) -> bool:
        """
        재시작 직후 SingletonLock이 잠깐 남는 타이밍 이슈가 있어,
        일정 시간 기다리면서 lock이 풀리기를 대기한다.
        """
        t0 = time.time()
        while time.time() - t0 < float(timeout_sec):
            if not self._is_profile_in_use(profile_dir):
                return True
            time.sleep(float(poll))
        return not self._is_profile_in_use(profile_dir)

    # =========================================================
    # chrome version / uc patcher
    # =========================================================
    def _find_chrome_exe_windows(self) -> Optional[str]:
        """chrome.exe 경로 찾기 (배포/고객PC에서 중요)."""
        try:
            p = uc.find_chrome_executable()
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass

        pf = os.environ.get("ProgramFiles")
        pf86 = os.environ.get("ProgramFiles(x86)")
        local = os.environ.get("LOCALAPPDATA")

        candidates: List[str] = []
        if pf:
            candidates.append(os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"))
        if pf86:
            candidates.append(os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"))
        if local:
            candidates.append(os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"))

        # 레지스트리(가능하면)
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", ""),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", ""),
        ]
        for hive, subkey, value_name in reg_paths:
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    v, _ = winreg.QueryValueEx(k, value_name)
                    if v and os.path.isfile(v):
                        return v
            except Exception:
                pass

        for p in candidates:
            if p and os.path.isfile(p):
                return p

        return None

    def _detect_chrome_major(self) -> Optional[int]:
        """
        크롬 major 버전 추출:
        - chromedriver mismatch(SessionNotCreatedException) 방지 핵심
        """
        chrome = self._find_chrome_exe_windows()
        if not chrome:
            return None
        try:
            out = subprocess.check_output([chrome, "--version"], stderr=subprocess.STDOUT, text=True)
            m = re.search(r"(\d+)\.", out or "")
            return int(m.group(1)) if m else None
        except Exception:
            return None

    def _get_driver_path_for_major(self, major: int) -> str:
        """uc patcher로 해당 major용 chromedriver 내려받고 경로를 받는다."""
        patcher = Patcher(version_main=major)
        patcher.auto()
        return patcher.executable_path

    def _wipe_uc_driver_cache(self) -> None:
        """
        undetected_chromedriver 캐시 드라이버 제거:
        - 배포 시 오래된 드라이버가 남아 mismatch를 유발하는 케이스가 있다.
        """
        bases = [
            os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "undetected_chromedriver"),
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "undetected_chromedriver"),
        ]
        for base in bases:
            try:
                if os.path.isdir(base):
                    for p in glob.glob(os.path.join(base, "**", "chromedriver*"), recursive=True):
                        if os.path.isfile(p):
                            try:
                                os.remove(p)
                            except Exception:
                                pass
            except Exception:
                pass

    # =========================================================
    # options
    # =========================================================
    def _build_options(self) -> Any:
        """
        크롬 옵션 구성

        [중요]
        - capture_enabled=True일 때만 performance log capability를 켠다. (driver 생성 시점에만 반영)
        - block_images=True일 때만 이미지 차단 prefs를 적용한다.
        """
        opts = uc.ChromeOptions()

        opts.add_argument("--lang=ko-KR")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-popup-blocking")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-quic")
        opts.add_argument("--remote-allow-origins=*")
        opts.add_argument("--log-level=3")
        opts.add_argument("--start-maximized")

        if self.headless:
            opts.add_argument("--headless=new")

        # 이미지 차단 토글(사이트가 깨지면 False로)
        if self.block_images:
            opts.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            })

        # perf log capability는 driver 생성 시점에만 반영됨
        if self.capture_enabled:
            opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        if self._profile_dir:
            opts.add_argument(f"--user-data-dir={self._profile_dir}")

        return opts

    # =========================================================
    # CDP / performance logs
    # =========================================================
    def _ensure_perf_supported(self) -> bool:
        """
        performance log 지원 여부를 확인한다.
        - 지원하지 않으면 get_log("performance")에서 예외가 날 수 있다.
        """
        if self._perf_supported is not None:
            return bool(self._perf_supported)

        try:
            _ = self.driver.get_log("performance")
            self._perf_supported = True
        except Exception as e:
            self._perf_supported = False
            self._log("performance log not supported:", str(e))
        return bool(self._perf_supported)

    # =========================================================
    # request capture
    # =========================================================
    def wait_api_request(
            self,
            url_contains: str,
            query_contains: Optional[str] = None,
            timeout_sec: float = 15.0,
            poll: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        """performance log에서 특정 API 요청(requestWillBeSent) 정보를 찾는다(응답 body 없음)."""
        if not self.capture_enabled:
            return None

        if not self._net_enabled:
            if not self.enable_capture_now():
                return None

        if not self._ensure_perf_supported():
            return None

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            logs = self.driver.get_log("performance")

            for row in logs or []:
                msg = row.get("message") if isinstance(row, dict) else None
                if not msg:
                    continue
                if "Network.requestWillBeSent" not in msg:
                    continue
                if url_contains not in msg:
                    continue
                if query_contains and query_contains not in msg:
                    continue

                j = json.loads(msg)
                m = (j or {}).get("message") or {}
                if m.get("method") != "Network.requestWillBeSent":
                    continue

                params = m.get("params") or {}
                req = params.get("request") or {}
                url = req.get("url") or ""

                if url_contains not in url:
                    continue
                if query_contains and query_contains not in url:
                    continue

                return {
                    "requestId": params.get("requestId"),
                    "url": url,
                    "method": req.get("method"),
                    "headers": req.get("headers"),
                    "postData": req.get("postData"),
                }

            time.sleep(poll)

        return None

    def _get_response_body(self, request_id: str) -> Optional[str]:
        """
        CDP Network.getResponseBody로 body를 얻는다.
        - base64Encoded 인 경우 디코딩 처리
        """
        if not request_id:
            return None

        try:
            res = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            if not isinstance(res, dict):
                return None

            body = res.get("body")
            if body is None:
                return None

            if res.get("base64Encoded"):
                return base64.b64decode(body).decode("utf-8", "replace")

            return str(body)
        except Exception:
            return None

    def wait_api_body(
            self,
            url_contains: str,
            query_contains: Optional[str] = None,
            timeout_sec: float = 15.0,
            poll: float = 0.2,
            require_status_200: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        performance log에서 responseReceived/loadingFinished를 매칭해 requestId를 잡고,
        Network.getResponseBody로 응답 내용을 가져온다.
        """
        if not self.capture_enabled:
            self._log("capture_enabled is False -> wait_api_body skip")
            return None

        if not self._net_enabled:
            if not self.enable_capture_now():
                return None

        if not self._ensure_perf_supported():
            return None

        candidates: Dict[str, Dict[str, Any]] = {}
        finished: set[str] = set()
        failed: set[str] = set()

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            logs = self.driver.get_log("performance")

            for row in logs or []:
                msg = row.get("message") if isinstance(row, dict) else None
                if not msg:
                    continue

                # responseReceived
                if "Network.responseReceived" in msg and (url_contains in msg) and (query_contains is None or query_contains in msg):
                    j = json.loads(msg)
                    m = (j or {}).get("message") or {}
                    if m.get("method") != "Network.responseReceived":
                        continue

                    params = m.get("params") or {}
                    resp = params.get("response") or {}
                    url = resp.get("url") or ""

                    if url_contains not in url:
                        continue
                    if query_contains and query_contains not in url:
                        continue

                    status = int(resp.get("status") or 0)
                    if require_status_200 and status != 200:
                        continue

                    rid = params.get("requestId")
                    if not rid:
                        continue

                    candidates[rid] = {
                        "requestId": rid,
                        "url": url,
                        "status": status,
                        "mimeType": resp.get("mimeType"),
                    }
                    continue

                # loadingFinished / loadingFailed
                if ("Network.loadingFinished" in msg) or ("Network.loadingFailed" in msg):
                    j = json.loads(msg)
                    m = (j or {}).get("message") or {}
                    method = m.get("method")
                    params = m.get("params") or {}
                    rid = params.get("requestId")
                    if not rid:
                        continue

                    if method == "Network.loadingFinished":
                        finished.add(rid)
                    elif method == "Network.loadingFailed":
                        failed.add(rid)

            for rid, meta in list(candidates.items()):
                if rid in failed:
                    candidates.pop(rid, None)
                    continue
                if rid not in finished:
                    continue

                body_text = self._get_response_body(rid)
                if body_text:
                    out = dict(meta)
                    out["bodyText"] = body_text
                    return out

            time.sleep(poll)

        return None

    def wait_api_json(
            self,
            url_contains: str,
            query_contains: Optional[str] = None,
            timeout_sec: float = 15.0,
            poll: float = 0.2,
            require_status_200: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """wait_api_body() 결과 bodyText를 JSON으로 파싱해서 반환 (JSON이 아니면 None)."""
        hit = self.wait_api_body(
            url_contains=url_contains,
            query_contains=query_contains,
            timeout_sec=timeout_sec,
            poll=poll,
            require_status_200=require_status_200,
        )
        if not hit:
            return None

        text = hit.get("bodyText") or ""
        if not text:
            return None

        try:
            return json.loads(text)
        except Exception:
            return None

    # =========================================================
    # start / quit
    # =========================================================
    def start_driver(
            self,
            timeout: int = 30,
            force_profile_dir: Optional[str] = None,
            allow_profile_fallback: bool = True
    ) -> Any:
        """
        Windows 기준 안정화:
        - 고정 프로필 기본 사용(로그인 유지)
        - 프로필이 사용 중이면 임시 프로필로 fallback
        - Chrome major 감지 후 해당 major로 uc patcher 적용

        - force_profile_dir: 지정되면 그 프로필을 "무조건" 사용 시도
        - allow_profile_fallback=False면, lock이 남아도 tmp profile로 절대 안 빠지고 재시도/대기 쪽으로만 간다.
        """
        fixed_profile_dir = os.path.join(
            os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
            "MyCrawlerProfile",
            "selenium_profile",
            )
        os.makedirs(fixed_profile_dir, exist_ok=True)

        chosen_profile = force_profile_dir or fixed_profile_dir

        self.last_start_env = {
            "headless": self.headless,
            "timeout": timeout,
            "fixed_profile_dir": fixed_profile_dir,
            "chosen_profile_dir": chosen_profile,
            "force_profile_dir": bool(force_profile_dir),
            "allow_profile_fallback": bool(allow_profile_fallback),
            "capture_enabled_at_start": bool(self.capture_enabled),
            "block_images_at_start": bool(self.block_images),
        }

        if force_profile_dir:
            self._profile_dir = force_profile_dir
            self._wipe_locks(self._profile_dir)
            self._wait_profile_unlock(self._profile_dir, timeout_sec=6.0, poll=0.2)
            time.sleep(SLEEP_AFTER_PROFILE)
        else:
            if self._is_profile_in_use(chosen_profile):
                if allow_profile_fallback:
                    self._profile_dir = self._new_tmp_profile()
                    self.last_start_env["profile_fallback"] = True
                    self._log("fixed profile in-use -> tmp profile:", self._profile_dir)
                else:
                    self._profile_dir = chosen_profile
                    self.last_start_env["profile_fallback"] = False
                    self._wipe_locks(self._profile_dir)
                    self._wait_profile_unlock(self._profile_dir, timeout_sec=8.0, poll=0.2)
                    time.sleep(SLEEP_AFTER_PROFILE)
            else:
                self._profile_dir = chosen_profile
                self.last_start_env["profile_fallback"] = False
                self._wipe_locks(self._profile_dir)
                time.sleep(SLEEP_AFTER_PROFILE)

        major = self._detect_chrome_major()
        self.last_start_env["chrome_major"] = major

        try:
            opts = self._build_options()

            if major:
                driver_path = self._get_driver_path_for_major(major)
                self.driver = uc.Chrome(
                    options=opts,
                    driver_executable_path=driver_path,
                    use_subprocess=True,
                )
            else:
                self.driver = uc.Chrome(
                    options=opts,
                    use_subprocess=True,
                )

            try:
                self.driver.set_page_load_timeout(timeout)
            except Exception:
                pass

            return self.driver

        except SessionNotCreatedException as e:
            self.last_error = e
            self._safe_quit_driver()
            self._wipe_uc_driver_cache()
            raise e

        except Exception as e:
            self.last_error = e
            self._safe_quit_driver()
            raise e

    def _safe_quit_driver(self) -> None:
        d = self.driver
        self.driver = None
        if not d:
            return
        try:
            d.quit()
        except Exception:
            pass

    def quit(self) -> None:
        """
        종료 시:
        - 드라이버 종료
        - 임시 프로필이면 삭제
        - 고정 프로필(fixed_profile_dir)은 삭제하지 않는다(로그인 유지 목적)
        """
        self._safe_quit_driver()

        try:
            fixed_profile_dir = os.path.join(
                os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
                "MyCrawlerProfile",
                "selenium_profile",
                )
            if self._profile_dir and os.path.isdir(self._profile_dir) and self._profile_dir != fixed_profile_dir:
                shutil.rmtree(self._profile_dir, ignore_errors=True)
        except Exception:
            pass
        finally:
            self._profile_dir = None
            self._net_enabled = False
            self._perf_supported = None

    # =========================================================
    # helpers
    # =========================================================
    def wait_element(self, by: Any, selector: str, timeout: int = 10) -> Any:
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except Exception as e:
            self.last_error = e
            return None

    @staticmethod
    def explain_exception(context: str, e: Exception) -> str:
        if isinstance(e, NoSuchElementException):
            return f"❌ {context}: 요소 없음"
        if isinstance(e, StaleElementReferenceException):
            return f"❌ {context}: Stale 요소"
        if isinstance(e, TimeoutException):
            return f"⏱️ {context}: 시간 초과"
        if isinstance(e, ElementClickInterceptedException):
            return f"🚫 {context}: 클릭 방해"
        if isinstance(e, ElementNotInteractableException):
            return f"🚫 {context}: 비활성 요소"
        if isinstance(e, InvalidSelectorException):
            return f"🚫 {context}: 선택자 오류"
        if isinstance(e, WebDriverException):
            return f"⚠️ {context}: WebDriver 오류"
        return f"❗ {context}: 알 수 없는 오류"
