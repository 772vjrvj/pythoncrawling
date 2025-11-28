# src/workers/main/delivery/api_delivery_content_set_load_worker.py
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
from src.utils.config import server_url  # 서버 URL 및 설정 정보
from collections import defaultdict
from datetime import datetime
from src.workers.main.delivery.site_11st_delivery import ElevenstDeliveryCrawler
from src.workers.main.delivery.site_ssg_delivery import SsgDeliveryCrawler
from datetime import datetime, timedelta


class ApiDeliveryContentSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://ohou.se/store/category.json"
        self.base_main_detail_url = "https://ohou.se/productions/{id}/delivery.json"
        self.running = True  # 실행 상태 플래그 추가
        self.site_name = "주문 송장번호 택배사"
        self.excel_filename = ""
        self.data_obj_list = []
        self.total_cnt = 0            # 전체 페이지 개수(=게이지 분모)
        self.total_pages = 0
        self.current_cnt = 0          # 현재 진행 페이지
        self.current_page = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

    # 초기화
    def init(self):
        # 기존처럼 한 번 호출해서 excel_driver, file_driver, selenium_driver, driver 세팅
        self.driver_set(False)
        return True

    def _normalize_result_rows_for_export(self, rows):
        """
        CSV 저장용 전처리:
        - 주문일자: yyyy-mm-dd
        - 송장번호: 숫자만 남김
        """
        normalized = []

        for r in rows:
            row = dict(r)  # 원본 수정 방지

            # 주문일자 처리
            base_dt = row.get("_parsed_dt")
            if base_dt:
                row["주문일자"] = format_yyyymmdd_to_yyyy_mm_dd(base_dt)
            else:
                raw_date = row.get("주문일자")
                yyyymmdd = parse_datetime_to_yyyymmdd(str(raw_date or ""))
                if yyyymmdd:
                    row["주문일자"] = format_yyyymmdd_to_yyyy_mm_dd(yyyymmdd)

            # 송장번호 숫자만
            inv = str(row.get("송장번호") or "")
            inv_digits = re.sub(r"\D", "", inv)
            row["송장번호"] = inv_digits

            normalized.append(row)

        return normalized

    # === 신규: 마켓별로 독립적인 WebDriver 생성 유틸 ===
    def _create_driver_for_market(self, headless=False):
        """
        마켓마다 완전히 독립된 브라우저 세션을 사용하기 위해
        기존 드라이버를 정리하고 새로 생성한다.
        """
        # 이전 마켓에서 사용하던 드라이버 정리
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.log_signal_func(f"[공통] 이전 드라이버 quit 중 오류 (무시): {e}")
            finally:
                self.driver = None

        # SeleniumUtils 새로 생성
        self.selenium_driver = SeleniumUtils(headless)

        # 새 WebDriver 시작
        self.driver = self.selenium_driver.start_driver(1200)
        self.log_signal_func("[공통] 마켓용 브라우저 새로 생성 완료")

    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.excel_filename, self.columns)

            # =========================
            # 1) 엑셀 데이터 그룹핑 (마켓, id)
            # =========================
            groups = {}   # market → id → [row list]

            for row in self.excel_data_list:
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

            # 정렬 (최근 주문일자 기준 내림차순)
            for market in groups:
                self.total_cnt += 1
                for uid in groups[market]:
                    groups[market][uid].sort(
                        key=self.sort_by_date_desc,
                        reverse=True
                    )

            # =========================
            # 2) 마켓별 처리
            # =========================
            all_result_rows = []

            for market in groups:
                self.current_cnt += 1
                self.log_signal_func(f"[마켓] {market}")

                # === 신규: 마켓 시작마다 브라우저 새로 띄우기 ===
                self._create_driver_for_market(headless=False)

                for uid in groups[market]:
                    rows = groups[market][uid]
                    self.log_signal_func(f"  [ID] {uid} / row {len(rows)}건")

                    if market == "11번가":
                        crawler = ElevenstDeliveryCrawler(
                            self.driver,
                            self.log_signal_func,
                            self.api_client,
                            self.selenium_driver,
                        )
                        result_rows = crawler.fetch_delivery_rows(rows)
                        all_result_rows.extend(result_rows)

                    elif market == "SSG":
                        crawler = SsgDeliveryCrawler(
                            self.driver,
                            self.log_signal_func,
                            self.api_client,
                            self.selenium_driver,
                        )
                        result_rows = crawler.fetch_delivery_rows(rows)
                        all_result_rows.extend(result_rows)

                    else:
                        # 그 외 마켓은 일단 로그만
                        for r in rows:
                            self.log_signal_func(
                                f"    [날짜] {r.get('주문일자')} → row: {r}"
                            )

                # === 신규: 마켓 처리 끝나면 브라우저 정리 ===
                if self.driver:
                    try:
                        self.driver.quit()
                        self.log_signal_func(f"[마켓] {market} 브라우저 종료")
                    except Exception as e:
                        self.log_signal_func(f"[마켓] {market} 브라우저 종료 중 오류 (무시): {e}")
                    finally:
                        self.driver = None

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

            # === CSV 저장 시점에 날짜/송장번호 형식 맞춰서 출력 ===
            export_rows = self._normalize_result_rows_for_export(all_result_rows)
            self.excel_driver.append_to_csv(self.excel_filename, export_rows, self.columns)

            # CSV -> 엑셀 변환
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

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)

        # 드라이버 세팅
        self.driver = self.selenium_driver.start_driver(1200)

    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")

        # === 신규: 남아 있는 드라이버 정리 ===
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.log_signal_func(f"[공통] destroy 중 드라이버 종료 오류 (무시): {e}")
            finally:
                self.driver = None

        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        self.running = False
