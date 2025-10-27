# kipris_macro_newchrome.py
# -*- coding: utf-8 -*-
"""
요구사항:
- 크롬을 '새로' 띄워서 좌상단(0,0) 붙이고 '최대화' 후 작업 시작
- data.xlsx 의 '출원번호(일자)' 컬럼을 읽어
  1) https://www.kipris.or.kr/khome/main.do 이동
  2) 화면 중앙(오프셋 적용) 클릭 → input 포커스
  3) "AN=[<applno>]" 입력 후 Enter
  4) 브라우저 '좌우 중앙'(=창 가로 중앙) 클릭(오프셋 적용) → 상세보기

실행 전:
    pip install pandas openpyxl pyautogui pygetwindow pyperclip
(Windows에서 pygetwindow 문제시 pip install pywin32)
"""

import os
import time
import random
import subprocess
import pandas as pd
import pyautogui
import pygetwindow as gw
import pyperclip

# ===================== 사용자 설정 =====================
EXCEL_PATH = "data.xlsx"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # 환경에 맞게
MAIN_URL   = "https://www.kipris.or.kr/khome/main.do"

# 입력 포커스 클릭: 창 '중앙' 기준 오프셋(px)
FOCUS_OFF_X  = 0
FOCUS_OFF_Y  = 100  # 입력창이 중앙보다 위쪽이면 음수(위로)

# 상세 클릭: 창 '가로 중앙' 기준 오프셋(px)https://www.kipris.or.kr/khome/main.do

DETAIL_OFF_X = -200
DETAIL_OFF_Y = 140   # 결과 타이틀 영역이 중앙 아래쪽이면 양수(아래로)https://www.kipris.or.kr/khome/main.do


# 각 단계 지연(사람같이)
TYPE_DELAY_RANGE_MS = (40, 110)  # 타이핑 키당 지연(ms)
AFTER_ENTER_WAIT    = (1.2, 2.0) # 검색 후 결과 대기
AFTER_DETAIL_WAIT   = (0.8, 1.6) # 상세 클릭 후 대기
BETWEEN_ITEMS_WAIT  = (0.8, 2.2) # 항목 사이 쉬는 시간
# ======================================================


def slow_type(text: str):
    for ch in text:
        pyautogui.write(ch)
        time.sleep(random.uniform(*TYPE_DELAY_RANGE_MS) / 1000.0)


def digits_only(v) -> str:
    if v is None:
        return ""
    s = str(v)
    s = s.split("(")[0]
    return "".join(ch for ch in s if ch.isdigit())


def start_fresh_chrome():
    """
    '새' 크롬 창을 띄움.
    - 기존 세션을 건드리지 않으려면 --new-window 정도만 사용.
    - 완전 새 프로필을 원하면 --user-data-dir 임시 폴더를 사용해도 됨.
    """
    if not os.path.exists(CHROME_PATH):
        raise FileNotFoundError(f"Chrome 경로 확인: {CHROME_PATH}")

    # 새 창 실행 (필요 시 --new-window)
    # 팝업 억제용으로 --disable-features=RendererCodeIntegrity 등 넣을 수도 있으나 최소로 유지
    subprocess.Popen([CHROME_PATH, "--new-window", "about:blank"])
    time.sleep(1.0)  # 프로세스 부팅 여유


def find_new_chrome_window(timeout=10):
    """
    막 띄운 크롬 창을 찾아 반환.
    """
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        wins = []
        try:
            # 일반적으로 'Chrome' 또는 '새 탭 - Google Chrome' 등의 타이틀
            for key in ("Google Chrome", "Chrome", "chrome", "새 탭", "New Tab"):
                wins.extend(gw.getWindowsWithTitle(key))
        except Exception:
            pass

        # 중복 제거
        uniq = []
        seen = set()
        for w in wins:
            try:
                ident = (w.title, w.left, w.top, w.width, w.height)
            except Exception:
                ident = (id(w),)
            if ident not in seen:
                seen.add(ident)
                uniq.append(w)

        # visible한 창 선택
        for w in uniq:
            try:
                vis = getattr(w, "visible", True)
            except Exception:
                vis = True
            if vis:
                return w

        last = uniq[-1] if uniq else None
        time.sleep(0.3)
    return last


def move_to_top_left_and_maximize(win):
    """
    좌상단(0,0)에 붙이고 최대화.
    """
    try:
        # 먼저 (0,0)으로 이동
        win.moveTo(0, 0)
        time.sleep(0.1)
    except Exception:
        pass
    try:
        win.maximize()
        time.sleep(0.2)
    except Exception:
        pass


def activate_window(win):
    try:
        win.activate()
        time.sleep(0.25)
    except Exception:
        try:
            win.minimize(); time.sleep(0.1); win.restore(); time.sleep(0.25)
        except Exception:
            pass


def click_window_center(win, offx=0, offy=0):
    try:
        left, top, width, height = win.left, win.top, win.width, win.height
    except Exception:
        sw, sh = pyautogui.size()
        cx, cy = sw // 2 + offx, sh // 2 + offy
        pyautogui.moveTo(cx, cy, duration=random.uniform(0.08, 0.22))
        pyautogui.click()
        return

    cx, cy = left + width // 2 + offx, top + height // 2 + offy
    pyautogui.moveTo(cx, cy, duration=random.uniform(0.5, 0.6))
    pyautogui.click()


def ensure_main_page(win):
    """
    주소창 포커스 → MAIN_URL 이동 → 잠깐 대기
    """
    activate_window(win)
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.15)
    pyperclip.copy(MAIN_URL)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(random.uniform(0.9, 1.5))


def run():
    # 1) 새 크롬 띄우기
    start_fresh_chrome()
    win = find_new_chrome_window(timeout=12)
    if not win:
        print("❌ 새 크롬 창을 찾지 못했습니다.")
        return

    # 2) 좌상단 부착 + 최대화
    move_to_top_left_and_maximize(win)
    activate_window(win)

    # 3) 엑셀 로드
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ 엑셀 없음: {EXCEL_PATH}")
        return
    df = pd.read_excel(EXCEL_PATH)

    if "출원번호(일자)" not in df.columns:
        # 첫 컬럼 fallback
        first_col = df.columns[0]
        print(f"⚠️ '출원번호(일자)' 컬럼 없음 → '{first_col}' 사용")
        df = df.rename(columns={first_col: "출원번호(일자)"})

    rows = []
    for _, r in df.iterrows():
        v = r.get("출원번호(일자)")
        if pd.isna(v):
            continue
        appl = digits_only(v)
        if appl:
            rows.append(appl)

    if not rows:
        print("⚠️ 처리할 출원번호 없음")
        return

    # 4) 루프 실행
    for i, appl in enumerate(rows, start=1):
        print(f"[{i}/{len(rows)}] {appl}")

        # 4-1) main.do 로 이동
        ensure_main_page(win)

        # 4-2) 창 중앙(오프셋) 클릭 → 입력 포커스
        click_window_center(win, FOCUS_OFF_X, FOCUS_OFF_Y)
        time.sleep(random.uniform(0.10, 0.22))

        # 4-3) 기존값 삭제 후 AN=[appl] 입력 + Enter
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.06)
        pyautogui.press("backspace")
        time.sleep(0.08)

        query = f"AN=[{appl}]"
        # 한글/IME 이슈 줄이려면 클립보드-붙여넣기 사용 권장
        pyperclip.copy(query)
        pyautogui.hotkey("ctrl", "v")
        # 또는: slow_type(query)

        time.sleep(0.08)
        pyautogui.press("enter")

        # 4-4) 결과 대기
        time.sleep(random.uniform(*AFTER_ENTER_WAIT))

        # 4-5) 상세 클릭 (창 가로 중앙 + 오프셋)
        click_window_center(win, DETAIL_OFF_X, DETAIL_OFF_Y)

        # 4-6) 상세 대기 및 휴지
        time.sleep(random.uniform(*AFTER_DETAIL_WAIT))
        time.sleep(random.uniform(*BETWEEN_ITEMS_WAIT))

    print("✅ 완료")


if __name__ == "__main__":
    run()
