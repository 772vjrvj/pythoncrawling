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
import winreg
from typing import Optional, Tuple, Dict, Any

import undetected_chromedriver as uc
from undetected_chromedriver.patcher import Patcher

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


# 기본 윈도우 크기(참고용). 현재는 --start-maximized를 쓰지만,
# headless나 일부 환경에서 window-size가 필요할 수 있어 상수는 유지.
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 800

# 고정 프로필 사용 시(로그인 유지) 크롬 락 파일 지운 직후,
# 크롬이 내부적으로 파일 잠금 상태를 정리할 시간을 약간 주기 위함.
SLEEP_AFTER_PROFILE = 0.3


class SeleniumUtils:
    def __init__(self, headless: bool = False, debug: Optional[bool] = None):
        """
        headless : True면 브라우저 UI 없이 실행
        debug    : True면 내부 로그 출력
        """
        self.headless = headless
        self.driver = None

        # 실행할 때 선택된 프로필 경로(고정 프로필 or 임시 프로필)
        self._tmp_profile: Optional[str] = None

        # 마지막 예외 저장(외부에서 원인 확인용)
        self.last_error: Optional[Exception] = None

        # 디버그 플래그: 인자 없으면 환경변수로 제어 가능
        if debug is None:
            debug = os.environ.get("SELENIUMUTILS_DEBUG", "").strip().lower() in ("1", "true", "y", "yes")
        self.debug = bool(debug)

        # start_driver 실행 당시 환경 정보를 기록(고객 PC 디버깅에 매우 도움)
        self.last_start_env: Dict[str, Any] = {}

    # =========================================================
    # log
    # =========================================================
    def _log(self, *args):
        """debug=True일 때만 print 출력"""
        if self.debug:
            print("[SeleniumUtils]", *args)

    # =========================================================
    # profile
    # =========================================================
    def _new_tmp_profile(self) -> str:
        """
        임시 프로필 폴더 생성
        - 고정 프로필이 이미 사용 중(다른 크롬/다른 자동화 실행 등)일 때 fallback 용
        - tempfile 아래에 만든다 (종료 시 삭제 가능)
        """
        base = os.path.join(tempfile.gettempdir(), "selenium_profiles")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"profile_{uuid.uuid4().hex}")
        os.makedirs(path, exist_ok=True)
        return path

    def _wipe_locks(self, path: str):
        """
        크롬 프로필 락 관련 파일/디렉토리 제거
        - 크롬이 비정상 종료되면 SingletonLock, DevToolsActivePort 등이 남아서
          다음 실행 시 "Chrome failed to start" 류 에러가 나기 쉽다.
        - ⚠️ 실제로 크롬이 프로필을 사용 중일 때 지우면 프로필 손상 위험이 있으니
          start_driver()에서 in-use 체크 후 "고정 프로필"일 때만 수행하는 구조로 사용.
        """
        for pat in ["Singleton*", "LOCK", "LockFile", "DevToolsActivePort", "lockfile"]:
            for p in glob.glob(os.path.join(path, pat)):
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception:
                    # 락 파일이 이미 사라졌거나 권한 문제가 있어도 치명적이지 않으니 무시
                    pass

    def _is_profile_in_use(self, profile_dir: str) -> bool:
        """
        Windows에서 크롬 프로필이 "사용 중"인지 대략 판단
        - SingletonLock 파일이 있으면 in-use 가능성이 높다.
        - msvcrt로 non-blocking lock을 잡아보고 실패하면 사용 중으로 판단.
        - 확실치 않으면 안전하게 True(사용 중)로 간주하여 임시 프로필로 회피.
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
                # lock 실패 -> 다른 프로세스가 사용 중
                return True
            finally:
                try:
                    f.close()
                except Exception:
                    pass
        except Exception:
            # 확실치 않으면 "사용 중"으로 잡아 안전하게 처리
            return True

    # =========================================================
    # chrome exe / version
    # =========================================================
    def _find_chrome_exe_windows(self) -> Optional[str]:
        """
        Windows에서 chrome.exe 경로를 최대한 찾는다.
        - uc.find_chrome_executable() 우선 사용
        - Program Files / LocalAppData 후보 경로 확인
        - App Paths 레지스트리 키도 확인
        """
        # 1) uc 내장 탐색 시도
        try:
            p = uc.find_chrome_executable()
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass

        # 2) 기본 설치 경로 후보들
        pf = os.environ.get("ProgramFiles")
        pf86 = os.environ.get("ProgramFiles(x86)")
        local = os.environ.get("LOCALAPPDATA")

        path_candidates = []
        if pf:
            path_candidates.append(os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"))
        if pf86:
            path_candidates.append(os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"))
        if local:
            path_candidates.append(os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"))

        # 3) App Paths 레지스트리(실제 설치 위치를 직접 가리키는 경우가 많음)
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

        return None

    def _get_chrome_version_text(self) -> Optional[str]:
        """
        chrome.exe --version 결과를 가져온다.
        예: "Google Chrome 121.0.6167.85"
        """
        chrome_exe = self._find_chrome_exe_windows()
        if not chrome_exe:
            return None

        try:
            out = subprocess.check_output(
                [chrome_exe, "--version"],       # chrome.exe 자체를 호출해야 확실함
                stderr=subprocess.STDOUT,
                text=True,
                shell=False
            )
            return (out or "").strip()
        except Exception:
            return None

    def _detect_chrome_major(self) -> Optional[int]:
        """
        Chrome 버전 문자열에서 major 버전만 추출
        예: "Google Chrome 121.0.6167.85" -> 121
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
        """
        SessionNotCreatedException 메시지에서 브라우저 major를 파싱(가능하면)
        예: "Current browser version is 121.0.6167.85 ..."
        """
        msg = str(e)

        m = re.search(r"Current browser version is (\d+)", msg)
        if m:
            return int(m.group(1))

        m = re.search(r"browser version (\d+)", msg, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None

        return None

    def _wipe_uc_driver_cache(self):
        """
        undetected_chromedriver가 내려받아 패치해둔 chromedriver 캐시를 정리
        - chrome 업데이트/드라이버 꼬임/권한 문제 등으로 uc 캐시가 깨졌을 때 도움이 됨
        - 폴더 통째 삭제가 아니라 chromedriver*만 지워서 영향 최소화
        """
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
        """
        현재 Chrome major에 맞는 chromedriver를 undetected_chromedriver Patcher로 확보
        - patcher.auto()가 다운로드/패치까지 해줌
        """
        patcher = Patcher(version_main=major)
        patcher.auto()
        return patcher.executable_path

    # =========================================================
    # options
    # =========================================================
    def _build_options(self):
        """
        크롬 실행 옵션(가장 중요한 안정화 포인트)
        - 여기는 "하나하나" 왜 넣는지 주석을 자세히 달아둠
        """
        opts = uc.ChromeOptions()

        # --- (1) 자동화 탐지 완화 계열 ------------------------------------
        # AutomationControlled 플래그를 끄면 일부 사이트에서 자동화 탐지 시그널이 줄어듦
        # (완전 회피는 아니지만 uc + 이 옵션 조합이 기본 세팅으로 많이 쓰임)
        opts.add_argument("--disable-blink-features=AutomationControlled")

        # 브라우저 언어/지역 설정
        # - 네이버/국내 사이트에서 언어가 꼬여서 다른 UI가 뜨는 것 방지
        opts.add_argument("--lang=ko-KR")

        # 브라우저를 최대화로 시작
        # - 일부 사이트는 viewport 크기에 따라 요소가 달라져서 자동화가 꼬일 수 있음
        # - headless가 아니라면 사람처럼 보이기도 하고 안정성이 좋아짐
        opts.add_argument("--start-maximized")

        # --- (2) 안정성/호환성 계열 --------------------------------------
        # /dev/shm 공유메모리 사용 문제를 회피(리눅스/도커에서 주로 필요)
        # - Windows에선 큰 의미 없지만, 환경이 바뀌어도 안전하게 가져가는 옵션
        opts.add_argument("--disable-dev-shm-usage")

        # 최초 실행(first-run) 안내/팝업 방지
        # - 자동화 시작 시 "기본 브라우저 설정" 같은 화면 뜨면 작업 흐름이 깨짐
        opts.add_argument("--no-first-run")

        # "기본 브라우저로 설정" 안내 화면 방지
        opts.add_argument("--no-default-browser-check")

        # QUIC 프로토콜 비활성화
        # - 네트워크 이슈(특히 프록시/보안툴/특정 환경)에서 QUIC 때문에 접속/후킹이 꼬이는 경우가 있음
        # - 안정성 우선이면 끄는 게 편함
        opts.add_argument("--disable-quic")

        # --- (3) Chrome 111+ 계열 CORS/원본 관련 예외 회피 -----------------
        # 특정 조합(버전/드라이버/웹드라이버 설정)에서
        # "Only local connections are allowed" 류의 에러가 나는 경우가 있어
        # 디버깅/현장 배포 안정성 차원에서 넣어두면 도움이 되는 옵션.
        # (항상 필요하진 않지만, 넣어도 일반 사용에 부작용은 거의 없음)
        opts.add_argument("--remote-allow-origins=*")

        # --- (4) 프로필 지정 ----------------------------------------------
        # 고정 프로필을 쓰면:
        # - 로그인 세션 유지
        # - 캡차/쿠키 유지
        # - 사용자 환경(확장/로컬스토리지 등) 유지 가능
        # 단, 프로필이 사용 중이면 임시 프로필로 회피하는 구조와 함께 사용해야 안전함
        if self._tmp_profile:
            opts.add_argument(f"--user-data-dir={self._tmp_profile}")

        # --- (5) headless 모드 --------------------------------------------
        # 최신 headless 엔진 사용(Chrome의 new headless)
        # - 옛날 --headless 보다 호환성이 좋아짐
        if self.headless:
            opts.add_argument("--headless=new")

        return opts

    # =========================================================
    # window place / quit
    # =========================================================
    def _get_screen_size(self) -> Tuple[int, int]:
        """
        화면 해상도를 얻는다.
        - 왼쪽 반 화면 배치(_place_left_half)에서 사용
        - tkinter가 안되면 fallback 1920x1080
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
        return 1920, 1080

    def _place_left_half(self):
        """
        브라우저 창을 왼쪽 반 화면으로 배치(사용자 확인/로그인 작업 편의)
        headless면 창이 없으니 스킵
        """
        if not self.driver or self.headless:
            return
        sw, sh = self._get_screen_size()
        try:
            self.driver.set_window_rect(x=0, y=0, width=max(600, sw // 2), height=max(600, sh))
        except Exception:
            pass

    def _safe_quit_driver(self):
        """
        driver를 최대한 안전하게 종료
        - driver.quit() 실패하는 케이스(드라이버가 먹통/이미 죽음 등) 대비
        - service.process.kill()까지 시도해서 좀비 프로세스 방지
        """
        d = self.driver
        self.driver = None

        if not d:
            return

        try:
            d.quit()
            return
        except Exception:
            pass

        try:
            svc = getattr(d, "service", None)
            proc = getattr(svc, "process", None)
            if proc and getattr(proc, "poll", None) and proc.poll() is None:
                proc.kill()
        except Exception:
            pass

    def _create_uc_driver(self, opts, major: Optional[int]):
        """
        uc.Chrome 생성 공통 함수
        - major가 있으면 해당 버전에 맞춘 chromedriver를 patcher로 확보 후 지정
        - use_subprocess=False: uc 내부에서 subprocess로 분기하는 동작을 줄여
          프로세스 잔존/빈 창/종료 불안정 이슈를 완화하는데 도움되는 경우가 많음
        """
        if major:
            driver_path = self._get_driver_path_for_major(major)
            self._log("using driver major:", major, "| driver_path:", driver_path)
            return uc.Chrome(
                options=opts,
                driver_executable_path=driver_path,
                use_subprocess=False,
            )

        self._log("using driver major: None (uc auto)")
        return uc.Chrome(options=opts, use_subprocess=False)

    # =========================================================
    # public
    # =========================================================
    def start_driver(self, timeout: int = 30):
        """
        Windows 기준 안정화:
        - 고정 프로필 기본 사용(캡차/로그인 유지)
        - 프로필이 사용 중이면 임시 프로필로 fallback
        - Chrome major 감지 후 그 major로 uc patcher 적용
        - SessionNotCreatedException 시 캐시 wipe 후 재시도
        """

        # 고정 프로필(권장): 로그인/쿠키/캡차 유지 목적
        fixed_profile_dir = os.path.join(
            os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
            "MyCrawlerProfile",
            "selenium_profile"
        )
        os.makedirs(fixed_profile_dir, exist_ok=True)

        # start_driver 당시 환경 기록 (문제 발생 시 로그로 원인 추적 가능)
        self.last_start_env = {
            "headless": self.headless,
            "timeout": timeout,
            "fixed_profile_dir": fixed_profile_dir,
        }

        # 1) 프로필 선택: 고정 프로필을 기본으로 쓰되
        #    사용 중이면(다른 크롬이 락 잡음) 임시 프로필로 회피
        use_profile = fixed_profile_dir
        if self._is_profile_in_use(fixed_profile_dir):
            tmp = self._new_tmp_profile()
            self._log("fixed profile seems in-use -> fallback tmp profile:", tmp)
            use_profile = tmp
            self.last_start_env["profile_fallback"] = True
        else:
            self.last_start_env["profile_fallback"] = False

        self._tmp_profile = use_profile

        # 2) 락 제거: 고정 프로필일 때만(임시 프로필은 새로 만들어서 필요 거의 없음)
        #    + 사용 중인 프로필을 건드리지 않도록 위에서 in-use 체크를 했음
        if self._tmp_profile == fixed_profile_dir:
            self._wipe_locks(self._tmp_profile)
            time.sleep(SLEEP_AFTER_PROFILE)

        # 3) 크롬 major 감지: 현재 설치된 Chrome 버전에 맞춰 chromedriver를 고정시키기 위함
        major = self._detect_chrome_major()
        self.last_start_env["chrome_major"] = major
        self.last_start_env["chrome_version_text"] = self._get_chrome_version_text()

        # 4) 드라이버 생성
        try:
            opts = self._build_options()
            self.driver = self._create_uc_driver(opts, major)

            # 페이지 로딩 타임아웃 (네이버/대형 페이지에서 무한 대기 방지)
            try:
                self.driver.set_page_load_timeout(timeout)
            except Exception:
                pass

            # 창 배치(사용자 로그인/확인 편의)
            self._place_left_half()
            return self.driver

        # 4-1) 드라이버/브라우저 버전 미스매치로 흔히 나는 예외
        except SessionNotCreatedException as e:
            self._safe_quit_driver()

            # uc 캐시가 꼬인 경우가 많아 chromedriver 캐시를 정리
            self._wipe_uc_driver_cache()

            # 에러 메시지에서 브라우저 버전 major를 파싱해 재시도
            parsed = self._parse_major_from_error(e) or major
            self.last_start_env["session_not_created_parsed_major"] = parsed

            if parsed:
                opts = self._build_options()
                self.driver = self._create_uc_driver(opts, parsed)

                try:
                    self.driver.set_page_load_timeout(timeout)
                except Exception:
                    pass

                self._place_left_half()
                return self.driver

            # 파싱 실패하면 원 예외를 올려서 상위에서 로그로 확인
            self.last_error = e
            raise e

        # 4-2) 기타 예외: 드라이버 정리 후 예외 전달
        except Exception as e:
            self._safe_quit_driver()
            self.last_error = e
            raise e

    def quit(self):
        """
        외부에서 종료 호출 시
        - 드라이버 안전 종료
        - 임시 프로필이면 삭제(정리)
        - 고정 프로필은 유지(로그인/쿠키 유지 목적)
        """
        self._safe_quit_driver()

        try:
            fixed_profile_dir = os.path.join(
                os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
                "MyCrawlerProfile",
                "selenium_profile"
            )

            # 임시 프로필만 삭제
            if self._tmp_profile and os.path.isdir(self._tmp_profile) and (self._tmp_profile != fixed_profile_dir):
                shutil.rmtree(self._tmp_profile, ignore_errors=True)
        except Exception:
            pass
        finally:
            self._tmp_profile = None

    # =========================================================
    # helpers
    # =========================================================
    def wait_element(self, by, selector: str, timeout: int = 10):
        """
        element 존재 대기 헬퍼
        - presence_of_element_located: DOM에 존재만 하면 반환(보이는지/클릭 가능 여부는 아님)
        - 실패 시 None 반환하고 last_error에 예외 저장
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except Exception as e:
            self.last_error = e
            return None

    @staticmethod
    def explain_exception(context: str, e: Exception) -> str:
        """
        예외를 UI 로그용 한글 메시지로 변환
        """
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
