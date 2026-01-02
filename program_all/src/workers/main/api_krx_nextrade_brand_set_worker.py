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

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.number_utils import to_int, to_float


class ApiKrxNextradeSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
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

        # =========================
        # KRX / NEXTRADE URL + REFERER
        # =========================
        self.krx_url = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        self.krx_referer = "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"

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
            "x-requested-with": "XMLHttpRequest",
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
        self.file_driver = FileUtils(self.log_signal_func)
        self.excel_driver = ExcelUtils(self.log_signal_func)
        return True

    def main(self):
        try:
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

    # =========================
    # auto
    # =========================
    def auto_loop(self, auto_time, min_rate, min_sum_won):
        hour = self.parse_auto_hour(auto_time)
        minute = 0

        self.log_signal_func(f"[AUTO] 자동 리포트 시간: {hour:02d}:{minute:02d}")

        while self.running:
            try:
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
        # 세션/쿠키 워밍업 (APIClient가 세션 유지 시 효과)
        try:
            self.log_signal_func(f"[KRX {ymd}] 워밍업 GET")
            self.api_client.get("https://data.krx.co.kr", headers=self.krx_headers)
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            self.log_signal_func(f"[KRX {ymd}] 워밍업 실패: {e}")

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
        # 세션/쿠키 워밍업
        try:
            self.log_signal_func(f"[NEXTRADE {ymd}] 워밍업 GET")
            self.api_client.get("https://www.nextrade.co.kr", headers=self.nx_headers)
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            self.log_signal_func(f"[NEXTRADE {ymd}] 워밍업 실패: {e}")

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
        try:
            hour = int(str(auto_time).strip())
            if 0 <= hour <= 23:
                return hour
        except Exception:
            pass
        raise ValueError("auto_time은 0~23 사이의 시간만 입력하세요")

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
