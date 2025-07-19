import json
import random
import re
import threading
import time
import os
from urllib.parse import urlparse, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from bs4 import BeautifulSoup

from src.utils.config import NAVER_LOC_ALL
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords, extract_numbers
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url  # 서버 URL 및 설정 정보


class ApiOvrepleSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()

        self.place_cookie = None
        self.columns = None
        self.csv_filename = None
        self.cookie1 = None
        self.cookie2 = None
        self.id_list = None
        self.ca_id = None
        self.site_name = "OVREPLE"
        self.shop_url = "http://43.202.198.24/data/item"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.sess = None
        self.api_client = None
        self.saved_ids = set()
        self.base_url = "https://www.ovreple.com/shop/list.php"
        self.dest_base_url = "https://www.ovreple.com/shop/item.php"

    # 초기화
    def init(self):
        keyword_str = self.get_setting_value(self.setting, "keyword")
        self.ca_id = self.get_setting_value(self.setting, "ca_id")
        self.id_list = split_comma_keywords(str(keyword_str))
        self.driver_set()
        self.log_signal_func(f"아이디 리스트 : {self.id_list}")
        return True


    # 프로그램 실행
    def main(self):
        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.columns = ["상품코드", "상품명", "판매가격", "상품설명", "이미지1", "URL"]
        df = pd.DataFrame(columns=self.columns)
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")
        self.total_cnt = self.get_total_cnt()
        self.log_signal_func(f"전체 상품수 : {self.total_cnt}")
        self.get_prod_list()
        return True


    # 상품목록
    def get_prod_list(self):
        for idx, category_id in enumerate(self.id_list, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            self.log_signal_func(f"현재 ID({category_id}): {idx} / {len(self.id_list)}")
            self.detail_id_info(category_id, idx)


    def detail_id_info(self, category_id, idx):
        page = 0
        result_list = []

        try:
            while True:
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                page += 1
                prod_id_list = self.fetch_search_results(category_id, page)
                if len(prod_id_list) == 0:
                    break

                for i, prod_id in enumerate(prod_id_list, start=1):
                    obj = self.fetch_detail_result(prod_id)
                    result_list.append(obj)
                    self.current_cnt += 1
                    self.log_signal_func(f"현재 ID({category_id}): {idx} / {len(self.id_list)}, 현재 상품 : {self.current_cnt}/{self.total_cnt}")
                    self.log_signal_func(f"상품코드 : {obj['상품코드']}, 상품명 : {obj['상품명']}, 판매가격 : {obj['판매가격']}")
                    pro_value = (self.current_cnt / self.total_cnt) * 1000000
                    self.progress_signal.emit(self.before_pro_value, pro_value)
                    self.before_pro_value = pro_value

                self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns)

        except Exception as e:
            self.log_signal_func(f"❌ 키워드 추출 중 오류 발생: {e}")


    def get_total_cnt(self):
        url = f"{self.base_url}?ca_id={self.ca_id}"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.ovreple.com",
            "if-modified-since": "Sun, 13 Jul 2025 12:42:53 GMT",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        try:
            response = self.api_client.get(url=url, headers=headers)
            if not response:
                return 0

            soup = BeautifulSoup(response, "html.parser")
            total_count = 0

            li_tags = soup.select(".list-unstyled li")

            for li in li_tags:
                a_tag = li.find("a", href=True)
                if not a_tag:
                    continue

                href = a_tag["href"]
                text = a_tag.get_text()

                for sub_ca_id in self.id_list:
                    if f"ca_id={sub_ca_id}" in href:
                        match = re.search(r"\((\d+)\)", text)
                        if match:
                            total_count += int(match.group(1))
                        break  # 같은 li에서 여러 id 중복 집계 방지

            return total_count

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_category_count 실패: {e}")
            return 0


    def fetch_search_results(self, category_id, page):
        url = f"{self.base_url}?ca_id={category_id}&sort=&sortodr=&page={page}"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.ovreple.com",
            "if-modified-since": "Sun, 13 Jul 2025 12:42:53 GMT",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        item_ids = []

        try:
            response = self.api_client.get(url=url, headers=headers)
            if not response:
                return item_ids

            soup = BeautifulSoup(response, "html.parser")
            for h4 in soup.select("h4.product-name"):
                a_tag = h4.find("a", href=True)
                if a_tag:
                    match = re.search(r"it_id=([A-Z0-9]+)", a_tag["href"])
                    if match:
                        item_ids.append(match.group(1))

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_search_results 실패: {e}")

        return item_ids


    def fetch_detail_result(self, product_id):
        url = f"{self.dest_base_url}?it_id={product_id}"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.ovreple.com",
            "if-modified-since": "Sun, 13 Jul 2025 14:00:41 GMT",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        try:
            res = self.api_client.get(url=url, headers=headers)
            if res:

                soup = BeautifulSoup(res, "html.parser")
                save_dir = self.file_driver.create_folder(
                    os.path.join("images", self.site_name, product_id)
                )

                # 1. 상품명
                name = soup.select_one("h3.product-title strong")
                name = name.get_text(strip=True) if name else ""

                # 2. 판매가격
                price = soup.select_one("strong.shop-product-prices")
                price = price.get_text(strip=True) if price else ""

                # 3. 이미지1 다운로드 (.shop-product-img img)
                img_tag = soup.select_one(".shop-product-img img")
                image1 = ""
                if img_tag and img_tag.get("src"):
                    src = img_tag["src"]
                    img_url = src if src.startswith("http") else "https:" + src
                    self.file_driver.save_image(save_dir, f"{product_id}_0.jpg", img_url, headers)
                    image1 = f"{self.site_name}/{product_id}/{product_id}_0.jpg"

                # 4. 상품설명 이미지들 → sit_inf_explan 안의 img들 (첫 번째는 제외)
                # 첫번째는 해당 업체 관련 홍보물이라 제거
                content = ""
                sub_imgs = soup.select("#sit_inf_explan img")
                image_count = 0
                for idx, img in enumerate(sub_imgs[1:], 1):  # 첫 번째 img는 제외
                    src = img.get("src")
                    if not src:
                        continue
                    img_url = src if src.startswith("http") else "https:" + src
                    filename = f"{product_id}_{idx}.jpg"
                    self.file_driver.save_image(save_dir, filename, img_url, headers)

                    # 설명용 HTML 구성
                    content += f'<p><img src="{self.shop_url}/{self.site_name}/{product_id}/{filename}" title="{filename}" alt="{filename}"><br style="clear:both;"></p>\n'
                    image_count += 1

                return {
                    "상품코드": product_id,
                    "상품명": name,
                    "판매가격": price,
                    "상품설명": content,
                    "이미지1": image1,
                    "URL": url,
                }

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_detail_result 실패: {e}")
        return {}

    # 드라이버 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # api
        self.api_client = APIClient(use_cache=False, log_func =self.log_signal_func)

    # 마무리
    def destroy(self):
        self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        if self.running:
            self.progress_end_signal.emit()

    # 정지
    def stop(self):
        self.running = False

