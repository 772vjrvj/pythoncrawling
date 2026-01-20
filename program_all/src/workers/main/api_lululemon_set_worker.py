import os
import re
import json
import time
from decimal import Decimal
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker
import random

# =========================================================
# API
# =========================================================
class ApiLululemonSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.file_driver = None
        self.excel_driver = None

        self.url_list = []
        self.running = True

        self.company_name = "lululemon_option"
        self.site_name = "lululemon_option"

        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        self.api_client = APIClient(use_cache=False)

        # === 엑셀 컬럼 ===
        self.columns = ["컬러", "사이즈", "옵션가", "재고수량", "관리코드", "사용여부"]

        # === 저장 폴더 ===
        self.out_dir = os.path.join(os.getcwd(), "output_lululemon")
        os.makedirs(self.out_dir, exist_ok=True)

    # -----------------------------------------------------
    # 초기화
    # -----------------------------------------------------
    def init(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        return True

    # -----------------------------------------------------
    # 메인
    # -----------------------------------------------------
    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            # 외부에서 넘어온 excel_data_list 에서 URL 컬럼 추출
            self.url_list = [
                str(row[k]).strip()
                for row in self.excel_data_list
                for k in row.keys()
                if k.lower() == "url" and row.get(k) and str(row[k]).strip()
            ]

            self.total_cnt = len(self.url_list)
            self.current_cnt = 0
            self.before_pro_value = 0

            self.call_product_list()
            return True

        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

    # -----------------------------------------------------
    # URL 목록 처리 (url 1개당 엑셀 1개)
    # -----------------------------------------------------
    def call_product_list(self):
        if not self.url_list:
            return

        for num, url in enumerate(self.url_list, start=1):
            if not self.running:
                break

            self.current_cnt += 1

            options, product_name = self.product_api_data(url)

            # === 저장 전 로그 ===
            if options:
                self.log_signal.emit(
                    f"[옵션 미리보기] 총 {len(options)}건 / 첫번째 옵션: {options[0]}"
                )
            else:
                self.log_signal.emit("[옵션 미리보기] 옵션 없음 (0건)")

            filename = f"{self.safe_filename(product_name)}_{self.now_stamp()}.xls"
            fullpath = os.path.join(self.out_dir, filename)

            # openpyxl은 xlsx만 지원 → 임시 xlsx 저장 후 xls로 rename
            tmp_xlsx = fullpath[:-4] + ".xlsx"

            self.excel_driver.save_obj_list_to_excel(
                filename=tmp_xlsx,
                obj_list=options,
                columns=self.columns,
                sheet_name="Sheet1"
            )

            if os.path.exists(tmp_xlsx):
                if os.path.exists(fullpath):
                    os.remove(fullpath)
                os.rename(tmp_xlsx, fullpath)

            self.log_signal.emit(f"({num}/{self.total_cnt}) 저장완료: {fullpath}")

            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

            time.sleep(random.uniform(3, 5))

    # -----------------------------------------------------
    # 단일 상품 처리 (옵션 배열 + 상품명)
    # -----------------------------------------------------
    def product_api_data(self, url: str):
        try:
            u = urlparse(url)
            authority = u.netloc
            path = u.path + (("?" + u.query) if u.query else "")
            origin = f"{u.scheme}://{u.netloc}"
            referer = origin + "/"

            headers = {
                "authority": authority,
                "method": "GET",
                "path": path,
                "scheme": u.scheme,

                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "cache-control": "max-age=0",
                "priority": "u=0, i",
                "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",

                "host": authority,
                "origin": origin,
                "referer": referer,
            }

            s = requests.Session()
            s.get(referer, headers=headers, timeout=20)
            resp = s.get(url, headers=headers, timeout=20)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")

            productgroup = None
            for sc in scripts:
                if not sc.string:
                    continue
                try:
                    data = json.loads(sc.string)
                except Exception:
                    continue

                try:
                    objs = [data]
                    data.get("@type")
                except Exception:
                    objs = data

                for obj in objs:
                    if obj.get("@type") == "ProductGroup" and obj.get("hasVariant"):
                        productgroup = obj
                        break
                if productgroup:
                    break

            if not productgroup:
                self.log_signal.emit(f"[SKIP] ProductGroup 없음: {url}")
                return [], "product"

            variants = productgroup.get("hasVariant") or []

            product_name = "product"
            for v in variants:
                nm = (v.get("name") or "").strip()
                if nm:
                    product_name = nm.split(" - ")[0].strip()
                    break

            rows = []
            for v in variants:
                color = (v.get("color") or "").strip()
                size = (v.get("size") or "").strip()

                nm = (v.get("name") or "").strip()
                if nm and (not color or not size):
                    parts = [p.strip() for p in nm.split(" - ")]
                    if len(parts) >= 3:
                        if not color:
                            color = parts[-2]
                        if not size:
                            size = parts[-1]

                offers = v.get("offers") or []
                offer0 = offers[0] if offers else {}

                rows.append({
                    "color": color,
                    "size": size,
                    "priceCurrency": offer0.get("priceCurrency", ""),
                    "price": offer0.get("price", ""),
                    "availability": offer0.get("availability", ""),
                })

            min_price = None
            for r in rows:
                try:
                    p = Decimal(r["price"])
                except Exception:
                    continue
                if min_price is None or p < min_price:
                    min_price = p

            rows.sort(key=lambda r: (r["color"], int(r["size"]) if str(r["size"]).isdigit() else 9999))

            out = []
            for r in rows:
                in_stock = "Y" if str(r["availability"]).endswith("InStock") else "N"

                opt = 0
                if min_price and r["priceCurrency"] == "CAD":
                    try:
                        diff = Decimal(r["price"]) - min_price
                        if diff > 0:
                            opt = int(diff) * 1000
                    except Exception:
                        pass

                out.append({
                    "컬러": self.shorten_color(r["color"]),
                    "사이즈": r["size"],
                    "옵션가": opt,
                    "재고수량": 5 if in_stock == "Y" else 0,
                    "관리코드": "",
                    "사용여부": "Y",
                })

            return out, product_name

        except Exception as e:
            self.log_signal.emit(f"[SKIP] 처리 실패: {url} / {e}")
            return [], "product"



    # -----------------------------------------------------
    # 컬러명 25자 제한 축약
    # -----------------------------------------------------
    def shorten_color(self, color: str) -> str:
        if len(color) <= 25:
            return color
        parts = color.split()
        if not parts:
            return color[:25]
        return (parts[0] + " " + "".join(p[0].upper() for p in parts[1:]))[:25]

    # -----------------------------------------------------
    # 파일명 안전 처리
    # -----------------------------------------------------
    def safe_filename(self, name: str) -> str:
        name = re.sub(r'[\\/:*?"<>|]', "_", name.strip())
        return (name or "product")[:80]

    # -----------------------------------------------------
    # yyyyMMdd_HHmmss
    # -----------------------------------------------------
    def now_stamp(self):
        return time.strftime("%Y%m%d_%H%M%S")

    # -----------------------------------------------------
    # 종료
    # -----------------------------------------------------
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
