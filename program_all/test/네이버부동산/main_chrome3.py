# file: chrome_macro.py
# 목적: 매크로(키보드/창 포커싱) 방식으로 "크롬에서 URL 열기"만 담당하는 안정 모듈
# 특징:
#  - 간결 + 예외처리 + 모든 라인 주석
#  - Selenium/Playwright/Puppeteer 미사용
#  - 브라우저가 떠 있으면: 새 탭으로 열고 직전 탭(바로 왼쪽) 1개 닫기 옵션 지원
#  - 파싱(HTML 수집/분석)은 호출측에서 수행 (이 모듈 역할 아님)

import os
import time
import shutil
import subprocess
from typing import Optional, List, Dict, Any

import psutil  # 프로세스 존재 여부 확인용 (chrome.exe 감시)
import pyautogui  # 단축키 전송 (Ctrl+Shift+Tab, Ctrl+W 등)
import pygetwindow as gw  # 창 전경 활성화 시도
import re, json  # __NEXT_DATA__ 추출용
import pyperclip  # 클립보드 읽기


# 전경 창(활성 창): 화면 맨 앞에 떠 있고, 키보드/마우스 입력이 이 창으로 들어가는 상태. 타이틀 바가 강조(하이라이트)돼 있고 Alt+Tab 했을 때 바로 보이는 그 창.

# 전역 누적 리스트: 모든 URL에 대한 최종 결과가 여기 모임
ALL_RESULTS: List[Dict[str, Any]] = []


class ChromeOpenError(Exception):
    """크롬 실행/제어 중 발생 예외 (모듈 외부에서 캐치하기 쉬우라고 커스텀)."""


# 필수 키 정의 (result에 반드시 있어야 하는 키들)
REQUIRED_RESULT_KEYS = {
    "brokerageName",
    "brokerName",
    "address",
    "businessRegistrationNumber",
    "profileImageUrl",
    "brokerId",
    "ownerConfirmationSaleCount",
    "phone",
}
REQUIRED_PHONE_KEYS = {"brokerage", "mobile"}


def _is_target_broker_result(obj: Dict[str, Any]) -> bool:
    """
    우리가 원하는 '중개사 정보' 스키마를 만족하는 result 인지 검사.
    - result 딕셔너리 내부에 REQUIRED_RESULT_KEYS 모두 존재
    - result['phone']는 dict 이고 REQUIRED_PHONE_KEYS 모두 존재
    """
    if not isinstance(obj, dict):
        return False

    # 1) 1차 키 존재 여부
    if not REQUIRED_RESULT_KEYS.issubset(obj.keys()):
        return False

    # 2) phone 구조 검사
    phone = obj.get("phone")
    if not isinstance(phone, dict):
        return False
    if not REQUIRED_PHONE_KEYS.issubset(phone.keys()):
        return False

    # (선택) 타입 검증이 필요하면 아래 주석 해제해서 더 엄격히 체크 가능
    # if not isinstance(obj["brokerageName"], str): return False
    # if not isinstance(obj["ownerConfirmationSaleCount"], (int, float)): return False
    # if not isinstance(phone["brokerage"], str) or not isinstance(phone["mobile"], str): return False

    return True


def parse_target_broker_results(html: str) -> List[Dict[str, Any]]:
    """
    HTML에서 __NEXT_DATA__ → dehydratedState.queries[*].state.data.result 들을 얻고,
    그 중 _is_target_broker_result 를 만족하는 것만 반환.
    (이 함수는 'parse_next_queries_results'가 이미 존재한다고 가정하고 재사용)
    """
    all_results = parse_next_queries_results(html)  # 이전 단계에서 만든 함수 재사용
    return [r for r in all_results if _is_target_broker_result(r)]



def _which_chrome() -> Optional[str]:
    """
    크롬 실행 파일 경로를 탐색.
    1) PATH에 등록된 'chrome' 우선
    2) 윈도우의 대표 설치 경로 순회
    - 찾으면 절대경로 문자열 반환, 없으면 None
    """
    # PATH 검색 (터미널에서 'chrome'만 쳐도 실행되는 상태인지)
    cand = shutil.which("chrome")
    if cand:
        return cand

    # 대표 설치 경로들 점검 (일반적으로 여기에 존재)
    candidates = [
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def _is_chrome_running() -> bool:
    """
    chrome.exe 프로세스가 떠 있는지 확인.
    - 떠 있으면 True, 아니면 False
    """
    for p in psutil.process_iter(["name"]):
        if (p.info.get("name") or "").lower() == "chrome.exe":
            return True
    return False


def _activate_chrome_or_raise(timeout: float = 5.0) -> None:
    """
    크롬 창을 전경으로 '필수적으로' 올린다.
    - 성공 못 하면 예외 발생시켜 호출측에서 흐름 제어 가능하게 함.
    - 여러 창이 있을 수 있으므로 타이틀에 'Chrome' 포함된 창들을 뒤에서부터 시도.
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            # 현재 떠 있는 모든 창 중 'Chrome' 텍스트가 제목에 포함된 창 수집
            wins = [w for w in gw.getAllWindows() if w.title and "Chrome" in w.title]
            if wins:
                # 가장 최근에 활성된 걸로 보이는 뒤쪽부터 시도
                for w in reversed(wins):
                    try:
                        # 최소화되어 있으면 활성화가 안 될 수 있으니 스킵
                        if not w.isMinimized:
                            w.activate()       # 전경으로
                            time.sleep(0.15)   # OS 전환 딜레이
                            return             # 성공
                    except Exception:
                        # 개별 창 활성화 실패 시 다음 창 시도
                        pass
        except Exception:
            # 윈도우 열람 실패 시 잠깐 대기 후 재시도
            pass
        time.sleep(0.15)
    # 끝까지 실패하면 예외
    raise ChromeOpenError("크롬 창을 전경으로 가져오지 못했습니다.")


def _spawn_chrome_url(chrome_path: str, url: str) -> None:
    """
    chrome.exe에 URL을 '직접 인자'로 전달하여 열기.
    - 이미 실행 중이면: 기존 창의 '새 탭'으로 열림 (Chrome 기본 동작)
    - 미실행이면: 새 창으로 기동하며 해당 URL 로드
    """
    try:
        subprocess.Popen(
            [chrome_path, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    except Exception as e:
        raise ChromeOpenError(f"크롬 실행 실패: {e}")


def _hotkey(*keys: str, pause: float = 0.05) -> None:
    """
    단축키 전송 도우미.
    - pyautogui의 전역 PAUSE를 건드리지 않고 호출 단위 딜레이만 줌.
    - 실패 시 예외를 올려 호출부에서 제어.
    """
    pyautogui.hotkey(*keys)
    time.sleep(pause)


def open_url(url: str, *, replace_previous: bool = False, settle: float = 1.0) -> None:
    """
    [공개 함수] 크롬에 URL을 연다.

    동작 개요:
      - 크롬이 꺼져 있으면: 새 창으로 기동 + 해당 URL 로드
      - 크롬이 떠 있으면: 기존 창의 '새 탭'으로 로드 (Chrome 기본 동작)
      - replace_previous=True 이고 '이미 떠 있는' 상황이면:
          1) 새 탭이 오른쪽에 생성되어 활성되었다고 가정
          2) 바로 왼쪽(직전) 탭으로 이동(Ctrl+Shift+Tab)
          3) 그 탭을 닫기(Ctrl+W)
          4) 포커스는 자동으로 오른쪽(=새 탭)에 남음

    매개변수:
      - url: 열 주소 (필수, 문자열)
      - replace_previous: 직전 탭 1개를 닫을지 여부 (기본 False)
      - settle: 새 탭/창 생성 후 안정화 대기 시간(초). 환경에 따라 0.8~1.5 조절.

    예외:
      - ChromeOpenError: 경로 탐색/실행/포커스 실패 등 안정성 저하가 우려될 때 발생
    """
    # URL 유효성 간단 점검
    if not url or not isinstance(url, str):
        raise ChromeOpenError("유효한 URL 문자열이 필요합니다.")

    # 크롬 경로 찾기 (없으면 실행 불가)
    chrome_path = _which_chrome()
    if not chrome_path:
        raise ChromeOpenError("크롬 실행 파일을 찾을 수 없습니다. (Chrome 미설치 또는 PATH 미등록)")

    # pyautogui 안전 설정: 모서리로 마우스 이동 시 강제 중단 허용
    pyautogui.FAILSAFE = True

    # 현재 크롬 실행 여부 (replace_previous 로직 분기용)
    was_running = _is_chrome_running()

    # URL 열기 (새 창 또는 새 탭)
    _spawn_chrome_url(chrome_path, url)

    # 탭/창 생성 + 렌더링 시작 대기 (너무 길게 줄 필요 없음)
    time.sleep(settle)

    # 창 포커스 확보 (키 입력 대상이 반드시 크롬이 되도록)
    #  - 열자마자 전경일 가능성이 높지만, 안전하게 보장
    _activate_chrome_or_raise()

    # 직전 탭 닫기 옵션 처리
    if replace_previous and was_running:
        # 가정: 현재 활성 탭은 "방금 연 새 탭(오른쪽)"임.
        # 1) 왼쪽(직전) 탭으로 이동
        _hotkey("ctrl", "shift", "tab", pause=0.05)
        # 2) 해당 탭 닫기
        _hotkey("ctrl", "w", pause=0.05)
        # 이제 포커스는 자동으로 오른쪽(=새 탭)에 남는다.


def close_all_chrome() -> None:
    """
    모든 작업이 끝났을 때 크롬 전체 종료가 필요하면 호출.
    - 안전하게 'chrome.exe'만 종료 (다른 앱에 영향 없음)
    - 필요 없다면 호출하지 않아도 됨.
    """
    if not _is_chrome_running():
        return
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "chrome.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        time.sleep(0.3)  # 종료 정리 대기
    except Exception as e:
        raise ChromeOpenError(f"크롬 종료 실패: {e}")


def copy_page_html_via_view_source(settle_after_open: float = 0.8) -> str:
    """
    현재 '컨텐츠 탭'이 활성 상태라고 가정하고,
    1) 주소창에서 현재 URL 복사
    2) 새 탭(Ctrl+T)으로 view-source:<URL> 열기
    3) 전체 선택(Ctrl+A) 후 복사(Ctrl+C)
    4) 임시 탭 닫기(Ctrl+W)
    5) 클립보드 텍스트(=원본 HTML 소스) 반환

    주의:
    - 크롬이 전경(활성) 창이어야 키 입력이 정확히 들어간다.
    """
    # 1) 크롬 전경 확보
    _activate_chrome_or_raise()

    # 2) 현재 URL 복사 (Ctrl+L, Ctrl+C)
    _hotkey("ctrl", "l", pause=0.06)
    _hotkey("ctrl", "c", pause=0.06)
    time.sleep(0.05)
    cur_url = (pyperclip.paste() or "").strip()

    if not cur_url:
        raise ChromeOpenError("현재 탭 URL을 읽지 못했습니다. (주소창 복사 실패)")

    # 3) 새 탭으로 view-source 열기
    _hotkey("ctrl", "t", pause=0.08)
    # 주소창 포커스는 새 탭에서 자동으로 잡힘
    vs_url = f"view-source:{cur_url}" if not cur_url.startswith("view-source:") else cur_url
    pyautogui.typewrite(vs_url, interval=0.0)
    pyautogui.press("enter")
    time.sleep(settle_after_open)  # 소스 렌더 대기

    # 4) 전체 선택 후 복사
    _hotkey("ctrl", "a", pause=0.06)
    _hotkey("ctrl", "c", pause=0.08)
    time.sleep(0.05)
    html = pyperclip.paste() or ""

    # 5) 임시 view-source 탭 닫기 → 원 탭으로 포커스 복귀
    _hotkey("ctrl", "w", pause=0.08)

    if not html:
        raise ChromeOpenError("페이지 소스 복사에 실패했습니다. (클립보드가 비어있음)")

    return html


def parse_next_queries_results(html: str) -> list[dict]:
    """
    HTML 문자열에서 <script id="__NEXT_DATA__" type="application/json">...</script>
    내부의 JSON을 파싱하여, dehydratedState.queries[*].state.data.result 만 배열로 반환.

    반환: List[dict]  (각 dict가 'result' 객체)
    """
    if not isinstance(html, str) or not html:
        return []

    # 1) __NEXT_DATA__ 스크립트 블록 추출
    m = re.search(
        r'<script\s+id=["\']__NEXT_DATA__["\']\s+type=["\']application/json["\'][^>]*>(\{.*?\})</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return []

    # 2) JSON 로드
    try:
        data = json.loads(m.group(1))
    except Exception:
        return []

    # 3) dehydratedState.queries 접근
    dstate = (data.get("props") or {}).get("pageProps", {}).get("dehydratedState", {})
    queries = dstate.get("queries") or []
    results: list[dict] = []

    for q in queries:
        try:
            st = (q or {}).get("state", {})
            dt = (st or {}).get("data", {})
            if dt.get("isSuccess") is True and isinstance(dt.get("result"), dict):
                results.append(dt["result"])  # 그대로 수집
        except Exception:
            # 한 항목 파싱 실패는 건너뜀
            continue

    return results



# ─────────────────────────────────────────────────────────────────────────────
# 사용 예시: URL 열기 → 소스 복사 → __NEXT_DATA__ 파싱 → result 배열 축적
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        close_all_chrome()
        time.sleep(0.8)

        article_ids = ['2543143946', '2546530248']
        BASE = "https://fin.land.naver.com/articles/"
        all_results = []

        for i, aid in enumerate(article_ids):
            url = f"{BASE}{aid}"

            # 1) 새 탭으로 열고(첫 건은 기존 탭 없음 → False), 이전 탭 닫기(둘째부터 True)
            open_url(url, replace_previous=(i > 0), settle=1.0)
            time.sleep(0.6)  # 환경에 따라 조절 (0.5~1.2)

            # 2) 현재 탭(=방금 연 컨텐츠 탭)의 원본 HTML 소스 가져오기
            html = copy_page_html_via_view_source(settle_after_open=0.8)

            # 3) __NEXT_DATA__에서 result 배열만 추출
            targets = parse_target_broker_results(html)  # 원하는 스키마만 필터링
            ALL_RESULTS.extend(targets)                  # 전역 누적

        print(ALL_RESULTS)

    finally:
        close_all_chrome()
