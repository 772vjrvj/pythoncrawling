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
from typing import Optional, Tuple, Dict, Any, List

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
    def __init__(
            self,
            headless: bool = False,
            debug: Optional[bool] = None
    ):
        """
        headless : True면 브라우저 UI 없이 실행
        debug    : True면 내부 로그 출력

        [빌드/배포 주의]
        - PyInstaller onefile/onedir 모두에서 동작 가능하도록
          chrome.exe 위치 탐색/driver mismatch 대응을 내부에서 처리한다.
        """
        self.headless = headless
        self.driver = None
        self.last_error: Optional[Exception] = None

        # debug 인자 없으면 환경변수로도 켤 수 있게
        if debug is None:
            debug = os.environ.get("SELENIUMUTILS_DEBUG", "").strip().lower() in ("1", "true", "y", "yes")
        self.debug = bool(debug)

        # 실행 시 사용할 프로필 폴더(고정 or 임시)
        self._profile_dir: Optional[str] = None

        # - capture_enabled=True 로 띄우면 perf log + CDP 캡처 루틴 사용 가능
        # - block_images=True 로 띄우면 이미지 로딩 차단(성능/트래픽 감소) -> 페이지에 따라 깨질 수 있으니 토글
        self.capture_enabled = False
        self.block_images = False
        self._net_enabled = False
        self._perf_supported = None  # type: Optional[bool]

        # start_driver 당시 환경 기록(고객PC 디버깅용)
        self.last_start_env: Dict[str, Any] = {}

    # =========================================================
    # log
    # =========================================================
    def _log(self, *args):
        if self.debug:
            print("[SeleniumUtils]", *args)

    # =========================================================
    # 토글 API
    # =========================================================
    def set_capture_options(self, enabled: bool, block_images: Optional[bool] = None):
        """
        enabled=True  : CDP 캡처 사용(= performance log를 읽고 Network.getResponseBody를 쓰는 기능 사용)
        block_images  : 이미지 차단(옵션이므로 driver 시작 전에 적용 권장)

        [중요]
        - block_images는 크롬 옵션(prefs)이기 때문에 driver 생성 이후에는 바꿔도 적용 안된다.
        - capture_enabled는 driver 생성 후 enable_capture_now()로 켤 수 있다.
        """
        self.capture_enabled = bool(enabled)
        if block_images is not None:
            self.block_images = bool(block_images)

    def enable_capture_now(self) -> bool:
        """
        driver 실행 후 CDP 캡처 활성화(Network.enable + perf log 지원 체크)
        - 옵션(performance log capability)은 driver 생성 시점에 켜져 있어야 가장 안정적이다.
        - 하지만 일부 환경에서 "일단 띄우고" 나중에 켜는 방식을 원하면 사용.
        """
        self.capture_enabled = True
        return bool(self.enable_network_capture())

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

    def _wipe_locks(self, path: str):
        """
        고정 프로필 사용 시 남아있는 lock 파일 제거
        - DevToolsActivePort 남아있으면 크롬이 즉시 종료되거나 연결 실패하는 케이스가 있다.
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
        - 정확한 lock 잡기까지는 안 하고, SingletonLock 존재로 빠르게 판단
        - 더 강한 판정이 필요하면 msvcrt locking 방식으로 확장 가능
        """
        lock_path = os.path.join(profile_dir, "SingletonLock")
        return os.path.exists(lock_path)

    def _wait_profile_unlock(self, profile_dir: str, timeout_sec: float = 6.0, poll: float = 0.2) -> bool:
        """
        === 신규 ===
        restart 직후 SingletonLock이 잠깐 남는 타이밍 이슈가 많아서
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
        """
        chrome.exe 경로 찾기 (배포/고객PC에서 매우 중요)

        [빌드/배포 주의]
        - 고객PC에서 크롬 설치 위치가 다를 수 있어 uc.find_chrome_executable() + 레지스트리 + 기본 경로 순으로 탐색
        """
        try:
            p = uc.find_chrome_executable()
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass

        pf = os.environ.get("ProgramFiles")
        pf86 = os.environ.get("ProgramFiles(x86)")
        local = os.environ.get("LOCALAPPDATA")

        candidates = []
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
        """
        uc patcher로 해당 major용 chromedriver 내려받고 경로를 받는다.
        - 배포 환경에서 크롬 업데이트로 driver mismatch 나는 걸 줄여준다.
        """
        patcher = Patcher(version_main=major)
        patcher.auto()
        return patcher.executable_path

    def _wipe_uc_driver_cache(self):
        """
        undetected_chromedriver 캐시 드라이버 제거:
        - 배포 시 어떤 PC에서 오래된 드라이버가 남아 mismatch를 유발하는 케이스가 있다.
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
    def _build_options(self):
        """
        크롬 옵션 구성

        [빌드/배포 주의]
        - capture_enabled=True일 때만 performance log를 켠다.
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
            # headless는 사이트마다 탐지/차단이 있을 수 있어 필요할 때만
            opts.add_argument("--headless=new")

        # === 신규 === 이미지 차단 토글
        if self.block_images:
            try:
                opts.add_experimental_option("prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.default_content_setting_values.notifications": 2,
                })
            except Exception:
                pass

        # === 신규 === perf log 토글 (캡처할 때만)
        if self.capture_enabled:
            try:
                opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            except Exception:
                pass

        if self._profile_dir:
            opts.add_argument(f"--user-data-dir={self._profile_dir}")

        return opts

    # =========================================================
    # CDP / performance logs (공통)
    # =========================================================
    def enable_network_capture(self) -> bool:
        """
        CDP Network.enable + performance log 지원 체크

        [빌드/배포 주의]
        - 어떤 환경(특히 보안제품/정책)에서는 performance log 접근이 막힐 수 있다.
        - 그 경우 _perf_supported=False로 내려가며 wait_api_*는 None을 반환하게 된다.
        """
        if not self.driver:
            return False

        try:
            self.driver.execute_cdp_cmd("Network.enable", {})
            self._net_enabled = True
        except Exception as e:
            self._net_enabled = False
            self._log("Network.enable failed:", str(e))

        try:
            _ = self.driver.get_log("performance")
            self._perf_supported = True
        except Exception as e:
            self._perf_supported = False
            self._log("performance log not supported:", str(e))

        return bool(self._net_enabled and self._perf_supported)

    # =========================================================
    # === 신규 === request 캡처 전용
    # =========================================================
    def wait_api_request(
            self,
            url_contains: str,
            query_contains: Optional[str] = None,
            timeout_sec: float = 15.0,
            poll: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        """
        request 정보만 반환 (response body 없음)
        """
        if not self.driver:
            return None

        if not self.capture_enabled:
            return None

        if not self._net_enabled or self._perf_supported is False:
            self.enable_network_capture()

        key_req = "Network.requestWillBeSent"

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            try:
                logs = self.driver.get_log("performance")
            except Exception:
                logs = []

            for row in logs or []:
                msg = row.get("message") if isinstance(row, dict) else None
                if not msg:
                    continue

                if key_req not in msg:
                    continue
                if url_contains not in msg:
                    continue
                if query_contains and query_contains not in msg:
                    continue

                try:
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
                except Exception:
                    continue

            time.sleep(poll)

        return None

    def drain_performance_logs(self):
        """
        performance 로그 비우기:
        - 페이지 이동 직전에 호출하면 "과거 이벤트 오염"을 줄일 수 있다.
        """
        if not self.driver:
            return
        try:
            _ = self.driver.get_log("performance")
        except Exception:
            pass

    def _get_response_body(self, request_id: str) -> Optional[str]:
        """
        CDP Network.getResponseBody로 body를 얻는다.
        - base64Encoded 인 경우 디코딩 처리
        """
        if not self.driver or not request_id:
            return None
        try:
            res = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            if not isinstance(res, dict):
                return None
            body = res.get("body")
            if body is None:
                return None
            if res.get("base64Encoded"):
                try:
                    return base64.b64decode(body).decode("utf-8", "replace")
                except Exception:
                    return str(body)
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
        ✅ 공통 네트워크 캡처 (도메인 지식 없음)
        """
        if not self.driver:
            return None

        if not self.capture_enabled:
            self._log("capture_enabled is False -> wait_api_body skip")
            return None

        if not self._net_enabled or self._perf_supported is False:
            self.enable_network_capture()

        key_resp = "Network.responseReceived"
        key_fin = "Network.loadingFinished"
        key_fail = "Network.loadingFailed"

        candidates: Dict[str, Dict[str, Any]] = {}
        finished = set()
        failed = set()

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            try:
                logs = self.driver.get_log("performance")
            except Exception:
                logs = []

            for row in logs or []:
                msg = row.get("message") if isinstance(row, dict) else None
                if not msg:
                    continue

                if (key_resp not in msg) and (key_fin not in msg) and (key_fail not in msg):
                    continue

                if key_resp in msg and (url_contains in msg) and (query_contains is None or query_contains in msg):
                    try:
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
                    except Exception:
                        continue
                    continue

                if (key_fin in msg) or (key_fail in msg):
                    try:
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
                    except Exception:
                        continue

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
        """
        wait_api_body() 결과 bodyText를 JSON으로 파싱해서 반환
        - JSON이 아니면 None
        """
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
    def start_driver(self, timeout: int = 30, force_profile_dir: Optional[str] = None, allow_profile_fallback: bool = True):
        """
        Windows 기준 안정화:
        - 고정 프로필 기본 사용(로그인 유지)
        - 프로필이 사용 중이면 임시 프로필로 fallback
        - Chrome major 감지 후 해당 major로 uc patcher 적용

        === 신규 ===
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

        # === 신규 === force_profile_dir면 fallback 금지 케이스가 많음
        if force_profile_dir:
            self._profile_dir = force_profile_dir
            # 재기동 직후 lock 잔재 제거 + 대기
            self._wipe_locks(self._profile_dir)
            self._wait_profile_unlock(self._profile_dir, timeout_sec=6.0, poll=0.2)
            time.sleep(SLEEP_AFTER_PROFILE)
        else:
            # 기존 로직 유지
            if self._is_profile_in_use(chosen_profile):
                if allow_profile_fallback:
                    self._profile_dir = self._new_tmp_profile()
                    self.last_start_env["profile_fallback"] = True
                    self._log("fixed profile in-use -> tmp profile:", self._profile_dir)
                else:
                    # === 신규 === fallback 금지면 대기만 한다
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
                    use_subprocess=True
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

    def restart_driver_keep_profile(self, timeout: int = 30, retry: int = 3, retry_sleep: float = 0.6):
        """
        같은 user-data-dir(프로필)을 유지한 채 드라이버만 재시작한다.
        - 로그인 세션 유지
        - performance log ON/OFF 같은 capability 변경을 적용할 때 필요

        === 신규(핵심 수정) ===
        - 재기동 시 tmp profile fallback을 절대 허용하지 않는다.
          (lock 잔재 때문에 fallback되면 세션이 날아가서 로그인 다시 탑니다)
        """
        old_profile = self._profile_dir

        self._safe_quit_driver()
        self.driver = None

        self._profile_dir = old_profile

        last_e = None
        for i in range(max(1, int(retry))):
            try:
                if self._profile_dir and os.path.isdir(self._profile_dir):
                    self._wipe_locks(self._profile_dir)

                time.sleep(float(retry_sleep))

                # === 신규 === old_profile 강제 + fallback 금지
                return self.start_driver(
                    timeout=timeout,
                    force_profile_dir=self._profile_dir,
                    allow_profile_fallback=False
                )

            except Exception as e:
                last_e = e
                try:
                    self._log("restart_driver_keep_profile failed:", str(e))
                except Exception:
                    pass
                time.sleep(float(retry_sleep))

        self.last_error = last_e
        raise last_e

    def _safe_quit_driver(self):
        d = self.driver
        self.driver = None
        if not d:
            return
        try:
            d.quit()
        except Exception:
            pass

    def quit(self):
        """
        종료 시:
        - 드라이버 종료
        - 임시 프로필이면 삭제

        [빌드/배포 주의]
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
