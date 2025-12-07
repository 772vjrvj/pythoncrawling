# src/workers/main/delivery/api_delivery_ssg_content_set_load_worker.py
# -*- coding: utf-8 -*-

import json
import random
import threading
import time
import os, re, shutil, requests
import pandas as pd
import pyautogui
from urllib.parse import urlparse, unquote, parse_qs
from bs4 import BeautifulSoup
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.utils.time_utils import parse_datetime_to_yyyymmdd, format_yyyymmdd_to_yyyy_mm_dd
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url
from collections import defaultdict
from datetime import datetime
from src.workers.main.delivery.site_ssg_delivery import SsgDeliveryCrawler
from datetime import datetime, timedelta


class ApiDeliverySsgContentSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.running = True
        self.site_name = "ssg 주문 송장번호 택배사"
        self.excel_filename = ""
        self.data_obj_list = []
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.current_page = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

    # 초기화
    def init(self):
        self.driver_set(False)
        return True

    def _normalize_result_rows_for_export(self, rows):
        """
        CSV 저장용 전처리:
        - 주문일자: yyyy-mm-dd
        - 송장번호: 숫자만 추출
        """
        normalized = []

        for r in rows:
            row = dict(r)

            base_dt = row.get("_parsed_dt")
            if base_dt:
                row["주문일자"] = format_yyyymmdd_to_yyyy_mm_dd(base_dt)
            else:
                raw_date = row.get("주문일자")
                yyyymmdd = parse_datetime_to_yyyymmdd(str(raw_date or ""))
                if yyyymmdd:
                    row["주문일자"] = format_yyyymmdd_to_yyyy_mm_dd(yyyymmdd)

            inv = str(row.get("송장번호") or "")
            row["송장번호"] = re.sub(r"\D", "", inv)

            normalized.append(row)

        return normalized

    # 브라우저 새로 생성
    def _create_driver_for_market(self, headless=False):

        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

        self.selenium_driver = SeleniumUtils(headless)
        self.driver = self.selenium_driver.start_driver(1200)
        self.log_signal_func("[공통] 마켓용 브라우저 새로 생성 완료")


    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.excel_filename, self.columns)

            # ========================
            # 1) 엑셀 데이터 그룹핑
            # ========================
            groups = {}  # market → id → [rows]

            # === 신규: 원본 엑셀 순서 복원용 인덱스 추가 ===
            for idx, row in enumerate(self.excel_data_list):
                row["_orig_idx"] = idx  # 원본 파일 순서 보존

                market = row.get("마켓")
                uid = row.get("id")
                date_str = row.get("주문일자")

                if not market or not uid or not date_str:
                    continue

                dt = parse_datetime_to_yyyymmdd(date_str)
                if not dt:
                    continue

                row["_parsed_dt"] = dt

                if market not in groups:
                    groups[market] = {}
                if uid not in groups[market]:
                    groups[market][uid] = []

                groups[market][uid].append(row)

            # 날짜 내림차순 정렬
            for market in groups:
                self.total_cnt += 1
                for uid in groups[market]:
                    groups[market][uid].sort(
                        key=self.sort_by_date_desc,
                        reverse=True
                    )

            # ========================
            # 2) 마켓별 처리
            # ========================
            all_result_rows = []

            for market in groups:
                self.current_cnt += 1
                self.log_signal_func(f"[마켓] {market}")

                for uid, rows in groups[market].items():
                    self.log_signal_func(f"  [ID] {uid} / row {len(rows)}건")

                    if market == "SSG":

                        # 계정별 브라우저 생성
                        self._create_driver_for_market(headless=True)

                        try:
                            crawler = SsgDeliveryCrawler(
                                self.driver,
                                self.log_signal_func,
                                self.api_client,
                                self.selenium_driver,
                            )
                            result_rows = crawler.fetch_delivery_rows(rows)
                            all_result_rows.extend(result_rows)

                        except Exception as e:
                            self.log_signal_func(f"[SSG] ID {uid} 처리 오류: {e}")

                        finally:
                            if self.driver:
                                try:
                                    self.driver.quit()
                                except:
                                    pass
                                self.driver = None
                                self.log_signal_func(f"[SSG] ID {uid} 브라우저 종료")

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

            # ======================================================
            # === 신규: 최종 결과를 원본 엑셀 순서(_orig_idx)대로 복원 ===
            # ======================================================
            all_result_rows.sort(key=lambda r: r.get("_orig_idx", 0))

            # CSV 출력 직전 전처리
            export_rows = self._normalize_result_rows_for_export(all_result_rows)

            # CSV 저장
            self.excel_driver.append_to_csv(
                self.excel_filename,
                export_rows,
                self.columns
            )

            # CSV → 엑셀 변환
            self.excel_driver.convert_csv_to_excel_and_delete(self.excel_filename)

            return True

        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False


    def sort_by_date_desc(self, item):
        return item["_parsed_dt"]

    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless)
        self.driver = self.selenium_driver.start_driver(1200)

    # 종료 처리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")

        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
