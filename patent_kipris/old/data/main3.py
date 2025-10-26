# -*- coding: utf-8 -*-
"""
KIPRIS 상세검색 자동화 (AP / AN / IPC + 페이지네이션)
- 엑셀 Sheet1 에서 AP/AN/IPC 컬럼 자동 인식(헤더 탐지 + 정규화)
- Selenium으로 상세검색 수행
- # === 신규 === 검색결과 페이지네이션: span.totalPage 읽고, #srchRsltPagingNum 값을 설정 후 .btn-jump 동작
- # === 변경 === 메인 검색창(#inputQuery)에 단일 문자열(AN/IPC/AP/TRH)로 검색
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
            el.send_keys(Keys.DELETE)
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

# === 신규 === 특정 페이지로 점프 (스크롤 없이 JS 우선, 실패 시 클릭 대체)
def _jump_to_page(driver, page_no: int, wait_after=2.0, timeout=10):
    """
    #srchRsltPagingNum value를 page_no로 설정 후 이동.
    1) goJumpPage(btn)이 전역에 있으면 직접 호출
    2) 없으면 .btn-jump 클릭 (필요 시 scrollIntoView)
    """
    input_sel = '#srchRsltPagingNum.paginationNum'
    btn_sel   = 'button.btn-jump'

    # 값 설정 + goJumpPage 호출 시도
    driver.execute_script(f"""
        const input = document.querySelector('{input_sel}');
        const btn   = document.querySelector('{btn_sel}');
        if (input) {{
            input.value = '{page_no}';
            input.dispatchEvent(new Event('input', {{bubbles:true}}));
            input.dispatchEvent(new Event('change', {{bubbles:true}}));
        }}
        if (typeof window.goJumpPage === 'function' && btn) {{
            window.goJumpPage(btn);
        }} else if (btn) {{
            btn.scrollIntoView({{block:'center'}});
            btn.click();
        }}
    """)

    # 페이지 이동 안정화
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.CSS_SELECTOR, input_sel).get_attribute("value") == str(page_no)
        )
    except Exception:
        pass
    time.sleep(wait_after)

# === 신규 === 페이지네이션 전체 순회 (함수 진입 즉시 스크롤)
def paginate_results(driver, max_pages: int | None = None, wait_after_jump: float = 2.0):
    """
    검색 결과에서 1페이지를 기준으로 2..N 페이지까지 순회.
    - max_pages 지정 시 그 수만큼만 순회(예: 5면 최대 5페이지까지만)
    - 사이트의 totalPage가 더 작으면 그 값에 맞춰 자동 제한
    - === 신규: 함수 진입 즉시 스크롤 맨 아래로 이동해 페이징 영역 노출
    """
    # === 신규 === 진입 시 바로 스크롤 (페이징 컨트롤 노출)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

    total = _get_total_pages(driver, timeout=10)
    if total <= 1:
        return  # 더 갈 페이지 없음

    if max_pages is not None:
        total = min(total, max_pages)

    # ✅ 최초 1/N 로그
    print(f"📄 페이지 이동: 1/{total}")

    # 현재는 1페이지에 있다고 가정 → 2..total 로 이동
    for p in range(2, total + 1):
        try:
            print(f"📄 페이지 이동: {p}/{total}")
            _jump_to_page(driver, p, wait_after=wait_after_jump, timeout=10)
            time.sleep(1.5)
        except (TimeoutException, StaleElementReferenceException):
            print(f"⚠️ 페이지 {p} 이동 실패 → 재시도")
            try:
                _jump_to_page(driver, p, wait_after=wait_after_jump, timeout=10)
                print(f"📄 페이지 이동(재시도 성공): {p}/{total}")
            except Exception as e:
                print(f"❌ 페이지 {p} 이동 실패: {e}")
                continue

# =========================
# 4) KIPRIS 검색
# =========================

# === 신규 === KIPRIS 메인 검색어 문자열 빌더 (AN / IPC / AP / TRH)
def build_kipris_query(an: str, ipc: str, ap: str) -> str:
    """
    예) AN=[2002]*IPC=[G06F]*AP=[삼성전자주식회사]*TRH=[삼성전자주식회사]
    - 빈 값은 자동 생략
    - TRH는 별도 입력이 없으므로 AP 값과 동일하게 사용(요청 예시 준수)
    """
    parts = []
    def bracket(v: str) -> str:
        # ']' 문자가 값에 있을 경우 최소한의 이스케이프 (대괄호 깨짐 방지)
        return "[" + v.replace("]", "\\]") + "]"

    if an:
        parts.append(f"AN={bracket(an)}")
    if ipc:
        parts.append(f"IPC={bracket(ipc)}")
    if ap:
        parts.append(f"AP={bracket(ap)}")
        # === 신규 === TRH도 AP와 동일하게 구성
        parts.append(f"TRH={bracket(ap)}")

    return "*".join(parts)

# === 변경 ===: 상세검색 팝업을 쓰지 않고 메인 검색창(#inputQuery)에 단일 쿼리 입력
def search_patents(detail_list):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.kipris.or.kr/khome/main.do")

        # 메인 검색창 준비
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "inputQuery"))
            )
        except TimeoutException:
            print("⚠️ 메인 페이지 로딩 지연: inputQuery 탐지 실패")
            time.sleep(1.5)

        for num, patent in enumerate(detail_list, start=1):
            # 각 건은 에러가 나도 다음으로 넘어가도록 전체 try 보호
            try:
                q = build_kipris_query(patent.an, patent.ipc, patent.ap)
                print(f"🔍 상세검색 {num}: AP={patent.ap}, AN={patent.an}, IPC={patent.ipc}")
                print(f"   ➤ 쿼리: {q}")

                # 1) 검색어 입력
                try:
                    _wait_send_keys(driver, (By.ID, "inputQuery"), q, timeout=10, clear_first=True)
                    time.sleep(0.2)
                except TimeoutException:
                    print("❌ inputQuery 입력 실패")
                    continue  # 이 건 스킵

                # 2) 검색 실행
                #   - 우선 commonly used 버튼들을 시도하고, 실패 시 Enter로 대체
                executed = False
                for locator in [
                    (By.CSS_SELECTOR, 'button.btn-search[data-lang-id="btn.search"]'),
                    (By.ID, "btnMainSearch"),
                    (By.CSS_SELECTOR, "button.btn-search"),
                ]:
                    try:
                        _wait_click(driver, locator, timeout=3)
                        executed = True
                        break
                    except Exception:
                        pass
                if not executed:
                    # Enter key 대체
                    try:
                        el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "inputQuery")))
                        el.send_keys(Keys.ENTER)
                        executed = True
                    except Exception:
                        executed = False

                if not executed:
                    print("❌ 검색 실행 실패(버튼/Enter)")
                    continue  # 이 건 스킵

                # === 신규 === 검색 후 resultSection(or 결과 텍스트) 대기
                time.sleep(1.2)
                try:
                    # 결과 페이지로 전환되며 '건이 검색되었습니다.' 텍스트 데이터-속성이 종종 등장
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-lang-id="srlt.txt20"]'))
                    )
                    print("✅ 검색 결과 텍스트 로드 완료: 건이 검색되었습니다.")
                except TimeoutException:
                    print("⚠️ 결과 텍스트 미탐지 → 계속 진행")

                # === 신규 === totalPage 끝까지 페이지네이션 수행
                try:
                    # 1️⃣ 먼저 페이지 맨 아래로 스크롤
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.8)  # 스크롤 후 약간 대기 (렌더링 여유)

                    # 2️⃣ totalPage 요소 대기(없어도 paginate_results에서 1로 처리)
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.totalPage"))
                        )
                        print("✅ totalPage 요소 탐지 완료")
                    except TimeoutException:
                        print("ℹ️ totalPage 즉시 미탐지 (단건 결과/1페이지일 수 있음)")

                    paginate_results(driver, max_pages=None, wait_after_jump=2.0)
                except Exception as e:
                    print(f"⚠️ 페이지네이션 중 예외 발생: {e}")

                # 다음 특허로 넘어가기 위해 메인으로 복귀
                try:
                    driver.get("https://www.kipris.or.kr/khome/main.do")
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "inputQuery"))
                    )
                except TimeoutException:
                    print("⚠️ 메인 복귀 후 inputQuery 대기 실패")
                    # 그래도 다음 루프 계속

            except Exception as e:
                # 건 단위 최종 보호막: 어떤 예외든 현재 건은 스킵하고 다음으로
                print(f"❌ 상세검색 {num} 처리 중 예외: {e}")
                try:
                    # 다음 건을 위해 메인 복귀 시도
                    driver.get("https://www.kipris.or.kr/khome/main.do")
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "inputQuery"))
                    )
                except Exception:
                    pass
                continue

        try:
            input("✅ 전체 검색/페이지 순회 완료. 브라우저 닫으려면 Enter를 누르세요.")
        except Exception:
            # 비상호작용 환경(예: CI) 대비
            pass

    finally:
        try:
            driver.quit()
        except Exception:
            pass

# =========================
# 5) main
# =========================

def main():
    excel_path = "../../data_new_20251022_1.xlsx"  # ← 요청하신 파일명 반영
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
