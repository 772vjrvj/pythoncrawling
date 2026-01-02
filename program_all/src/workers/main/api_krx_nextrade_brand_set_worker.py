# ============================================
# ./src/workers/api_krx_nextrade_set_load_worker.py
# ============================================
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import time
import datetime
import random
import json
import threading
import pyautogui

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.number_utils import to_int, to_float
from src.utils.selenium_utils import SeleniumUtils


class ApiKrxNextradeSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.api_client = APIClient(use_cache=False)

        # =========================
        # output
        # =========================
        # === 자동 리포트는 항상 누적 ===
        self.output_xlsx_auto = "krx_nextrade.xlsx"
        self.output_xlsx = self.output_xlsx_auto

        self.running = True
        self.before_pro_value = 0
        self.last_auto_date = None

        self._last_keepalive = 0

        # =========================
        # KRX / NEXTRADE URL + REFERER
        # =========================
        self.krx_url = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        self.krx_referer = "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"
        self.krx_url_login = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd"


        self.nx_url = "https://www.nextrade.co.kr/brdinfoTime/brdinfoTimeList.do"
        self.nx_referer = "https://www.nextrade.co.kr/menu/transactionStatusMain/menuList.do"

        # =========================
        # headers
        # =========================
        self.krx_headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://data.krx.co.kr",
            "referer": self.krx_referer,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "x-requested-with": "XMLHttpRequest"
        }

        self.nx_headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.nextrade.co.kr",
            "referer": self.nx_referer,
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "x-requested-with": "XMLHttpRequest",
        }

    # =========================
    # init / main
    # =========================
    def init(self):
        self.driver_set(False)

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.krx_url_login)


        return True


    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)


        self.driver = self.selenium_driver.start_driver(1200)


    def main(self):
        try:

            self.wait_for_user_confirmation()

            fr_date = self.get_setting_value(self.setting, "fr_date")
            to_date = self.get_setting_value(self.setting, "to_date")

            self.log_signal_func(f"날짜 시작일 : {fr_date}")
            self.log_signal_func(f"날짜 종료일 : {to_date}")

            min_sum_uk = int(self.get_setting_value(self.setting, "price_sum"))
            min_rate = float(self.get_setting_value(self.setting, "rate"))

            # 억 -> 원(비교용)
            min_sum_won = min_sum_uk * 100000000

            self.log_signal_func(f"거래대금 이상(억) : {min_sum_uk}")
            self.log_signal_func(f"거래대금 이상(원) : {min_sum_won}")
            self.log_signal_func(f"등락률 이상(%) : {min_rate}")

            auto_yn = str(self.get_setting_value(self.setting, "auto_yn")).lower() in ("1", "true", "y")
            auto_time = str(self.get_setting_value(self.setting, "auto_time"))

            self.log_signal_func(f"자동 리포트 여부 : {auto_yn}")
            self.log_signal_func(f"자동 리포트 시간 : {auto_time}")

            if auto_yn:
                self.output_xlsx = self.output_xlsx_auto
                self.log_signal_func(f"[AUTO] 누적 저장 파일: {self.output_xlsx}")
                self.auto_loop(auto_time, min_rate, min_sum_won)
            else:
                self.output_xlsx = f"krx_nextrade_{fr_date}_{to_date}.xlsx"
                self.log_signal_func(f"[RUN] 저장 파일: {self.output_xlsx}")

                dates = self.make_dates(fr_date, to_date)
                all_rows = []

                self.log_signal_func(f"[RUN] 기간 처리 시작: {dates[0]} ~ {dates[-1]} (총 {len(dates)}일)")

                for idx, ymd in enumerate(dates, start=1):
                    if not self.running:
                        self.log_signal_func("[RUN] 중단 플래그 감지 → 루프 종료")
                        break

                    self.log_signal_func(f"[DAY {idx}/{len(dates)}] {ymd} 처리 시작")

                    rows = self.process_one_day(ymd, min_rate, min_sum_won)
                    all_rows.extend(rows)

                    self.log_signal_func(f"[DAY {idx}/{len(dates)}] {ymd} 완료 (조건 통과 {len(rows)}건)")

                    pro = (idx / len(dates)) * 1000000
                    self.progress_signal.emit(self.before_pro_value, pro)
                    self.before_pro_value = pro

                    # === 랜덤 슬립 (1~2초) ===
                    time.sleep(random.uniform(1, 2))

                self.log_signal_func(f"[RUN] 엑셀 저장 시작 (총 {len(all_rows)}건)")
                self.append_excel(all_rows)
                self.log_signal_func(f"[RUN] 엑셀 저장 완료: {self.output_xlsx}")

            return True

        except Exception as e:
            self.log_signal_func(f"❌ 오류: {e}")
            return False


    def wait_for_user_confirmation(self):
        self.log_signal_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")

        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("로그인 후  후 OK를 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 쿠키 설정
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        self.driver.get(self.krx_referer)

        time.sleep(2)  # 예제용

        self.log_signal_func("🚀 작업 완료!")


    # =========================
    # auto
    # =========================
    def auto_loop(self, auto_time, min_rate, min_sum_won):
        hour, minute = self.parse_auto_hour(auto_time)

        self.log_signal_func(f"[AUTO] 자동 리포트 시간: {hour:02d}:{minute:02d}")

        while self.running:
            try:

                # === 신규 === 10초마다 로그인 연장 버튼 클릭
                now_ts = time.time()
                if now_ts - self._last_keepalive >= 10:
                    self._last_keepalive = now_ts
                    try:
                        btn = self.driver.find_element("id", "jsExtendLoginBtn")
                        if btn.is_displayed():
                            btn.click()
                            self.log_signal_func("[KEEPALIVE] 로그인 연장 클릭")
                    except Exception:
                        pass

                now = datetime.datetime.now()
                today = now.strftime("%Y%m%d")

                if self.last_auto_date == today:
                    time.sleep(1)
                    continue

                if now.hour == hour and now.minute == minute:
                    try:
                        self.output_xlsx = self.output_xlsx_auto
                        self.log_signal_func(f"[AUTO] {today} 자동 리포트 실행 시작 (파일: {self.output_xlsx})")

                        rows = self.process_one_day(today, min_rate, min_sum_won)
                        self.append_excel(rows)

                        self.last_auto_date = today
                        self.log_signal_func(f"[AUTO] {today} 자동 리포트 완료 (저장 {len(rows)}건)")

                    except Exception as e:
                        self.log_signal_func(f"[AUTO] 실행 오류: {e}")

                    time.sleep(65)
                else:
                    time.sleep(1)

            except Exception as e:
                self.log_signal_func(f"[AUTO LOOP] 예외 발생: {e}")
                time.sleep(5)

    # =========================
    # core
    # =========================
    def process_one_day(self, ymd, min_rate, min_sum_won):
        self.log_signal_func(f"[{ymd}] 데이터 수집 시작 (KRX / NEXTRADE)")

        krx = self.fetch_krx(ymd)
        self.log_signal_func(f"[{ymd}] KRX 수신 완료 ({len(krx)}건)")

        nx = self.fetch_nextrade(ymd)
        self.log_signal_func(f"[{ymd}] NEXTRADE 수신 완료 ({len(nx)}건)")

        krx_map = {self.only_digits(r.get("ISU_SRT_CD")): r for r in krx}
        nx_map = {self.only_digits(r.get("isuSrdCd", "").replace("A", "")): r for r in nx}

        all_codes = set(krx_map.keys()) | set(nx_map.keys())
        self.log_signal_func(f"[{ymd}] 병합 대상 종목 수: {len(all_codes)}")

        merged = []

        for code in all_codes:
            k = krx_map.get(code)
            n = nx_map.get(code)

            trade_sum_won = (to_int(k.get("ACC_TRDVAL")) if k else 0) + (to_int(n.get("accTrval")) if n else 0)

            rate = to_float(k.get("FLUC_RT")) if k else None
            if rate is None and n:
                rate = to_float(n.get("upDownRate"))

            name = ""
            if n:
                name = n.get("isuAbwdNm", "")
            if not name and k:
                name = k.get("ISU_ABBRV", "")
            if not name:
                name = code

            merged.append({
                "날짜": ymd,
                "종목명": name,
                "거래대금합계_원": trade_sum_won,
                "등락률": rate
            })

        # 거래대금 내림차순 정렬(원 기준)
        merged.sort(key=lambda x: x.get("거래대금합계_원", 0), reverse=True)

        # 조건 필터 + 순위 부여
        rows = []
        rank = 1
        for m in merged:
            m["순위"] = rank
            rank += 1

            if m.get("등락률") is None:
                continue
            if m.get("거래대금합계_원", 0) < min_sum_won:
                continue
            if m.get("등락률", 0) < min_rate:
                continue

            # === rows 들어가기 전에 억 단위로 변환(8자리 버림) ===
            m["거래대금합계"] = str(int(m.get("거래대금합계_원", 0)) // 100000000)

            rows.append(self.map_columns(m))

        self.log_signal_func(f"[{ymd}] 조건 통과 종목 수: {len(rows)}")
        return rows

    # =========================
    # fetch
    # =========================
    def fetch_krx(self, ymd):
        payload = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "locale": "ko_KR",
            "mktId": "ALL",
            "trdDd": str(ymd),
            "share": "1",
            "money": "1",
            "csvxls_isNo": "false",
        }

        self.log_signal_func(f"[KRX {ymd}] POST 요청 시작")
        resp = self.api_client.post(self.krx_url, headers=self.krx_headers, data=payload)
        time.sleep(random.uniform(1, 2))

        data = json.loads(resp)
        out = data.get("OutBlock_1", [])
        self.log_signal_func(f"[KRX {ymd}] 응답 완료 (OutBlock_1={len(out)}건)")
        return out

    def fetch_nextrade(self, ymd):
        result = []
        page = 1
        total_cnt = 0

        while True:
            payload = {
                "_search": "false",
                "nd": str(int(time.time() * 1000)),
                "pageUnit": "1000",
                "pageIndex": str(page),
                "sidx": "",
                "sord": "asc",
                "scAggDd": str(ymd),
                "scMktId": "",
                "searchKeyword": "",
            }

            self.log_signal_func(f"[NEXTRADE {ymd}] page {page} 요청 시작")
            resp = self.api_client.post(self.nx_url, headers=self.nx_headers, data=payload)
            time.sleep(random.uniform(1, 2))

            data = json.loads(resp)
            items = data.get("brdinfoTimeList", [])

            self.log_signal_func(f"[NEXTRADE {ymd}] page {page} 수신 ({len(items)}건)")

            if not items:
                break

            if total_cnt == 0:
                try:
                    total_cnt = int(data.get("totalCnt", 0))
                except Exception:
                    total_cnt = 0
                self.log_signal_func(f"[NEXTRADE {ymd}] totalCnt={total_cnt}")

            result.extend(items)

            if total_cnt and len(result) >= total_cnt:
                break

            page += 1

        self.log_signal_func(f"[NEXTRADE {ymd}] 전체 수신 완료 (총 {len(result)}건)")
        return result

    # =========================
    # excel
    # =========================
    def append_excel(self, rows):
        self.excel_driver.append_rows_text_excel(
            filename=self.output_xlsx,
            rows=rows,
            columns=self.columns,
            sheet_name="Sheet1"
        )

    # =========================
    # utils
    # =========================
    def map_columns(self, m):
        return {c: m.get(c, "") for c in self.columns}

    def make_dates(self, fr, to):
        s = datetime.datetime.strptime(str(fr), "%Y%m%d")
        e = datetime.datetime.strptime(str(to), "%Y%m%d")

        dates = []
        while s <= e:
            dates.append(s.strftime("%Y%m%d"))
            s += datetime.timedelta(days=1)

        return dates

    def only_digits(self, s):
        return "".join(ch for ch in str(s) if ch.isdigit())

    def parse_auto_hour(self, auto_time):
        s = str(auto_time).strip()

        if not s.isdigit():
            raise ValueError("auto_time은 숫자여야 합니다")

        n = int(s)

        # 1~4자리 숫자 지원
        if n < 0 or n > 2359:
            raise ValueError("auto_time 범위 오류")

        if n < 100:          # MM → 00:MM
            hour = 0
            minute = n
        else:                # HMM or HHMM
            hour = n // 100
            minute = n % 100

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute

        raise ValueError("auto_time은 HHMM 형식(예: 2000, 0930, 929, 28)으로 입력하세요")


    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
        if self.selenium_driver:
            self.selenium_driver.quit()
