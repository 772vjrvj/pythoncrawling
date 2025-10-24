# -*- coding: utf-8 -*-
"""
KIPRIS 상세검색 자동화 (AP / AN / IPC + 페이지네이션)
- 엑셀 Sheet1 에서 AP/AN/IPC 컬럼 자동 인식(헤더 탐지 + 정규화)
- Selenium으로 상세검색 수행
- # === 신규 === 검색결과 페이지네이션: span.totalPage 읽고, #srchRsltPagingNum 값을 늘려 .btn-jump 클릭
"""

import re
import time
import pandas as pd
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # (필요 시)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
)

# =========================
# 1) 엑셀 유틸
# =========================

HARD_REQUIRED = {"AP", "AN", "IPC"}  # ✔ 필수 컬럼

def _normalize_col(name: str) -> str:
    if name is None:
        return ""
    s = str(name)
    s = s.replace("\ufeff", "")
    s = re.sub(r"[\r\n\t]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.upper()

def _find_header_row(df_preview: pd.DataFrame, needed=HARD_REQUIRED, scan_rows=10) -> int:
    limit = min(scan_rows, len(df_preview))
    for r in range(limit):
        row = df_preview.iloc[r].astype(str).fillna("")
        normed = [_normalize_col(c) for c in row.tolist()]
        if needed.issubset(set(normed)):
            return r
    return 0

def read_excel_safely(path: str, sheet="Sheet1") -> pd.DataFrame:
    preview = pd.read_excel(path, sheet_name=sheet, header=None, nrows=10, dtype=str, engine="openpyxl")
    header_row = _find_header_row(preview)
    df = pd.read_excel(path, sheet_name=sheet, header=header_row, dtype=str, engine="openpyxl")
    normalized = {col: _normalize_col(col) for col in df.columns}
    df.rename(columns=normalized, inplace=True)

    # 흔한 alias → 표준화
    alias = {
        "NO": "AN",
        "APP_NO": "AN",
        "APPLICATION_NO": "AN",
        "AP_NO": "AN",
        "APNO": "AN",
        "IPC CODE": "IPC",
        "IPCCODE": "IPC",
        "IPC_CODE": "IPC",
    }
    for col in list(df.columns):
        target = alias.get(col)
        if target and target != col:
            df.rename(columns={col: target}, inplace=True)

    missing = HARD_REQUIRED - set(df.columns)
    if missing:
        print("📄 감지된 컬럼:", list(df.columns))
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")
    return df

# =========================
# 2) 데이터 모델
# =========================

@dataclass
class PatentDetail:
    ap: str
    an: str
    ipc: str
    def __init__(self, ap, an, ipc):
        self.ap  = ("" if pd.isna(ap)  else str(ap)).strip()
        self.an  = ("" if pd.isna(an)  else str(an)).strip()
        self.ipc = ("" if pd.isna(ipc) else str(ipc)).strip()

# =========================
# 3) Selenium 유틸
# =========================

def _wait_click(driver, locator, timeout=10):
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()

def _wait_send_keys(driver, locator, text, timeout=10, clear_first=True):
    el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
    if clear_first:
        try:
            el.clear()
        except Exception:
            el.send_keys(Keys.CONTROL, "a")
    el.send_keys(text)

# === 신규 === 결과 페이지에서 총 페이지 수 읽기
def _get_total_pages(driver, timeout=10) -> int:
    """
    <span class="totalPage">5</span> 값을 읽어 정수로 반환.
    없거나 파싱 실패 시 1 반환.
    """
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.totalPage"))
        )
        txt = (el.text or "").strip()
        total = int(re.sub(r"[^\d]", "", txt)) if txt else 1
        return total if total >= 1 else 1
    except TimeoutException:
        return 1
    except Exception:
        return 1

# === 신규 === 특정 페이지로 점프
def _jump_to_page(driver, page_no: int, wait_after=2.0, timeout=10):
    """
    #srchRsltPagingNum value를 page_no로 설정 후 .btn-jump 클릭 → 이동 대기
    """
    # 입력창/버튼 찾기
    input_locator = (By.CSS_SELECTOR, 'input#srchRsltPagingNum.paginationNum')
    btn_locator   = (By.CSS_SELECTOR, 'button.btn-jump')

    # 현재 페이지 값을 읽어둠(대기 조건에 활용)
    try:
        current_val = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(input_locator)
        ).get_attribute("value")
    except TimeoutException:
        current_val = None

    # 값 설정: JS로 value 변경 및 input/change 이벤트 디스패치
    def _set_value_js(_driver, value: int):
        _driver.execute_script("""
            const el = document.querySelector('input#srchRsltPagingNum.paginationNum');
            if (el) {
                el.value = arguments[0].toString();
                el.dispatchEvent(new Event('input', {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
            }
        """, value)

    _set_value_js(driver, page_no)

    # 점프 버튼 클릭
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(btn_locator)).click()

    # 페이지 이동 대기: 입력값이 목표값이 될 때까지 + 약간의 안정화 슬립
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(*input_locator).get_attribute("value") == str(page_no)
        )
    except Exception:
        # 일부 사이트는 입력값 유지 안 될 수 있음 → 결과 변화만 간격 슬립으로 대체
        pass

    time.sleep(wait_after)  # 간단 안정화 대기(필요시 결과 리스트 기준으로 명시적 대기로 교체)

# === 신규 === 페이지네이션 전체 순회
def paginate_results(driver, max_pages: int | None = None, wait_after_jump: float = 2.0):
    """
    검색 결과에서 1페이지를 기준으로 2..N 페이지까지 순회.
    - max_pages 지정 시 그 수만큼만 순회(예: 5면 최대 5페이지까지만)
    - 사이트의 totalPage가 더 작으면 그 값에 맞춰 자동 제한
    """
    total = _get_total_pages(driver, timeout=10)
    if total <= 1:
        return  # 더 갈 페이지 없음

    if max_pages is not None:
        total = min(total, max_pages)

    # 현재는 1페이지에 있다고 가정 → 2..total 로 이동
    for p in range(2, total + 1):
        try:
            print(f"📄 페이지 이동: {p}/{total}")
            _jump_to_page(driver, p, wait_after=wait_after_jump, timeout=10)
        except (TimeoutException, StaleElementReferenceException):
            print(f"⚠️ 페이지 {p} 이동 실패 → 재시도")
            try:
                _jump_to_page(driver, p, wait_after=wait_after_jump, timeout=10)
                print(f"📄 페이지 이동(재시도 성공): {p}/{total}")
            except Exception as e:
                print(f"❌ 페이지 {p} 이동 실패: {e}")
                # 계속 진행 (필요 시 break로 중단 가능)
                continue

# =========================
# 4) KIPRIS 검색
# =========================

def search_patents(detail_list):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.kipris.or.kr/khome/main.do")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "btnOpenSearchDetail"))
            )
        except TimeoutException:
            print("⚠️ 메인 페이지 요소 대기 타임아웃: btnOpenSearchDetail")
            time.sleep(2)

        for num, patent in enumerate(detail_list, start=1):
            print(f"🔍 상세검색 {num}: AP={patent.ap}, AN={patent.an}, IPC={patent.ipc}")

            # 상세검색 열기
            try:
                _wait_click(driver, (By.ID, "btnOpenSearchDetail"), timeout=10)
            except TimeoutException:
                print("⚠️ 상세검색 버튼 클릭 실패(타임아웃). 페이지 새로고침 시도.")
                driver.get("https://www.kipris.or.kr/khome/main.do")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "btnOpenSearchDetail"))
                )
                _wait_click(driver, (By.ID, "btnOpenSearchDetail"), timeout=10)

            # 상세검색 필드 로딩 대기
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-field="IPC"]'))
                )
            except TimeoutException:
                print("⚠️ 상세검색 필드 로딩 지연")
                time.sleep(1)

            # IPC
            try:
                _wait_send_keys(driver, (By.CSS_SELECTOR, 'input[data-field="IPC"]'), patent.ipc, timeout=10)
            except TimeoutException:
                print("❌ IPC 입력 실패")

            # AP
            try:
                _wait_send_keys(driver, (By.CSS_SELECTOR, 'input[data-field="AP"]'), patent.ap, timeout=10)
            except TimeoutException:
                print("❌ AP 입력 실패")

            # AN: 필드가 있으면 입력
            try:
                an_input_locator = (By.CSS_SELECTOR, 'input[data-field="AN"]')
                WebDriverWait(driver, 2).until(EC.presence_of_element_located(an_input_locator))
                _wait_send_keys(driver, an_input_locator, patent.an, timeout=10)
            except TimeoutException:
                pass  # 필드 없음 → 스킵

            # 검색 버튼
            try:
                _wait_click(driver, (By.CSS_SELECTOR, 'button.btn-search[data-lang-id="adsr.search"]'), timeout=10)
            except TimeoutException:
                print("❌ 검색 버튼 클릭 실패")
            except ElementClickInterceptedException:
                print("⚠️ 다른 요소가 가려 클릭 실패 → 한번 더 시도")
                time.sleep(0.5)
                _wait_click(driver, (By.CSS_SELECTOR, 'button.btn-search[data-lang-id="adsr.search"]'), timeout=10)

            # === 신규 === 페이지네이션 수행 (예: 최대 5페이지까지만 순회)
            #  - 사이트 totalPage가 5보다 작으면 그만큼만 이동
            #  - 더 많이 보고 싶으면 max_pages=None 로 전체 이동
            try:
                # 결과가 뜰 시간을 조금 부여
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.totalPage"))
                )
            except TimeoutException:
                # totalPage가 늦게 뜨는 경우도 있으니 약간 여유
                time.sleep(2)

            # paginate_results(driver, max_pages=5, wait_after_jump=2.0)
            paginate_results(driver, max_pages=None, wait_after_jump=2.0)

            # 다음 특허로 넘어가기 위해 메인으로 복귀
            driver.get("https://www.kipris.or.kr/khome/main.do")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "btnOpenSearchDetail"))
                )
            except TimeoutException:
                print("⚠️ 메인 복귀 후 상세검색 버튼 대기 실패")

        input("✅ 전체 검색/페이지 순회 완료. 브라우저 닫으려면 Enter를 누르세요.")

    finally:
        driver.quit()

# =========================
# 5) main
# =========================

def main():
    excel_path = "../../data_new_20251022_1.xlsx"
    sheet_name = "Sheet1"

    try:
        df1 = read_excel_safely(excel_path, sheet=sheet_name)
    except Exception as e:
        print(f"❌ 엑셀 로딩 실패: {e}")
        return

    print("📄 정규화된 컬럼:", list(df1.columns))

    for col in ["AP", "AN", "IPC"]:
        df1[col] = df1[col].astype(str).str.strip()
    df1 = df1.replace({"": pd.NA}).dropna(subset=["AP", "AN", "IPC"])

    detail_list = [PatentDetail(row["AP"], row["AN"], row["IPC"]) for _, row in df1.iterrows()]
    if not detail_list:
        print("❌ Sheet1에 유효한 데이터가 없습니다.")
        return

    search_patents(detail_list)

if __name__ == "__main__":
    main()
