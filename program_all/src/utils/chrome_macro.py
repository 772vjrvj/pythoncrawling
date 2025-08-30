# chrome_macro.py (class 버전)
# 목적: 매크로(키보드/창 포커싱) 방식으로 "크롬에서 URL 열기"만 담당하는 안정 모듈 (객체지향)
# 특징:
#  - Selenium/Playwright/Puppeteer 미사용
#  - 브라우저가 떠 있으면: 새 탭으로 열고, 옵션에 따라 직전 탭(왼쪽) 1개 닫기 지원
#  - __enter__/__exit__ 지원 (with 문)
#  - 전역 함수 대신 ChromeMacro 인스턴스 메서드로 제공

import os
import re
import json
import time
import shutil
import subprocess
from typing import Optional

import psutil
import pyautogui
import pygetwindow as gw
import pyperclip


class ChromeOpenError(Exception):
    """크롬 실행/제어 중 발생 예외."""


class ChromeMacro:
    """
    매크로(키보드/윈도우 포커싱)로 크롬을 제어하는 경량 도우미.

    Parameters
    ----------
    window_title_keyword : str
        전경 활성화 시 찾을 창 타이틀 키워드 (기본: 'Chrome')
    default_settle : float
        새 탭/창 생성 후 안정화 기본 대기 시간(초)
    failsafe : bool
        pyautogui FAILSAFE (마우스 화면 모서리 이동 시 강제중단) 사용 여부
    chrome_path : Optional[str]
        크롬 실행 파일 경로를 직접 지정(미지정 시 자동 탐색)
    """

    def __init__(
            self,
            window_title_keyword: str = "Chrome",
            default_settle: float = 1.0,
            failsafe: bool = True,
            chrome_path: Optional[str] = None,
    ) -> None:
        self.window_title_keyword = window_title_keyword
        self.default_settle = float(default_settle)
        self._prev_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = bool(failsafe)

        self.chrome_path = chrome_path or self._which_chrome()
        if not self.chrome_path:
            raise ChromeOpenError("크롬 실행 파일을 찾을 수 없습니다. (Chrome 미설치 또는 PATH 미등록)")

    # ─────────────────────────────────────────
    # 기본 유틸
    # ─────────────────────────────────────────
    @staticmethod
    def _which_chrome() -> Optional[str]:
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
        for p in psutil.process_iter(["name"]):
            if (p.info.get("name") or "").lower() == "chrome.exe":
                return True
        return False

    def _activate_chrome_or_raise(self, timeout: float = 5.0) -> None:
        """크롬 창을 전경으로 올림(실패 시 예외)."""
        end = time.time() + timeout
        while time.time() < end:
            try:
                wins = [w for w in gw.getAllWindows() if w.title and self.window_title_keyword in w.title]
                if wins:
                    for w in reversed(wins):
                        try:
                            if not w.isMinimized:
                                w.activate()
                                time.sleep(0.15)
                                return
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(0.15)
        raise ChromeOpenError("크롬 창을 전경으로 가져오지 못했습니다.")

    @staticmethod
    def _hotkey(*keys: str, pause: float = 0.05) -> None:
        pyautogui.hotkey(*keys)
        time.sleep(pause)

    def _spawn_chrome_url(self, url: str) -> None:
        try:
            subprocess.Popen(
                [self.chrome_path, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as e:
            raise ChromeOpenError(f"크롬 실행 실패: {e}")

    # ─────────────────────────────────────────
    # 공개 메서드
    # ─────────────────────────────────────────
    @property
    def is_running(self) -> bool:
        return self._is_chrome_running()

    def open_url(self, url: str, *, replace_previous: bool = False, settle: Optional[float] = None) -> None:
        """
        크롬에 URL 열기(새 탭 또는 새 창).

        replace_previous=True 이고 이미 크롬이 떠 있으면:
          1) 새 탭이 오른쪽에 생성됨(활성)
          2) 왼쪽(직전) 탭으로 이동(Ctrl+Shift+Tab)
          3) 그 탭 닫기(Ctrl+W)
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

    def copy_current_url(self) -> str:
        """활성 탭의 주소창에서 현재 URL 복사해서 반환."""
        self._activate_chrome_or_raise()
        self._hotkey("ctrl", "l", pause=0.06)
        self._hotkey("ctrl", "c", pause=0.06)
        time.sleep(0.05)
        return (pyperclip.paste() or "").strip()

    def copy_page_html_via_view_source(self, settle_after_open: float = 0.8) -> str:
        """
        현재 활성 탭의 원본 HTML 소스 가져오기.
        1) 현재 URL 복사 → 2) 새 탭으로 view-source:URL 열기 → 3) 전체복사 → 4) 탭 닫기
        """
        self._activate_chrome_or_raise()

        # 현재 URL 확보
        self._hotkey("ctrl", "l", pause=0.06)
        self._hotkey("ctrl", "c", pause=0.06)
        time.sleep(0.05)
        cur_url = (pyperclip.paste() or "").strip()
        if not cur_url:
            raise ChromeOpenError("현재 탭 URL을 읽지 못했습니다. (주소창 복사 실패)")

        # view-source 열기
        self._hotkey("ctrl", "t", pause=0.08)
        vs_url = f"view-source:{cur_url}" if not cur_url.startswith("view-source:") else cur_url
        pyautogui.typewrite(vs_url, interval=0.0)
        pyautogui.press("enter")
        time.sleep(float(settle_after_open))

        # 소스 전체 복사
        self._hotkey("ctrl", "a", pause=0.06)
        self._hotkey("ctrl", "c", pause=0.08)
        time.sleep(0.05)
        html = pyperclip.paste() or ""

        # 임시 탭 닫기 → 원탭 복귀
        self._hotkey("ctrl", "w", pause=0.08)

        if not html:
            raise ChromeOpenError("페이지 소스 복사에 실패했습니다. (클립보드가 비어있음)")
        return html

    def close_all(self) -> None:
        """모든 chrome.exe 종료 (다른 앱 영향 없음)."""
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
    # 컨텍스트 매니저
    # ─────────────────────────────────────────
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # FAILSAFE 원복
        pyautogui.FAILSAFE = self._prev_failsafe
        # 여기서 크롬을 강제 종료할 필요는 없음(선택)
        # 필요 시: self.close_all()
        return False  # 예외 전파
