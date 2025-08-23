import json
import math
import threading
import time
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime
import re

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
from bs4 import BeautifulSoup
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
from typing import List, TypedDict, Literal
from src.utils.number_utils import to_int_digits
from src.utils.str_utils import str_clean




import random

class Transaction(TypedDict):
    type: Literal["입금", "출금"]
    name: str
    date: int  # unix timestamp
    real_date: str           # 👈 추가
    balanceAfterTransaction: int
    amount: int
    id: str  # 거래점에서 숫자만 추출


class ApiNhBankSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()
        self.base_main_url   = "https://banking.nonghyup.com/servlet/IPCNPA000I.view"

        self.excludeKeywords = ""
        self.includeKeyword = ""

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.sess = None
        self.running = True
        self.driver = None
        self.base_url = None
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)


    def init(self):

        self.log_signal_func("크롤링 시작 ========================================")

        self.driver_set()

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.base_main_url)


    # 프로그램 실행
    def main(self):
        self.wait_for_user_confirmation()
        self.loop_poll()


    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 드라이버 객체 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 엑셀 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless=False)

        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)


    def wait_for_user_confirmation(self):
        self.log_signal_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")

        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("로그인 -> 거래내역 이동 -> 로딩이 끝난 후 OK를 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        time.sleep(2)  # 예제용


    def loop_poll(self):
        while True:
            try:
                self.set_date_to_today()
                self.click_inquiry()
                time.sleep(2)  # 로딩 대기
                data = self.parse_table()
                #self.log_signal_func(json.dumps(data, ensure_ascii=False, indent=2))
                self.log_signal_func(f"data : {data}")
            except Exception as e:
                self.log_signal_func(f"⚠ 오류: {e}")
            time.sleep(5)


    def set_date_to_today(self):
        """조회기간 select → 오늘 날짜로 갱신"""
        now = datetime.now()
        y, m, d = str(now.year), f"{now.month:02d}", f"{now.day:02d}"

        Select(self.driver.find_element(By.ID, "start_year")).select_by_value(y)
        Select(self.driver.find_element(By.ID, "start_month")).select_by_value(m)
        Select(self.driver.find_element(By.ID, "start_date")).select_by_value(d)

        Select(self.driver.find_element(By.ID, "end_year")).select_by_value(y)
        Select(self.driver.find_element(By.ID, "end_month")).select_by_value(m)
        Select(self.driver.find_element(By.ID, "end_date")).select_by_value(d)


    def click_inquiry(self):
        """조회 버튼 클릭"""
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[normalize-space()='조회' and contains(@onclick,'lfSubmitSearch')]")
        )).click()

    def extract_txid(self, branch_text: str) -> str:
        """'토스뱅크 \\n0921008' -> '0921008'"""
        m = re.search(r"(\d+)", branch_text or "")
        return m.group(1) if m else ""


    # -------------------------
    # 테이블 파싱
    # -------------------------
    def parse_table(self) -> List[Transaction]:
        """거래내역 테이블 파싱 → Transaction 리스트"""
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#listTable tbody")))
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#listTable tbody tr")

        result: List[Transaction] = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 9:
                continue

            when_txt     = str_clean(cols[1].text)  # 거래일시
            withdraw_txt = str_clean(cols[2].text)  # 출금금액
            deposit_txt  = str_clean(cols[3].text)  # 입금금액
            balance_txt  = str_clean(cols[4].text)  # 잔액
            record_txt   = str_clean(cols[6].text)  # 거래기록사항
            branch_txt   = str_clean(cols[7].text)  # 거래점

            withdraw = to_int_digits(withdraw_txt)
            deposit  = to_int_digits(deposit_txt)
            balance  = to_int_digits(balance_txt)

            if deposit > 0:
                tx_type = "입금"
                amount = deposit
            elif withdraw > 0:
                tx_type = "출금"
                amount = withdraw
            else:
                continue

            seq_txt = str_clean(cols[0].text)   # 순번 (1,2,3,...)
            seq_num = re.sub(r"\D", "", seq_txt) or "0"  # 숫자만 추출, 없으면 "0"

            ts   = parse_timestamp(when_txt)
            real_date = format_real_date(ts) if ts > 0 else ""
            branch_id = self.extract_txid(branch_txt)

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


    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
