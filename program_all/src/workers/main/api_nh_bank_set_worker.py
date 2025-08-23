# -*- coding: utf-8 -*-
import threading
import time
from datetime import datetime, timedelta
import re
from typing import List, TypedDict, Literal, Optional

import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.utils.time_utils import parse_timestamp, format_real_date
from src.workers.api_base_worker import BaseApiWorker
from src.utils.number_utils import to_int_digits
from src.utils.str_utils import str_clean

from src.db.nh_bank.nh_bank_repository import NhBankTxRepository
from src.api.nh_bank_app import create_app
from src.api.embedded_api_server import EmbeddedApiServer

class Transaction(TypedDict):
    type: Literal["입금", "출금"]
    name: str
    date: int              # unix timestamp
    real_date: str         # YYYY-MM-DD HH:mm:ss
    balanceAfterTransaction: int
    amount: int
    id: str                # "{in|ex}_{branchId}_{timestamp}"

class ApiNhBankSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.base_main_url = "https://banking.nonghyup.com/servlet/IPCNPA000I.view"

        self.excludeKeywords = ""
        self.includeKeyword  = ""
        self.running = True
        self.driver = None

        self.before_pro_value = 0

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.api_client = APIClient(use_cache=False)

        # Repo & API
        self.tx_repo = NhBankTxRepository()
        self.api_host = "0.0.0.0"
        self.api_port = 8088
        self.api_key  = "nh_bank"
        self._api_server: Optional[EmbeddedApiServer] = None

    def init(self):
        self.log_signal_func("크롤링 시작 ========================================")
        self._driver_set()

        # 반쪽 창
        sw, sh = pyautogui.size()
        self.driver.set_window_size(sw // 2, sh)
        self.driver.set_window_position(0, 0)
        self.driver.get(self.base_main_url)

        # 내장 API 서버 기동
        try:
            app = create_app(self.tx_repo, self.api_key)
            self._api_server = EmbeddedApiServer(app, host=self.api_host, port=self.api_port, log_level="warning")
            self._api_server.start()
            self.log_signal_func(f"API 서버: http://{self.api_host}:{self.api_port}/nhbank  (X-API-Key 필요)")
            return True
        except Exception as e:
            self.log_signal_func(f"⚠ API 서버 시작 실패: {e}")
            return False

    def main(self):
        self._wait_for_user_confirmation()
        self._loop_poll()

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")

        try:
            if self._api_server:
                self._api_server.stop()
                self.log_signal_func("API 서버 종료 완료")
        except Exception as e:
            self.log_signal_func(f"⚠ API 서버 종료 중 예외: {e}")

        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass

        self.tx_repo.close()
        time.sleep(1)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # ------------ internals ------------
    def _driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless=False)
        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)

    def _wait_for_user_confirmation(self):
        self.log_signal_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
        event = threading.Event()
        self.msg_signal.emit("로그인 -> 거래내역 이동 -> 로딩이 끝난 후 OK를 눌러주세요", "info", event)
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()
        self.log_signal_func("✅ 사용자 확인 완료")
        time.sleep(1)

    def _loop_poll(self):
        while True:
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            try:
                self._set_date_range()
                self._click_inquiry()
                time.sleep(2)  # 로딩 대기
                data = self._parse_table()
                data = self._filter_by_keywords(data)

                #self.log_signal_func(f"data: {data}")

                # ★ UPSERT 저장 (신규 INSERT, 기존 UPDATE)
                changed = self.tx_repo.upsert_many(data)
                self.log_signal_func(f"저장(UPSERT): {changed}건 / 파싱 {len(data)}건")

            except Exception as e:
                self.log_signal_func(f"⚠ 오류: {e}")
            time.sleep(5)

    def _set_date_to_today(self):
        now = datetime.now()
        y, m, d = str(now.year), f"{now.month:02d}", f"{now.day:02d}"
        Select(self.driver.find_element(By.ID, "start_year")).select_by_value(y)
        Select(self.driver.find_element(By.ID, "start_month")).select_by_value(m)
        Select(self.driver.find_element(By.ID, "start_date")).select_by_value(d)
        Select(self.driver.find_element(By.ID, "end_year")).select_by_value(y)
        Select(self.driver.find_element(By.ID, "end_month")).select_by_value(m)
        Select(self.driver.find_element(By.ID, "end_date")).select_by_value(d)

    def _set_date_range(self):
        today = datetime.now()
        start = today - timedelta(days=3)

        y_end, m_end, d_end = str(today.year), f"{today.month:02d}", f"{today.day:02d}"
        y_start, m_start, d_start = str(start.year), f"{start.month:02d}", f"{start.day:02d}"

        # start = 3일 전
        Select(self.driver.find_element(By.ID, "start_year")).select_by_value(y_start)
        Select(self.driver.find_element(By.ID, "start_month")).select_by_value(m_start)
        Select(self.driver.find_element(By.ID, "start_date")).select_by_value(d_start)

        # end = 오늘
        Select(self.driver.find_element(By.ID, "end_year")).select_by_value(y_end)
        Select(self.driver.find_element(By.ID, "end_month")).select_by_value(m_end)
        Select(self.driver.find_element(By.ID, "end_date")).select_by_value(d_end)



    def _click_inquiry(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[normalize-space()='조회' and contains(@onclick,'lfSubmitSearch')]")
        )).click()

    def _extract_txid(self, branch_text: str) -> str:
        m = re.search(r"(\d+)", branch_text or "")
        return m.group(1) if m else ""

    def _parse_table(self) -> List[Transaction]:
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#listTable tbody")))
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#listTable tbody tr")
        result: List[Transaction] = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 9:
                continue

            when_txt     = str_clean(cols[1].text)
            withdraw_txt = str_clean(cols[2].text)
            deposit_txt  = str_clean(cols[3].text)
            balance_txt  = str_clean(cols[4].text)
            record_txt   = str_clean(cols[6].text)
            branch_txt   = str_clean(cols[7].text)

            withdraw = to_int_digits(withdraw_txt)
            deposit  = to_int_digits(deposit_txt)
            balance  = to_int_digits(balance_txt)

            if deposit > 0:
                tx_type = "입금"; amount = deposit
            elif withdraw > 0:
                tx_type = "출금"; amount = withdraw
            else:
                continue

            ts = parse_timestamp(when_txt)
            real_date = format_real_date(ts) if ts > 0 else ""
            branch_id = self._extract_txid(branch_txt)

            type_code = "in" if tx_type == "입금" else "ex"
            txid = f"{type_code}_{branch_id}_{ts}"

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

    def _filter_by_keywords(self, items: List[Transaction]) -> List[Transaction]:
        inc = (self.includeKeyword or "").strip().lower()
        exc = (self.excludeKeywords or "").strip().lower()

        def ok(t: Transaction) -> bool:
            nm = (t["name"] or "").lower()
            if inc and inc not in nm:
                return False
            if exc and exc in nm:
                return False
            return True

        return [t for t in items if ok(t)]

    def stop(self):
        self.running = False
