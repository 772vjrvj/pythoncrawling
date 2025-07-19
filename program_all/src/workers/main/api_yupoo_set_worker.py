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


class ApiYupooSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()

        self.place_cookie = None
        self.columns = None
        self.csv_filename = None
        self.cookie1 = None
        self.cookie2 = None
        self.id_list = None
        self.site_name = "YUPOO"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.sess = None
        self.before_pro_value = 0
        self.api_client = None
        self.saved_ids = set()
        self.base_url = "https://tbstore.x.yupoo.com"
        self.dest_base_url = "http://43.202.198.24/data/item/yupoo"

    # 초기화
    def init(self):
        keyword_str = self.get_setting_value(self.setting, "keyword")
        self.id_list = split_comma_keywords(str(keyword_str))
        self.cookie1 = (self.get_setting_value(self.setting, "cookie1") or "").strip()
        self.cookie2 = (self.get_setting_value(self.setting, "cookie2") or "").strip()
        self.driver_set()
        self.log_signal_func(f"쿠키 목록 : {self.cookie1}")
        self.log_signal_func(f"쿠키 상세: {self.cookie2}")
        self.log_signal_func(f"아이디 리스트 : {self.id_list}")
        return True


    # 프로그램 실행
    def main(self):
        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.columns = ["상품코드", "상품명", "판매가격", "상품설명", "이미지1", "사이즈", "URL"]
        df = pd.DataFrame(columns=self.columns)
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")
        self.get_total_cnt()
        self.get_prod_list()
        return True

    # 전체수
    def get_total_cnt(self):
        self.total_cnt = 0  # 누적값 초기화
        for idx, category_id in enumerate(self.id_list, start=1):
            if not self.running:
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            result = self.fetch_search_results(category_id, page=1)
            count = result.get("total", 0)
            self.total_cnt += count
        self.log_signal_func(f"전체 상품수 : {self.total_cnt}")

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
                rs_obj = self.fetch_search_results(category_id, page)
                href_list = rs_obj['href_list']
                if len(href_list) == 0:
                    break

                for i, href in enumerate(href_list, start=1):
                    obj = self.fetch_detail_result(href, category_id)
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


    def fetch_search_results(self, category_id, page):
        url = f"{self.base_url}/categories/{category_id}?isSubCate=true&page={page}"

        headers = {
            "authority": "tbstore.x.yupoo.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "if-none-match": 'W/"59102-DA0thjIsSL0PJIxKgr9cjZQx9Vg"',
            "priority": "u=0, i",
            "referer": f"https://tbstore.x.yupoo.com/categories/{category_id}?isSubCate=true&page={page}",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "cookie": self.cookie1
        }

        try:
            res = self.api_client.get(url=url, headers=headers)
            if res:
                soup = BeautifulSoup(res, "html.parser")

                # 총 앨범 수 추출
                total = 0
                total_div = soup.select_one('.categories__box-right-total')
                if total_div:
                    numbers = extract_numbers(total_div.get_text(strip=True))
                    if numbers:
                        total = numbers[0]

                # 앨범 링크 목록 추출
                href_list = []
                for a in soup.find_all("a", class_="album__main"):
                    href = a.get("href")
                    if href:
                        full_href = href if href.startswith("http") else self.base_url + href
                        href_list.append(full_href)

                return {
                    "total": total,
                    "href_list": href_list
                }

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_search_results 실패: {e}")
            return {
                "total": 0,
                "href_list": []
            }


    def fetch_detail_result(self, href, category_id):
        product_id = urlparse(href).path.split("/")[2]

        url = f"https://tbstore.x.yupoo.com/albums/{product_id}?uid=1&isSubCate=true&referrercate={category_id}"

        headers = {
            "authority": "tbstore.x.yupoo.com",
            "method": "GET",
            "path": f"/albums/{product_id}?uid=1&isSubCate=true&referrercate={category_id}",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": self.cookie2,
            "if-none-match": 'W/"343d0-QKunod6Kzu5eUkRKBUaYWV9rD/4"',
            "priority": "u=0, i",
            "referer": href,
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1"
        }

        try:
            res = self.api_client.get(url=url, headers=headers)
            if res:
                soup = BeautifulSoup(res, "html.parser")

                price, name = "", ""
                title_tag = soup.select_one(".showalbumheader__gallerytitle")
                if title_tag:
                    text = title_tag.get_text(strip=True)
                    parts = text.split('/')
                    if len(parts) == 2:
                        price, name = parts[0].strip(), parts[1].strip()
                    else:
                        name = text

                size = ""
                size_tag = soup.select_one(".showalbumheader__gallerysubtitle.htmlwrap__main")
                if size_tag:
                    for token in size_tag.get_text(strip=True).split():
                        if "-" in token and any(c.isdigit() for c in token):
                            size = token
                            break

                # ⬇️ 폴더 경로 변경: images/yupoo/category_id/product_id
                save_dir = self.file_driver.create_folder(
                    os.path.join("images", "yupoo", f"yupoo_{category_id}", product_id)
                )

                cover_img = soup.select_one(".showalbumheader__gallerycover img")
                if cover_img and cover_img.get("src"):
                    src = cover_img["src"]
                    img_url = src if src.startswith("http") else "https:" + src
                    self.file_driver.save_image(save_dir, f"{product_id}_0.jpg", img_url, headers)

                sub_imgs = soup.select(".showalbum__children.image__main img")
                image_count = 0
                for idx, img in enumerate(sub_imgs, 1):
                    src = img.get("data-origin-src") or img.get("src")
                    if not src:
                        continue
                    img_url = src if src.startswith("http") else "https:" + src
                    self.file_driver.save_image(save_dir, f"{product_id}_{idx}.jpg", img_url, headers)
                    image_count += 1

                content, image1 = self.generate_content_and_image1(product_id, image_count)

                return {
                    "상품코드": product_id,
                    "상품명": name,
                    "판매가격": price,
                    "상품설명": content,
                    "이미지1": image1,
                    "사이즈": size,
                    "URL": href,
                }

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_detail_result 실패: {e}")
            return {}

    def generate_content_and_image1(self, product_id, image_count):
        image1 = f"yupoo/{product_id}/{product_id}_0.jpg"

        html_blocks = []
        for idx in range(1, image_count + 1):
            file = f"{product_id}_{idx}.jpg"
            full_url = f"{self.dest_base_url}/{product_id}/{file}"
            block = (
                f'<p><img src="{full_url}" title="{file}" alt="{file}">'
                f'<br style="clear:both;"></p>'
            )
            html_blocks.append(block)

        description_html = "\n".join(html_blocks)
        return description_html, image1


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

