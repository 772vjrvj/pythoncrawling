# nh_account_poll_and_parse.py
import re
import time
import json
import signal
from datetime import datetime
from typing import List, TypedDict, Literal
from zoneinfo import ZoneInfo


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

NH_MAIN = "https://banking.nonghyup.com/nhbank.html"

class Transaction(TypedDict):
    type: Literal["입금", "출금"]
    name: str
    date: int  # unix timestamp
    real_date: str           # 👈 추가
    balanceAfterTransaction: int
    amount: int
    id: str  # 거래점에서 숫자만 추출

# -------------------------
# 드라이버 초기화
# -------------------------
def build_driver(browser: str = "chrome", headless: bool = False):
    """Chrome/Edge 실행"""
    if browser == "edge":
        from selenium.webdriver.edge.options import Options as EdgeOptions
        opts = EdgeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--start-maximized")
        opts.add_argument("--lang=ko-KR")
        driver = webdriver.Edge(options=opts)
    else:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--start-maximized")
        opts.add_argument("--lang=ko-KR")
        # 자동화 티 줄이기
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Chrome(options=opts)

    driver.set_page_load_timeout(60)
    driver.implicitly_wait(0)
    return driver

# -------------------------
# 액션
# -------------------------
def click_login(driver):
    """메인 → 로그인 버튼 클릭"""
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.ID, "header_login")))
    candidates = [
        (By.XPATH, "//span[normalize-space()='로그인']/parent::a"),
        (By.CSS_SELECTOR, "#header_login a[data-tap^=\"navigate('/servlet/IPCNPA000I')\"]"),
        (By.XPATH, "//*[@id='header_login']//a[.//span[normalize-space()='로그인']]"),
        (By.LINK_TEXT, "로그인"),
    ]
    for by, sel in candidates:
        try:
            el = wait.until(EC.element_to_be_clickable((by, sel)))
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            continue
    return False

def set_date_to_today(driver):
    """조회기간 select → 오늘 날짜로 갱신"""
    now = datetime.now()
    y, m, d = str(now.year), f"{now.month:02d}", f"{now.day:02d}"

    Select(driver.find_element(By.ID, "start_year")).select_by_value(y)
    Select(driver.find_element(By.ID, "start_month")).select_by_value(m)
    Select(driver.find_element(By.ID, "start_date")).select_by_value(d)

    Select(driver.find_element(By.ID, "end_year")).select_by_value(y)
    Select(driver.find_element(By.ID, "end_month")).select_by_value(m)
    Select(driver.find_element(By.ID, "end_date")).select_by_value(d)

def click_inquiry(driver):
    """조회 버튼 클릭"""
    wait = WebDriverWait(driver, 10)
    el = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[normalize-space()='조회' and contains(@onclick,'lfSubmitSearch')]")
    ))
    el.click()

# -------------------------
# 파싱 헬퍼
# -------------------------
def _clean(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()

def _to_int_digits(s: str) -> int:
    """'1,234원' -> 1234"""
    if not s:
        return 0
    nums = re.findall(r"\d+", s)
    return int("".join(nums)) if nums else 0

def _parse_timestamp(ymd_hms_text: str) -> int:
    """'YYYY/MM/DD \\nHH:MM:SS' -> epoch seconds"""
    t = _clean(ymd_hms_text).replace("\n", " ").replace("  ", " ")
    parts = t.split()
    if len(parts) >= 2:
        ymd, hms = parts[0], parts[1]
    else:
        return 0
    try:
        dt = datetime.strptime(f"{ymd} {hms}", "%Y/%m/%d %H:%M:%S")
        return int(dt.timestamp())
    except Exception:
        return 0

def _extract_txid(branch_text: str) -> str:
    """'토스뱅크 \\n0921008' -> '0921008'"""
    m = re.search(r"(\d+)", branch_text or "")
    return m.group(1) if m else ""

# -------------------------
# 테이블 파싱
# -------------------------
def parse_table(driver) -> List[Transaction]:
    """거래내역 테이블 파싱 → Transaction 리스트"""
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#listTable tbody")))
    rows = driver.find_elements(By.CSS_SELECTOR, "#listTable tbody tr")

    result: List[Transaction] = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 9:
            continue

        when_txt     = _clean(cols[1].text)  # 거래일시
        withdraw_txt = _clean(cols[2].text)  # 출금금액
        deposit_txt  = _clean(cols[3].text)  # 입금금액
        balance_txt  = _clean(cols[4].text)  # 잔액
        record_txt   = _clean(cols[6].text)  # 거래기록사항
        branch_txt   = _clean(cols[7].text)  # 거래점

        withdraw = _to_int_digits(withdraw_txt)
        deposit  = _to_int_digits(deposit_txt)
        balance  = _to_int_digits(balance_txt)

        if deposit > 0:
            tx_type = "입금"
            amount = deposit
        elif withdraw > 0:
            tx_type = "출금"
            amount = withdraw
        else:
            continue

        seq_txt = _clean(cols[0].text)   # 순번 (1,2,3,...)
        seq_num = re.sub(r"\D", "", seq_txt) or "0"  # 숫자만 추출, 없으면 "0"

        ts   = _parse_timestamp(when_txt)
        real_date = datetime.fromtimestamp(ts, ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S") if ts > 0 else ""
        branch_id = _extract_txid(branch_txt)

        type_code = "in" if tx_type == "입금" else "ex"
        txid = f"{type_code}_{branch_id}_{ts}_{seq_num}"


        result.append(Transaction(
            type=tx_type,
            name=record_txt,
            date=ts,
            real_date=real_date,
            balanceAfterTransaction=balance,
            amount=amount,
            id=txid,
        ))
    return result

# -------------------------
# 루프
# -------------------------
def loop_poll(driver, interval=5):
    """interval초마다: 날짜 갱신 → 조회 → 테이블 파싱 → JSON print"""
    print(f"⏳ {interval}초 주기로 조회 시작 (Ctrl+C 종료)")
    try:
        signal.signal(signal.SIGINT, signal.default_int_handler)
    except Exception:
        pass

    while True:
        try:
            set_date_to_today(driver)
            click_inquiry(driver)
            time.sleep(2)  # 로딩 대기

            data = parse_table(driver)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except KeyboardInterrupt:
            print("🛑 중단")
            break
        except Exception as e:
            print("⚠ 오류:", e)

        time.sleep(interval)

# -------------------------
# 메인
# -------------------------
def main():
    driver = build_driver(browser="chrome", headless=False)
    try:
        driver.get(NH_MAIN)
        click_login(driver)
        print("✅ 로그인 페이지 이동 완료")
        input("👉 로그인/계좌내역 들어가면 엔터...")

        loop_poll(driver, interval=5)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
