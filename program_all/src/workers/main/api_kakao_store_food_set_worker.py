# -*- coding: utf-8 -*-
import time
import requests
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from src.workers.api_base_worker import BaseApiWorker
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
import random

class ApiKakaoStoreFoodSetLoadWorker(BaseApiWorker):
    """
    카카오 스토어 톡딜 푸드 카테고리 수집 워커
    - 페이지 범위(start_page ~ end_page) 순회
    - 각 상품 상세 옵션 API 호출하여 옵션별 실가격 계산
    - 최종 JSON → CSV → Excel 변환
    """

    def __init__(self):
        super().__init__()
        self.current_cnt = None
        self.before_pro_value = 0
        self.total_cnt = 0
        self.api_client = APIClient(use_cache=False)
        self.excel_driver = None
        self.file_driver = None
        self.running = True
        self.site_url = "https://store.kakao.com"
        self.company_name = "kakao_store_food"
        self.site_name = "kaka_ostore_food"
        self.csv_filename = ""
        self.product_obj_list = []

    # -----------------------------
    # 초기화
    # -----------------------------
    def init(self):
        self.driver_set()
        return True

    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ================================")
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)

    # -----------------------------
    # 메인 실행
    # -----------------------------
    def main(self):
        try:
            self.log_signal_func("카카오 스토어 푸드 크롤링 시작")
            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.csv_filename, self.columns)

            self.call_product_list()

            # CSV → Excel 변환
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
            self.log_signal_func("카카오 스토어 크롤링 완료 ✅")
            return True

        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

    # -----------------------------
    # 상품 목록 수집
    # -----------------------------
    def call_product_list(self):
        base_url = "https://store.kakao.com/a/f-s/home/tab/talk-deal/products"

        st_page = int(self.get_setting_value(self.setting, "st_page"))-1
        ed_page = int(self.get_setting_value(self.setting, "ed_page"))-1
        self.total_cnt = ed_page - st_page + 1
        for page in range(st_page, ed_page + 1):
            self.current_cnt = page + 1
            if not self.running:
                break

            timestamp = int(time.time() * 1000)

            params = {
                "page": page,
                "size": 12,
                "talkDealTabCategoryName": "FOOD",
                "preview": "false",
                "_": timestamp
            }

            headers = {
                "authority": "store.kakao.com",
                "method": "GET",
                "path": f"/a/f-s/home/tab/talk-deal/products?page={page}&size=12&talkDealTabCategoryName=FOOD&preview=false&_={timestamp}",
                "scheme": "https",
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "content-type": "application/json",
                "priority": "u=1, i",
                "referer": "https://store.kakao.com/home/top/food?fixed=true",
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "x-shopping-referrer": "",
                "x-shopping-tab-id": "8a4f5f9ed6eb63047e9d35"
            }

            try:
                response = self.api_client.get(base_url, headers=headers, params=params)
                if not response or not response.get("data"):
                    self.log_signal_func(f"[스킵] 페이지 {page}: 응답 없음")
                    continue

                products = response["data"].get("products", [])
                self.log_signal_func(f"페이지 {page + 1} -> {len(products)}건 수집")

                for idx, item in enumerate(products, start= 1):
                    if not self.running:
                        break
                    time.sleep(random.uniform(0.5, 1))
                    obj = self.make_product_obj(item)
                    if obj:
                        self.product_obj_list.append(obj)
                        self.log_signal_func(f"페이지 {page + 1} ({idx}/{len(products)}) 상품: {obj['상품명']} ({obj['업체명']})")

                # 중간 저장
                if len(self.product_obj_list) >= 10:
                    self.excel_driver.append_to_csv(self.csv_filename, self.product_obj_list, self.columns)
                    self.product_obj_list.clear()

                self.log_signal_func(f"전체 진행수: {self.current_cnt} / {self.total_cnt}")
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

            except Exception as e:
                self.log_signal_func(f"페이지 {page} 처리 오류: {e}")

        # 마지막 잔여 데이터 저장
        if self.product_obj_list:
            self.excel_driver.append_to_csv(self.csv_filename, self.product_obj_list, self.columns)

    # -----------------------------
    # 상품 정보 + 옵션 수집
    # -----------------------------
    def make_product_obj(self, p):
        try:
            product_id = p.get("productId")
            store_domain = p.get("storeDomain")
            talkdeal_price = p.get("groupDiscountedPrice") or 0

            # 행사 기간 변환
            period = p.get("groupDiscountPeriod", {})
            from_str, to_str = period.get("from"), period.get("to")
            period_str = None
            if from_str and to_str:
                f = datetime.strptime(from_str, "%Y%m%d%H%M%S")
                t = datetime.strptime(to_str, "%Y%m%d%H%M%S")
                period_str = f"{f.strftime('%Y-%m-%d %H:%M:%S')} ~ {t.strftime('%Y-%m-%d %H:%M:%S')}"

            # === remainDays 안전 처리 ===
            remain_days = int(p.get("remainDays") or 0)
            gcount = p.get("groupDiscountUserCount") or ""

            # 옵션 세부 API 호출
            options = self.get_product_options(store_domain, product_id, talkdeal_price)

            talkdeal_price_list = [
                {"옵션명": opt.get("value"), "가격": opt.get("realPrice")}
                for opt in options
            ]

            obj = {
                "순번": "",
                "톡딜 행사기간": period_str,
                "상품 구매 URL": f"https://store.kakao.com{p.get('linkPath', '')}",
                "앵콜/산지": "",
                "카테고리": "",
                "세부카테고리": "",
                "상품명": p.get("productName"),
                "메인가격": talkdeal_price,
                "옵션별금액": talkdeal_price_list,
                "쿠폰/이벤트유무": "",

                # === remainDays 로직 그대로 반영 ===
                "1일차": gcount if remain_days >= 3 else "",
                "2일차": gcount if remain_days == 2 else "",
                "3일차": gcount if remain_days == 1 else "",
                "4일차": gcount if remain_days == 0 else "",

                "리뷰 개수": f"{p.get('reviewCount', 0):,}",
                "만족도(%)": p.get("productPositivePercentage"),
                "업체명": p.get("storeName"),
                "비고": ""
            }

            return obj

        except Exception as e:
            self.log_signal_func(f"[make_product_obj] 오류: {e}")
            return None

    # -----------------------------
    # 옵션 상세 호출
    # -----------------------------
    def get_product_options(self, store_domain, product_id, base_price):
        try:
            url = f"https://store.kakao.com/a/f-m/{store_domain}/products/{product_id}/options"

            headers = {
                "authority": "store.kakao.com",
                "method": "GET",
                "path": f"/a/f-m/{store_domain}/products/{product_id}/options?_={int(time.time() * 1000)}",
                "scheme": "https",
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "content-type": "application/json",
                "priority": "u=1, i",
                "referer": f"https://store.kakao.com/{store_domain}/products/{product_id}?area=mainp&impression_id=air_shoptab_home_main_talkdeal&ordnum=1",
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "x-shopping-referrer": "",
                "x-shopping-tab-id": "114c398ab6ac8a540ca5a0"
            }

            params = {"_": int(time.time() * 1000)}
            data = self.api_client.get(url, headers=headers, params=params)
            if not data or not data.get("data"):
                return []

            options = data["data"].get("options", [])
            for opt in options:
                add_price = opt.get("addPrice") or 0
                opt["realPrice"] = base_price + add_price

            return options

        except Exception as e:
            self.log_signal_func(f"[get_product_options] 오류: {e}")
            return []

    # -----------------------------
    # 종료 처리
    # -----------------------------
    def destroy(self):
        self.progress_signal.emit(0, 1000000)
        self.log_signal_func("=============== 카카오 스토어 종료중...")
        time.sleep(3)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
