# chrome_macro.py (revised & hardened)
import os
import shutil
import tempfile
import subprocess
import time
from typing import Optional

import psutil
import pyautogui
import pygetwindow as gw
import pyperclip

# (선택) Windows 네이티브 클립보드 접근: 있으면 더 안정적, 없으면 pyperclip로 폴백
import win32clipboard
import win32con
import threading  # ✅ 누락 보강


class ChromeOpenError(Exception):
    """크롬 실행/제어 중 발생하는 사용자 정의 예외."""


class ChromeMacro:
    """
    매크로(키보드/윈도우 포커싱)로 크롬을 제어하는 경량 도우미.

    특징
    ─────────────────────────────────────────────────────────────────────────────
    - Selenium / Playwright / Puppeteer 미사용 (설치·드라이버 의존성 없음)
    - 전용 user-data-dir(임시 프로필)을 사용하여 항상 동일한 프로필/창에 탭을 붙임
    - 단축키 기반: 새 탭 열기, URL 이동, view-source 통해 소스 복사 등 수행
    - 클립보드 붙여넣기 방식으로 한글/특수문자 입력 안정성 확보

    제약/주의
    ─────────────────────────────────────────────────────────────────────────────
    - OS: Windows(프로세스명 chrome.exe, taskkill 사용), pygetwindow/pyautogui 전제
    - 포커스 기반 자동화 특성상: 포커스가 다른 앱으로 이동하면 오동작 가능
    - 보안 솔루션/정책에 따라 키보드/클립보드 후킹이 차단될 수 있음
    - 듀얼 모니터/가상데스크톱 환경에서 활성창 탐지가 지연될 수 있음
    """

    def __init__(
            self,
            window_title_keyword: str = "Chrome",
            default_settle: float = 1.0,
            failsafe: bool = True,
            chrome_path: Optional[str] = None,
            isolate_profile: bool = True,
            auto_close_all_on_init: bool = False,
            suppress_signin_ui: bool = True,
    ) -> None:
        """
        매크로 도우미 초기화.

        Parameters
        ----------
        window_title_keyword : str
            전경으로 올릴 크롬 창 제목에 포함될 키워드. 기본 "Chrome"
        default_settle : float
            크롬 스폰/탭 전환 직후 안정화 대기(초)
        failsafe : bool
            PyAutoGUI failsafe(마우스 좌상단 이동 시 예외) 활성 여부
        chrome_path : Optional[str]
            크롬 실행 파일 경로. None이면 _which_chrome()로 자동 탐색
        isolate_profile : bool
            True면 임시 user-data-dir(프로필 디렉터리) 사용
        auto_close_all_on_init : bool
            초기화 시 모든 chrome.exe 강제 종료 여부(주의!)
        suppress_signin_ui : bool
            (예약) 로그인/동기화 UI 억제 의도 플래그
        """
        self.window_title_keyword = window_title_keyword
        self.default_settle = float(default_settle)
        self._keeper_created = False  # ✅ 브라우저 종료 방지용 keeper 탭 생성 여부

        # ✅ 포커스 watcher
        self._focus_thread = None
        self._focus_running = False

        # PyAutoGUI failsafe 설정 저장/적용
        self._prev_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = bool(failsafe)

        # 크롬 경로 확정
        self.chrome_path = chrome_path or self._which_chrome()
        if not self.chrome_path:
            raise ChromeOpenError("크롬 실행 파일을 찾을 수 없습니다. (Chrome 미설치 또는 PATH 미등록)")

        # 전용 프로필 디렉터리 준비
        self.profile_dir = None
        if isolate_profile:
            self.profile_dir = os.path.join(tempfile.gettempdir(), f"chrome-macro-{os.getpid()}")
            os.makedirs(self.profile_dir, exist_ok=True)

        self.suppress_signin_ui = bool(suppress_signin_ui)

        # 옵션: 초기화 시 전 크롬 종료
        if auto_close_all_on_init:
            self.close_all()
            time.sleep(0.4)

    # ─────────────────────────────────────────
    # Keeper 탭: 브라우저 전체 종료 방지용
    # ─────────────────────────────────────────
    def ensure_keeper_tab(self) -> None:
        """
        최초 1회만 about:blank keeper 탭을 만들어두어,
        이후 Ctrl+W로 활성 탭을 닫더라도 브라우저 프로세스가 바로 종료되지 않게 함.
        """
        if not self._keeper_created:
            self._activate_chrome_or_raise()
            self._hotkey("ctrl", "t", pause=0.08)  # 새 탭
            self._hotkey("ctrl", "l", pause=0.05)  # 주소창 포커스
            self._paste_text("about:blank")
            pyautogui.press("enter")
            time.sleep(0.3)
            self._keeper_created = True

    # ─────────────────────────────────────────
    # 내부 유틸리티
    # ─────────────────────────────────────────
    @staticmethod
    def _which_chrome() -> Optional[str]:
        """크롬 실행 파일 경로를 탐색한다."""
        cand = shutil.which("chrome")
        if cand:
            return cand
        candidates = [
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
        return None

    @staticmethod
    def _is_chrome_running() -> bool:
        """chrome.exe 프로세스 존재 여부 확인."""
        for p in psutil.process_iter(["name"]):
            if (p.info.get("name") or "").lower() == "chrome.exe":
                return True
        return False

    def _activate_chrome_or_raise(self, timeout: float = 5.0) -> None:
        """
        크롬 창을 전경(Active Window)으로 올린다. 실패 시 예외.
        - 제목에 window_title_keyword 포함 창만 대상으로
        - 최소화된 창은 restore 후 activate
        - 여러 개면 뒤에서 앞으로 순회
        """
        end = time.time() + timeout
        while time.time() < end:
            try:
                wins = [w for w in gw.getAllWindows() if w.title and self.window_title_keyword in w.title]
                if wins:
                    for w in reversed(wins):
                        try:
                            if w.isMinimized:
                                try:
                                    w.restore()
                                    time.sleep(0.1)
                                except Exception:
                                    pass
                            w.activate()
                            time.sleep(0.15)
                            active = gw.getActiveWindow()
                            if active and active._hWnd == w._hWnd:
                                return
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(0.15)
        raise ChromeOpenError("크롬 창을 전경으로 가져오지 못했습니다.")

    def _hotkey(self, *keys: str, pause: float = 0.06, retries: int = 1) -> None:
        """
        pyautogui.hotkey()를 약간의 재시도로 안정 전송.
        - 포커스/입력잠금 등으로 인한 간헐 실패에 대비
        """
        for _ in range(retries + 1):
            try:
                pyautogui.hotkey(*keys)
                time.sleep(pause)
                return
            except Exception:
                time.sleep(0.08)

    def _paste_text(self, text: str, pause: float = 0.04) -> None:
        """
        주소창 등 안전 입력을 위해 타이핑 대신 '클립보드 붙여넣기' 사용.
        - 기존 클립보드 내용 백업 → 복구
        """
        backup = pyperclip.paste()
        try:
            pyperclip.copy(text)
            time.sleep(pause)
            self._hotkey("ctrl", "v", pause=0.04)
        finally:
            time.sleep(0.02)
            pyperclip.copy(backup)


    def _read_clipboard_stable(self, timeout: float = 5.0, min_len: int = 1) -> str:
        end = time.time() + max(0.5, timeout)
        last = ""
        while time.time() < end:
            try:
                if win32clipboard and win32con:
                    win32clipboard.OpenClipboard()
                    try:
                        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        else:
                            data = ""
                    finally:
                        win32clipboard.CloseClipboard()
                else:
                    data = pyperclip.paste()
                if data and len(data) >= min_len:
                    return data
                last = data or last
            except Exception:
                pass
            time.sleep(0.05)
        return last or ""



    def _dump_dom_via_headless(self, url: str, timeout: float = 25.0) -> str:
        """
        최후수단: UI/클립보드에 의존하지 않고 Headless Chrome으로 DOM 덤프.
        """
        args = [
            self.chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--virtual-time-budget=7000",  # SPA 초기 렌더 유도(ms)
            "--dump-dom",
            url,
        ]
        try:
            cp = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            out = (cp.stdout or b"").decode("utf-8", errors="ignore")
            if not out:
                out = (cp.stderr or b"").decode("utf-8", errors="ignore")
            return out.strip()
        except Exception:
            return ""

    def _spawn_chrome_url(self, url: str) -> None:
        """
        크롬 프로세스를 URL과 함께 스폰(동일 user-data-dir로 탭 유도).
        """
        try:
            args = [
                self.chrome_path,
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-sync",
                "--disable-features=EnableSyncConsent",
            ]
            if self.profile_dir:
                args.append(f"--user-data-dir={self.profile_dir}")
            args.append(url)

            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # 콘솔 창 숨김(Windows)
            )
        except Exception as e:
            raise ChromeOpenError(f"크롬 실행 실패: {e}")

    # ─────────────────────────────────────────
    # 공개 인터페이스
    # ─────────────────────────────────────────
    @property
    def is_running(self) -> bool:
        """chrome.exe 프로세스가 하나라도 실행 중이면 True."""
        return self._is_chrome_running()

    def open_url(self, url: str, *, replace_previous: bool = False, settle: Optional[float] = None) -> None:
        """
        크롬에 URL을 연다(같은 프로필로 새 탭 유도).
        - replace_previous=True: 직전 탭 닫음(포커스 꼬임 우려 → 기본 False 권장)
        """
        if not url or not isinstance(url, str):
            raise ChromeOpenError("유효한 URL 문자열이 필요합니다.")

        was_running = self.is_running
        self._spawn_chrome_url(url)
        time.sleep(self.default_settle if settle is None else float(settle))
        self._activate_chrome_or_raise()

        if replace_previous and was_running:
            self._hotkey("ctrl", "shift", "tab", pause=0.05)
            self._hotkey("ctrl", "w", pause=0.05)

    def close_active_tab(self, pause: float = 0.08) -> None:
        """
        현재 활성 탭을 닫는다.
        - 최초 1회 ensure_keeper_tab() 실행 시 브라우저 전체 종료 방지
        """
        self._activate_chrome_or_raise()
        self.ensure_keeper_tab()
        self._hotkey("ctrl", "w", pause=pause)

    def copy_current_url(self) -> str:
        """
        활성 탭의 현재 URL을 주소창에서 복사하여 반환.
        """
        self._activate_chrome_or_raise()
        self._hotkey("ctrl", "l", pause=0.05)
        self._hotkey("ctrl", "c", pause=0.05)
        time.sleep(0.04)
        return (pyperclip.paste() or "").strip()


    def copy_page_html_via_view_source(
            self,
            settle_after_open: float = 1.0,
            copy_retries: int = 6,
            copy_wait_each: float = 3.0,
    ) -> str:
        """
        활성 탭의 '원본 HTML 소스'를 view-source로 열어 복사(강화판).
        우선 클립보드 방식 → 실패 시 파일 저장 백업 → 최후수단 headless --dump-dom
        """
        self._activate_chrome_or_raise()

        # 1) 현재 URL 확보
        self._hotkey("ctrl", "l", pause=0.05)
        self._hotkey("ctrl", "c", pause=0.05)
        time.sleep(0.04)
        cur_url = (pyperclip.paste() or "").strip()
        if not cur_url:
            raise ChromeOpenError("현재 탭 URL을 읽지 못했습니다. (주소창 복사 실패)")

        # 2) 새 탭 → view-source 이동
        self._hotkey("ctrl", "t", pause=0.08)
        self._hotkey("ctrl", "l", pause=0.04)
        vs_url = f"view-source:{cur_url}" if not cur_url.startswith("view-source:") else cur_url
        self._paste_text(vs_url)
        pyautogui.press("enter")
        time.sleep(float(settle_after_open))

        # 2.5) 페이지 영역 포커스 보정
        self._focus_into_page_area()
        time.sleep(0.05)

        # 3) 클립보드 방식 복사(로딩/포커스/훅킹 대비 재시도)
        clip_backup = pyperclip.paste()
        html = ""
        try:
            for _ in range(copy_retries):
                self._activate_chrome_or_raise()
                self._focus_into_page_area()
                pyperclip.copy("")  # 초기화

                self._hotkey("ctrl", "a", pause=0.08, retries=1)
                self._hotkey("ctrl", "c", pause=0.12, retries=1)

                copied = self._read_clipboard_stable(timeout=copy_wait_each, min_len=1).strip()

                # 주소창을 잡은 경우(= URL만 복사됐거나 'view-source:'만 존재) 필터링
                if not copied or copied == cur_url or copied.startswith("view-source:"):
                    time.sleep(0.2)
                    continue

                # 너무 짧으면 아직 로딩 전일 수 있음(문자 수 기준 완화 가능)
                if len(copied) < 40 and "<!doctype" not in copied.lower() and "<html" not in copied.lower():
                    time.sleep(0.2)
                    continue

                html = copied
                break
        finally:
            # 복구(실패해도 무시)
            try:
                pyperclip.copy(clip_backup)
            except Exception:
                pass

        # 4) 임시 view-source 탭 닫고 복귀
        self._hotkey("ctrl", "w", pause=0.08)

        # 5) 클립보드 실패 → 파일 저장 백업 플랜
        if not html:
            html = self._save_view_source_to_temp(timeout=6.0)

        # 6) 최후수단: Headless 덤프
        if not html:
            html = self._dump_dom_via_headless(cur_url, timeout=30.0)
            if not html:
                raise ChromeOpenError("페이지 소스 복사에 실패했습니다. (클립보드/저장/헤드리스 모두 실패)")
        return html


    def open_and_grab_html(
            self,
            url: str,
            *,
            settle: Optional[float] = None,
            close_tab_after: bool = True,
            view_source_settle: float = 1.0,
            copy_retries: int = 5,
            copy_wait_each: float = 2.5,
    ) -> str:
        """
        URL을 새 탭으로 열고(view-source 경유) HTML을 수집한 뒤,
        필요 시 활성 탭을 닫아 '한 탭 유지' 정책을 돕는다.
        """
        self.open_url(url, replace_previous=False, settle=settle)
        html = self.copy_page_html_via_view_source(
            settle_after_open=view_source_settle,
            copy_retries=copy_retries,
            copy_wait_each=copy_wait_each,
        )
        if close_tab_after:
            self.close_active_tab()
        return html

    def close_all(self) -> None:
        """
        모든 chrome.exe 프로세스를 강제 종료한다. (다른 앱의 크롬 세션에도 영향 가능!)
        """
        if not self.is_running:
            return
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "chrome.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            time.sleep(0.3)
        except Exception as e:
            raise ChromeOpenError(f"크롬 종료 실패: {e}")

    # ─────────────────────────────────────────
    # 포커스 watcher 추가
    # ─────────────────────────────────────────
    def _focus_loop(self, interval: float = 1.0):
        while self._focus_running:
            try:
                active = gw.getActiveWindow()
                active_title = getattr(active, "title", "") or ""
                if not active or self.window_title_keyword not in active_title:
                    self._activate_chrome_or_raise(timeout=1.5)
            except Exception:
                pass
            time.sleep(interval)

    def start_focus_watcher(self, interval: float = 1.0):
        """포커스 복원 watcher 시작"""
        if self._focus_thread and self._focus_thread.is_alive():
            return
        self._focus_running = True
        self._focus_thread = threading.Thread(target=self._focus_loop, args=(interval,), daemon=True)
        self._focus_thread.start()

    def stop_focus_watcher(self):
        """포커스 복원 watcher 중지"""
        self._focus_running = False
        if self._focus_thread:
            self._focus_thread.join(timeout=2.0)
            self._focus_thread = None

    def _focus_into_page_area(self):
        """
        주소창 → 페이지 영역으로 포커스를 확실히 옮긴다.
        - F6은 크롬에서 주소창/툴바/북마크바/페이지 영역 사이를 순환
        """
        try:
            # 주소창에 있을 확률이 높으니 두세 번 돌려 페이지로 내린다
            for _ in range(3):
                pyautogui.press("f6")
                time.sleep(0.08)
        except Exception:
            pass


    def _save_view_source_to_temp(self, timeout: float = 6.0) -> str:
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"view_source_{int(time.time()*1000)}.txt")

        self._hotkey("ctrl", "s", pause=0.15, retries=1)
        time.sleep(0.25)

        # 파일명 입력란으로 확실히 포커스 이동
        try:
            pyautogui.hotkey("alt", "n")
            time.sleep(0.06)
        except Exception:
            pass

        self._paste_text(tmp_path)
        time.sleep(0.05)
        pyautogui.press("enter")
        time.sleep(0.2)
        pyautogui.press("enter")

        end = time.time() + max(1.5, timeout)
        while time.time() < end:
            if os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 0:
                try:
                    with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read()
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            time.sleep(0.1)

        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return ""

    # 컨텍스트 매니저 지원: with ChromeMacro() as cm: ...
    def __enter__(self):
        """with 문 진입 시 자기 자신을 반환."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """
        with 문 종료 시 PyAutoGUI FAILSAFE 원복.
        예외는 여기서 삼키지 않고(=False) 호출자에게 전파.
        """
        pyautogui.FAILSAFE = self._prev_failsafe
        self.stop_focus_watcher()   # ✅ watcher 정리 추가
        return False
