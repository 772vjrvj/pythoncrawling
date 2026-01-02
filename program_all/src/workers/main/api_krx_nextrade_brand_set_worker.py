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

            min_sum_uk = int(self.get_setting_value(self.setting, "price_sum"))
            min_rate = float(self.get_setting_value(self.setting, "rate"))

            min_sum_won = min_sum_uk * 100000000

            auto_yn = str(self.get_setting_value(self.setting, "auto_yn")).lower() in ("1", "true", "y")
            auto_time = str(self.get_setting_value(self.setting, "auto_time"))

            if auto_yn:
                self.output_xlsx = self.output_xlsx_auto
                self.auto_loop(auto_time, min_rate, min_sum_won)
            else:
                self.output_xlsx = f"krx_nextrade_{fr_date}_{to_date}.xlsx"

                dates = self.make_dates(fr_date, to_date)
                all_rows = []

                for idx, ymd in enumerate(dates, start=1):
                    if not self.running:
                        break

                    rows = self.process_one_day(ymd, min_rate, min_sum_won)
                    all_rows.extend(rows)

                    pro = (idx / len(dates)) * 1000000
                    self.progress_signal.emit(self.before_pro_value, pro)
                    self.before_pro_value = pro

                    # === 랜덤 슬립 (1~2초) ===
                    time.sleep(random.uniform(1, 2))

                self.append_excel(all_rows)

            return True

        except Exception as e:
            self.log_signal_func(f"❌ 오류: {e}")
            return False

    # =========================
    # auto
    # =========================
    def auto_loop(self, auto_time, min_rate, min_sum_won):
        hour = self.parse_auto_hour(auto_time)

        while self.running:
            now = datetime.datetime.now()
            today = now.strftime("%Y%m%d")

            if self.last_auto_date == today:
                time.sleep(1)
                continue

            if now.hour == hour and now.minute == 0:
                try:
                    self.output_xlsx = self.output_xlsx_auto
                    rows = self.process_one_day(today, min_rate, min_sum_won)
                    self.append_excel(rows)
                    self.last_auto_date = today
                except Exception as e:
                    self.log_signal_func(f"[AUTO] 오류: {e}")

                time.sleep(65)
            else:
                time.sleep(1)

    # =========================
    # core
    # =========================
    def process_one_day(self, ymd, min_rate, min_sum_won):
        krx = self.fetch_krx(ymd)
        nx = self.fetch_nextrade(ymd)

        krx_map = {self.only_digits(r.get("ISU_SRT_CD")): r for r in krx}
        nx_map = {self.only_digits(r.get("isuSrdCd", "").replace("A", "")): r for r in nx}

        merged = []

        for code in set(krx_map) | set(nx_map):
            k = krx_map.get(code)
            n = nx_map.get(code)

            trade_sum_won = (
                                to_int(k.get("ACC_TRDVAL")) if k else 0
                            ) + (
                                to_int(n.get("accTrval")) if n else 0
                            )

            rate = to_float(k.get("FLUC_RT")) if k else None
            if rate is None and n:
                rate = to_float(n.get("upDownRate"))

            name = n.get("isuAbwdNm") if n else k.get("ISU_ABBRV", code)

            merged.append({
                "날짜": ymd,
                "종목명": name,
                "거래대금합계_원": trade_sum_won,
                "등락률": rate
            })

        merged.sort(key=lambda x: x["거래대금합계_원"], reverse=True)

        rows = []
        for rank, m in enumerate(merged, start=1):
            if m["등락률"] is None:
                continue
            if m["거래대금합계_원"] < min_sum_won:
                continue
            if m["등락률"] < min_rate:
                continue

            m["순위"] = rank
            m["거래대금합계"] = str(m["거래대금합계_원"] // 100000000)

            rows.append(self.map_columns(m))

        return rows

    # =========================
    # fetch
    # =========================
    def fetch_krx(self, ymd):
        self.api_client.get("https://data.krx.co.kr", headers=self.krx_headers)
        time.sleep(random.uniform(1, 2))

        resp = self.api_client.post(self.krx_url, headers=self.krx_headers, data={
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "locale": "ko_KR",
            "mktId": "ALL",
            "trdDd": str(ymd),
            "share": "1",
            "money": "1",
            "csvxls_isNo": "false",
        })
        time.sleep(random.uniform(1, 2))

        return resp.json().get("OutBlock_1", [])

    def fetch_nextrade(self, ymd):
        self.api_client.get("https://www.nextrade.co.kr", headers=self.nx_headers)
        time.sleep(random.uniform(1, 2))

        result = []
        page = 1

        while True:
            resp = self.api_client.post(self.nx_url, headers=self.nx_headers, data={
                "_search": "false",
                "nd": str(int(time.time() * 1000)),
                "pageUnit": "1000",
                "pageIndex": str(page),
                "scAggDd": str(ymd),
            })
            time.sleep(random.uniform(1, 2))

            data = resp.json()
            items = data.get("brdinfoTimeList", [])
            if not items:
                break

            result.extend(items)
            page += 1
            if page > 50:
                break

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
        return [(s + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range((e - s).days + 1)]

    def only_digits(self, s):
        return "".join(ch for ch in str(s) if ch.isdigit())

    def parse_auto_hour(self, auto_time):
        hour = int(str(auto_time).strip())
        if 0 <= hour <= 23:
            return hour
        raise ValueError("auto_time은 0~23 사이의 시간만 입력하세요")

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        time.sleep(3)
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
