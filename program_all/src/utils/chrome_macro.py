# chrome_macro.py (revised & commented)
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


class ChromeOpenError(Exception):
    """크롬 실행/제어 중 발생하는 사용자 정의 예외."""


class ChromeMacro:
    """
    매크로(키보드/윈도우 포커싱)로 크롬을 제어하는 경량 도우미.

    특징
    ─────────────────────────────────────────────────────────────────────────────
    - Selenium / Playwright / Puppeteer 미사용 (설치·드라이버 의존성 없음)
    - 전용 user-data-dir(임시 프로필)을 사용하여 항상 동일한 프로필/창에 탭을 붙임
    - 키보드 단축키 기반으로 새 탭 열기, URL 이동, view-source 통해 소스 복사 등 수행
    - 클립보드 안전 붙여넣기(타이핑 대신)로 한글/특수문자 안정성 확보

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
            전경으로 올릴 크롬 창 제목에 포함될 키워드.
            기본 "Chrome" (한국어 Windows에서도 보통 "Chrome" 문자열이 포함됨)
        default_settle : float
            크롬 스폰/탭 전환 직후 안정화 대기 시간(초). open_url 등에서 기본 사용.
        failsafe : bool
            PyAutoGUI failsafe(마우스를 좌상단 구석으로 이동하면 예외로 중단) 활성화 여부.
            개발/디버깅 중엔 True 권장.
        chrome_path : Optional[str]
            크롬 실행 파일 경로. None이면 _which_chrome()로 자동 탐색.
        isolate_profile : bool
            True면 임시 user-data-dir(프로필 디렉토리)을 사용하여 깨끗한 환경 유지.
            크롬 동시 실행/세션 간섭 감소.
        auto_close_all_on_init : bool
            초기화 시 모든 chrome.exe를 강제 종료할지 여부. (다른 크롬 세션 영향!! 주의)
        suppress_signin_ui : bool
            (예약 필드) 동기화/로그인 UI 억제 의도. 현재 내부에서 직접 옵션 추가는 안함.

        Raises
        ------
        ChromeOpenError
            - 크롬 실행 파일을 찾지 못한 경우
        """
        self.window_title_keyword = window_title_keyword
        self.default_settle = float(default_settle)
        self._keeper_created = False  # ✅ 브라우저 종료 방지용 keeper 탭 생성 여부

        # PyAutoGUI failsafe 설정 보관/적용
        self._prev_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = bool(failsafe)

        # 크롬 경로 확정
        self.chrome_path = chrome_path or self._which_chrome()
        if not self.chrome_path:
            raise ChromeOpenError("크롬 실행 파일을 찾을 수 없습니다. (Chrome 미설치 또는 PATH 미등록)")

        # 전용 프로필 디렉터리: 한 번만 생성
        self.profile_dir = None
        if isolate_profile:
            # PID 기반 임시 경로 → 동시 다중 프로세스 사용 시 충돌 완화
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

        - 활성창 확보 후: Ctrl+T → Ctrl+L → "about:blank" 붙여넣기 → Enter
        - 이미 생성된 경우에는 재생성하지 않음
        """
        if not self._keeper_created:
            self._activate_chrome_or_raise()
            self._hotkey("ctrl", "t", pause=0.08)  # 새 탭 열기
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
        """
        크롬 실행 파일 경로를 탐색한다.
        - 우선 shutil.which("chrome")
        - 실패 시 Windows의 대표 경로 후보를 순회하여 존재 검사
        """
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
        """
        chrome.exe 프로세스 존재 여부 확인(Windows 전제).

        Returns
        -------
        bool
            하나라도 동작 중이면 True
        """
        for p in psutil.process_iter(["name"]):
            if (p.info.get("name") or "").lower() == "chrome.exe":
                return True
        return False

    def _activate_chrome_or_raise(self, timeout: float = 5.0) -> None:
        """
        크롬 창을 전경(Active Window)으로 올린다. 실패 시 예외.

        동작
        ----
        - pygetwindow로 모든 창을 조회 → 제목에 window_title_keyword 포함 창 필터
        - 여러 개면 '뒤에서 앞으로' 순회하며 복원/활성 시도
        - 최소화되어 있으면 restore 후 activate
        - 활성화 확인: getActiveWindow()._hWnd 비교

        Parameters
        ----------
        timeout : float
            활성화 최대 대기 시간(초). 다중 모니터/윈도우 전환 지연 고려.

        Raises
        ------
        ChromeOpenError
            타임아웃 내에 전경 전환 실패
        """
        end = time.time() + timeout
        while time.time() < end:
            try:
                # 제목에 키워드 포함된 창만 대상으로
                wins = [w for w in gw.getAllWindows() if w.title and self.window_title_keyword in w.title]
                if wins:
                    for w in reversed(wins):
                        try:
                            if w.isMinimized:
                                try:
                                    w.restore()
                                    time.sleep(0.1)
                                except Exception:
                                    # 일부 상황(권한/가상 데스크톱)에서 restore가 실패할 수 있음
                                    pass
                            w.activate()
                            time.sleep(0.15)
                            # 활성화 검증
                            active = gw.getActiveWindow()
                            if active and active._hWnd == w._hWnd:
                                return
                        except Exception:
                            # 창 하나에 대한 activate 실패 → 다음 창 시도
                            pass
            except Exception:
                # 일시적인 윈도우 열거 실패 → 재시도
                pass
            time.sleep(0.15)
        raise ChromeOpenError("크롬 창을 전경으로 가져오지 못했습니다.")

    def _hotkey(self, *keys: str, pause: float = 0.06, retries: int = 1) -> None:
        """
        pyautogui.hotkey()를 약간의 재시도로 안정 전송.

        Parameters
        ----------
        *keys : str
            'ctrl', 't' 등 순차 키 지정
        pause : float
            전송 후 안정 대기(초)
        retries : int
            예외 발생 시 재시도 횟수. 0이면 단발성.

        Notes
        -----
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
        주소창 등 안전 입력을 위해 타이핑 대신 '클립보드 붙여넣기'를 사용.

        Parameters
        ----------
        text : str
            붙여넣을 텍스트 (URL 등)
        pause : float
            copy 후 붙여넣기 전 준비 대기(초)

        Notes
        -----
        - 한글/이모지/특수문자 입력 시 타이핑보다 안정적
        - 기존 클립보드 내용을 백업→복원 하여 사용자 환경을 보존
        """
        backup = pyperclip.paste()
        try:
            pyperclip.copy(text)
            time.sleep(pause)
            self._hotkey("ctrl", "v", pause=0.04)
        finally:
            # 비정상 종료 대비: 되도록 원래 클립보드 내용을 복구
            time.sleep(0.02)
            pyperclip.copy(backup)

    def _spawn_chrome_url(self, url: str) -> None:
        """
        크롬 프로세스를 URL과 함께 스폰한다. (동일 user-data-dir로 탭 유도)

        Parameters
        ----------
        url : str
            열고자 하는 URL. 크롬 인자 마지막에 전달.

        Raises
        ------
        ChromeOpenError
            Popen 실패 등 프로세스 스폰 실패
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
                # 동일 프로필 → 동일 창에 탭으로 붙도록 유도
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

        Parameters
        ----------
        url : str
            열고자 하는 URL (유효한 문자열 필수)
        replace_previous : bool
            True면 "직전 탭"을 닫는다.
            - 주의: 활성 탭 가정이 어긋나면 포커스 꼬임 가능 → 기본 False 권장
        settle : Optional[float]
            스폰/탭 포커싱 이후 안정화 대기(초). None이면 default_settle 사용.

        Raises
        ------
        ChromeOpenError
            - url이 유효하지 않거나 문자열이 아닌 경우
            - 크롬 활성화 실패
        """
        if not url or not isinstance(url, str):
            raise ChromeOpenError("유효한 URL 문자열이 필요합니다.")

        was_running = self.is_running
        self._spawn_chrome_url(url)
        time.sleep(self.default_settle if settle is None else float(settle))
        self._activate_chrome_or_raise()

        if replace_previous and was_running:
            # 새 탭 활성 가정 → 왼쪽(직전) 탭으로 이동 후 닫기
            self._hotkey("ctrl", "shift", "tab", pause=0.05)
            self._hotkey("ctrl", "w", pause=0.05)

    def close_active_tab(self, pause: float = 0.08) -> None:
        """
        현재 활성 탭을 닫는다.

        Notes
        -----
        - 최초 1회 ensure_keeper_tab()으로 keeper 탭을 만들어두면,
          연속 Ctrl+W로 탭을 닫아도 브라우저 프로세스가 즉시 종료되지 않음.
        """
        self._activate_chrome_or_raise()
        self.ensure_keeper_tab()
        self._hotkey("ctrl", "w", pause=pause)

    def copy_current_url(self) -> str:
        """
        활성 탭의 현재 URL을 주소창에서 복사하여 반환.

        Returns
        -------
        str
            현재 탭의 URL(공백 제거), 실패 시 빈 문자열
        """
        self._activate_chrome_or_raise()
        self._hotkey("ctrl", "l", pause=0.05)  # 주소창 포커스
        self._hotkey("ctrl", "c", pause=0.05)  # 복사
        time.sleep(0.04)
        return (pyperclip.paste() or "").strip()

    def copy_page_html_via_view_source(self, settle_after_open: float = 1.0) -> str:
        """
        활성 탭의 '원본 HTML 소스'를 안전하게 가져온다. (view-source 경유)

        순서
        ----
        1) 현재 URL 복사 (주소창 Ctrl+L → Ctrl+C)
        2) 새 탭 열기 (Ctrl+T)
        3) 주소창에 'view-source:<URL>'을 '붙여넣기'로 입력(타이핑 금지) → Enter
        4) 페이지 로드 대기 후 전체 선택(Ctrl+A) → 복사(Ctrl+C)
        5) 임시 view-source 탭 닫기(Ctrl+W) → 원래 탭으로 복귀

        Parameters
        ----------
        settle_after_open : float
            view-source 탭을 연 뒤 렌더 완료까지 대기할 시간(초).
            - 페이지 소스가 매우 큰 경우 늘릴 필요가 있음.

        Returns
        -------
        str
            HTML 소스 텍스트

        Raises
        ------
        ChromeOpenError
            - 현재 탭 URL 복사 실패(주소창 비어있음 등)
            - 복사 종료 후 클립보드가 비어있는 경우(로드 지연/보안 차단 등)
        """
        self._activate_chrome_or_raise()

        # 1) 현재 URL 확보
        self._hotkey("ctrl", "l", pause=0.05)
        self._hotkey("ctrl", "c", pause=0.05)
        time.sleep(0.04)
        cur_url = (pyperclip.paste() or "").strip()
        if not cur_url:
            raise ChromeOpenError("현재 탭 URL을 읽지 못했습니다. (주소창 복사 실패)")

        # 2) 새 탭 열기
        self._hotkey("ctrl", "t", pause=0.08)

        # 3) 주소창에 view-source:<URL>을 안전하게 붙여넣기
        self._hotkey("ctrl", "l", pause=0.04)
        vs_url = f"view-source:{cur_url}" if not cur_url.startswith("view-source:") else cur_url
        self._paste_text(vs_url)
        pyautogui.press("enter")
        time.sleep(float(settle_after_open))

        # 4) 전체 복사(클립보드 채워질 때까지 짧게 대기)
        clip_backup = pyperclip.paste()
        try:
            pyperclip.copy("")  # 초기화
            self._hotkey("ctrl", "a", pause=0.05)
            self._hotkey("ctrl", "c", pause=0.08)
            # 클립보드가 실제로 채워질 시간을 조금 준다
            t0 = time.time()
            html = ""
            while time.time() - t0 < 2.0:
                html = pyperclip.paste() or ""
                if html:
                    break
                time.sleep(0.05)
        finally:
            # 복사 실패 시에도 기존 클립보드를 복구
            if not html:
                pyperclip.copy(clip_backup)

        # 5) 임시 view-source 탭 닫고 복귀
        self._hotkey("ctrl", "w", pause=0.08)

        if not html:
            raise ChromeOpenError("페이지 소스 복사에 실패했습니다. (클립보드가 비어있음)")
        return html

    def open_and_grab_html(
            self,
            url: str,
            *,
            settle: Optional[float] = None,
            close_tab_after: bool = True,
            view_source_settle: float = 1.0,
    ) -> str:
        """
        URL을 새 탭으로 열고, view-source 경유로 HTML을 수집한 뒤
        필요 시 활성 탭을 닫아 '한 탭 유지' 정책을 돕는다.

        Parameters
        ----------
        url : str
            열 URL
        settle : Optional[float]
            open_url 후 안정화 대기(초). None이면 default_settle 사용.
        close_tab_after : bool
            True면 수집 후 현재 활성 탭(= 방금 연 탭)을 닫음.
        view_source_settle : float
            view-source 탭 로드 안정 대기(초).

        Returns
        -------
        str
            수집한 HTML 소스

        Raises
        ------
        ChromeOpenError
            - URL 열기 실패/활성화 실패 등 내부 예외 전파
        """
        self.open_url(url, replace_previous=False, settle=settle)
        html = self.copy_page_html_via_view_source(settle_after_open=view_source_settle)
        if close_tab_after:
            self.close_active_tab()
        return html

    def close_all(self) -> None:
        """
        모든 chrome.exe 프로세스를 강제 종료한다. (다른 앱의 크롬 세션까지 영향을 줄 수 있음!!)

        Notes
        -----
        - Windows 전용: taskkill 사용
        - 보안 정책/권한에 따라 실패할 수 있음(check=False로 무시)
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
        return False
