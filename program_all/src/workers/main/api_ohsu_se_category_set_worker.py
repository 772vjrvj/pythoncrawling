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
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url  # 서버 URL 및 설정 정보


class ApiOhsuSeCategorySetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://ohou.se/store/category.json"
        self.base_main_detail_url = "https://ohou.se/productions/{id}/delivery.json"
        self.running = True  # 실행 상태 플래그 추가
        self.site_name = "오늘의 집"
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
        self.driver_set(False)
        return True

    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.excel_filename, self.columns)

            for row in self.excel_data_list:
                url = row.get("url", "")
                category = row.get("category", "")

                # === 신규 === URL 파라미터 추출
                parsed = urlparse(url)
                params = parse_qs(parsed.query)

                category_id = params.get("category_id", [""])[0]
                order = params.get("order", [""])[0]
                affect_type = params.get("affect_type", [""])[0]
                affect_id = params.get("affect_id", [""])[0]

                # === 로그 출력
                self.log_signal_func(f"url: {url}")
                self.log_signal_func(f"category: {category}")
                self.log_signal_func(
                    f"category_id: {category_id}, order: {order}, affect_type: {affect_type}, affect_id: {affect_id}"
                )

                # === 호출
                self.call_product_list(category_id, order, affect_type, affect_id, category)

            # === 마지막 잔여 데이터 저장 ===
            if self.data_obj_list:
                self.excel_driver.append_to_csv(self.excel_filename, self.data_obj_list, self.columns)
                self.data_obj_list.clear()

            return True
        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

    # -----------------------------
    # 상품 목록 + 상세 수집
    # -----------------------------
    def call_product_list(self, category_id, order, affect_type, affect_id, category):
        # 설정에서 시작/끝 페이지(1-base) 읽기
        st_page_idx = int(self.get_setting_value(self.setting, "st_page")) - 1  # 0-base
        ed_page_idx_cfg = int(self.get_setting_value(self.setting, "ed_page")) - 1  # 0-base

        if st_page_idx < 0:
            st_page_idx = 0

        per_page = 100  # 한 페이지당 100개

        # =========================
        # 1) 최초 조회: item_count로 실제 전체 페이지 계산
        # =========================
        headers_base = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "referer": f"https://ohou.se/store/category?category_id={category_id}&order={order}&affect_type={affect_type}&affect_id={affect_id}",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }

        # === 신규 ===: 최초 페이지는 st_page_idx 기준으로 조회 (1-base page)
        first_page_no = st_page_idx + 1
        first_params = {
            "v": "2",
            "category_id": category_id,
            "order": order,
            "affect_type": affect_type,
            "affect_id": affect_id,
            "per": str(per_page),
            "page": first_page_no,
        }

        first_data = None
        try:
            self.log_signal_func(f"[초기조회] page={first_page_no} 카테고리={category}")
            first_data = self.api_client.get(self.base_main_url, headers=headers_base, params=first_params)
        except Exception as e:
            self.log_signal_func(f"[초기조회 실패] page={first_page_no}: {e}")
            return

        if not first_data:
            self.log_signal_func("[초기조회] 응답 없음, 스킵")
            return

        # item_count에서 전체 페이지 계산
        item_count = first_data.get("item_count", 0)
        if not isinstance(item_count, int):
            try:
                item_count = int(item_count)
            except Exception:
                item_count = 0

        if item_count <= 0:
            self.log_signal_func(f"[초기조회] item_count가 0 입니다. (category_id={category_id})")
            return

        # ceil(item_count / per_page)
        self.total_pages = (item_count + per_page - 1) // per_page
        self.log_signal_func(f"[초기조회] item_count={item_count}, per={per_page}, total_pages={self.total_pages}")

        # 설정에서 받은 ed_page_idx와 실제 total_pages 중 작은 쪽을 사용
        max_idx = self.total_pages - 1  # 0-base
        if ed_page_idx_cfg > max_idx:
            ed_page_idx = max_idx
        else:
            ed_page_idx = ed_page_idx_cfg

        if st_page_idx > ed_page_idx:
            self.log_signal_func(f"[초기조회] st_page({st_page_idx+1}) > ed_page({ed_page_idx+1}), 스킵")
            return

        # 전체 진행 페이지 수 (게이지 분모)
        self.total_cnt = ed_page_idx - st_page_idx + 1

        # =========================
        # 2) 실제 페이지 루프
        # =========================
        for page_idx in range(st_page_idx, ed_page_idx + 1):
            if not self.running:
                break

            self.current_cnt = (page_idx - st_page_idx) + 1  # 1-base 진행 카운트
            page_no = page_idx + 1                          # API page 파라미터 (1-base)

            # 첫 페이지는 초기조회 결과 재사용
            if page_idx == st_page_idx:
                data = first_data
            else:
                params = {
                    "v": "2",
                    "category_id": category_id,
                    "order": order,
                    "affect_type": affect_type,
                    "affect_id": affect_id,
                    "per": str(per_page),
                    "page": page_no,
                }
                try:
                    data = self.api_client.get(self.base_main_url, headers=headers_base, params=params)
                except Exception as e:
                    self.log_signal_func(f"[목록] 페이지 {page_no} 요청 실패: {e}")
                    continue

            if not data or not data.get("productions"):
                self.log_signal_func(f"[스킵] 페이지 {page_no}: productions 없음")
                continue

            productions = data.get("productions", [])
            self.log_signal_func(f"[목록] 페이지 {page_no} -> {len(productions)}건 수집")

            # =========================
            # 각 상품 상세까지 조회해서 obj 생성
            # =========================
            for idx, item in enumerate(productions, start=1):
                if not self.running:
                    break

                product_id = str(item.get("id", "")).strip()
                product_name = (item.get("name") or "").strip()

                if not product_id:
                    self.log_signal_func(f"[상품스킵] page={page_no} idx={idx} : id 없음")
                    continue

                # 상세 조회
                detail_url = self.base_main_detail_url.format(id=product_id)
                detail_headers = headers_base.copy()
                # 상세 referer는 굳이 안 바꿔도 되지만, 필요시 이렇게:
                detail_headers["referer"] = f"https://ohou.se/productions/{product_id}/selling"

                detail_params = {"v": "3"}

                seller_info = {}
                try:
                    detail_data = self.api_client.get(detail_url, headers=detail_headers, params=detail_params)
                    seller_info = detail_data.get("seller_info") or {}
                except Exception as e:
                    self.log_signal_func(f"[상세 실패] id={product_id}, page={page_no}: {e}")
                    seller_info = {}

                # seller_info 필드들
                company = (seller_info.get("company") or "").strip()
                representative = (seller_info.get("representative") or "").strip()
                address = (seller_info.get("address") or "").strip()
                cs_phone = (seller_info.get("cs_phone") or "").strip()
                email = (seller_info.get("email") or "").strip()
                license_no = (seller_info.get("license") or "").strip()
                ec_license = (seller_info.get("ec_license") or "").strip()

                # === 최종 obj 생성 ===
                row_obj = {
                    "카테고리": category,
                    "아이디": product_id,
                    "상품명": product_name,
                    "페이지": page_no,
                    "상호": company,
                    "대표자": representative,
                    "사업장소재지": address,
                    "고객센터 전화번호": cs_phone,
                    "E-mail": email,
                    "사업자 등록번호": license_no,
                    "통신판매업 신고번호": ec_license,
                }

                self.data_obj_list.append(row_obj)

                self.log_signal_func(
                    f"[상품] page={page_no} idx={idx} id={product_id} name={product_name} email={email}"
                )

                # 너무 빠르게 때리지 않도록 딜레이
                time.sleep(random.uniform(0.2, 0.5))

                # === 신규: 버퍼가 어느 정도 쌓이면 CSV로 중간 저장 ===
                if len(self.data_obj_list) >= 100:
                    self.excel_driver.append_to_csv(self.excel_filename, self.data_obj_list, self.columns)
                    self.data_obj_list.clear()
                    self.log_signal_func("[중간저장] 100건 저장")

            # 페이지 단위 진행률 (게이지) 업데이트
            self.log_signal_func(f"전체 진행수: {self.current_cnt} / {self.total_cnt}")
            try:
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
            except Exception as e:
                self.log_signal_func(f"[진행률 오류] {e}")

        # 루프 끝: 남은 내용은 main()에서 한 번 더 flush

    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        self.running = False
