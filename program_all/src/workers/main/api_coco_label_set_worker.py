import json
import random
import re
import threading
import time
import os
from PIL import Image
from io import BytesIO

from urllib.parse import urlparse, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from bs4 import BeautifulSoup

from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url  # 서버 URL 및 설정 정보

class ApiCocoLabelSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()

        self.excel_filename = None
        self.coco_label_admin_list = None
        self.coco_label_site_list = None
        self.site_name = "COCO_LABEL"
        self.shop_url = "https://coco-label.com"
        self.shop_detail_url = "https://coco-label.com/ajax/get_shop_list_view.cm"

        self.file_driver = None
        self.excel_driver = None
        self.api_client = None

        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.keyword_list = None

        self.sess = None

        self.result = []
        self.img_count = 1

        self.headers = {
            "authority": "coco-label.com",
            "method": "GET",
            "path": "/",
            "scheme": "https",

            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "priority": "u=0, i",

            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',

            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",

            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        }

        self.main_category_obj_list = []
        self.main_category_obj_filter_list = []
        self.main_sub_category_obj_list = []


    # 초기화
    def init(self):
        self.driver_set()
        self.coco_label_admin_list = self.file_driver.read_json_array_from_resources("coco_label_admin_list.json")
        self.coco_label_site_list = self.file_driver.read_json_array_from_resources("coco_label_site_list.json")
        keyword_str = self.get_setting_value(self.setting, "keyword")
        self.keyword_list = split_comma_keywords(keyword_str)
        self.log_signal_func(f"요청 목록 : {self.keyword_list}")
        self.log_signal_func(f"관리자 목록 : {self.coco_label_admin_list}")
        self.log_signal_func(f"사이트 목록 : {self.coco_label_site_list}")
        return True


    def main(self):
        self.log_signal_func("크롤링 시작.")
        self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
        self.excel_driver.init_csv(self.excel_filename, self.columns)

        self.main_category_list()

        self.map_category()

        self.filter_by_keywords()

        self.log_signal_func(f"main_category_obj_filter_list : {self.main_category_obj_filter_list}")

        self.sub_category_list()

        self.get_product_detail()

        return True


    def main_category_list(self):
        response = self.api_client.get(url=self.shop_url, headers=self.headers)
        soup = BeautifulSoup(response, 'html.parser')
        root = soup.select_one(".viewport-nav.desktop._main_menu")
        self.main_category_obj_list = []
        if root:
            for li in root.find_all("li", class_="dropdown", recursive=False):
                a = li.find("a", recursive=False)
                if not a:
                    continue

                span = a.find("span", recursive=False)
                obj = {
                    "name": span.get_text(strip=True) if span else "",
                    "href": (a.get("href") or "").strip()
                }

                ul = li.find("ul", recursive=False)
                if ul:
                    children = []
                    for cli in ul.find_all("li", recursive=False):
                        ca = cli.find("a", recursive=False)
                        if not ca:
                            continue
                        cspan = ca.find("span", recursive=False)
                        children.append({
                            "name": cspan.get_text(strip=True) if cspan else "",
                            "href": (ca.get("href") or "").strip()
                        })
                    if children:
                        obj["children"] = children

                self.main_category_obj_list.append(obj)


    def map_category(self):
        for main_category_obj in self.main_category_obj_list:
            main_name = main_category_obj.get("name", "").replace(" ", "")

            # 상위 매핑
            for admin in self.coco_label_admin_list:
                admin_name = admin.get("name", "").replace(" ", "")

                if admin_name == main_name:
                    main_category_obj["value"] = admin.get("value")

                    # 자식 매핑
                    if "children" in main_category_obj and "children" in admin:
                        for m_child in main_category_obj["children"]:
                            m_child_name = m_child.get("name", "").replace(" ", "")

                            for c_child in admin["children"]:
                                c_child_name = c_child.get("name", "").replace(" ", "")

                                if c_child_name == m_child_name:
                                    m_child["value"] = c_child.get("value")
                                    break
                    break



        #
        #
        # self.main_category_obj_list = []
        # for index, keyword in enumerate(self.keyword_list, start=1):
        #     main_category = self.find_by_key(keyword)
        #     url = f"{self.shop_url}/{main_category["value"]}"
        #     response = self.api_client.get(url=url, headers=self.headers2)
        #     soup = BeautifulSoup(response, 'html.parser')
        #     items = soup.select('._item.item_gallary')
        #     main_obj = {
        #         'main_category_obj': main_category,
        #         'main_category_key': main_category["key"],
        #         'main_category_url': url,
        #         'sub_category_obj_list': items,
        #     }
        #     self.log_signal_func(f"key : {main_category["key"]}")
        #     self.main_category_obj_list.append(main_obj)
        #
        # self.log_signal_func(f"main_list : {len(self.main_category_obj_list)}")
        # self.sub_category_list()


    def filter_by_keywords(self):
        self.main_category_obj_filter_list = []
        for main_category_obj in self.main_category_obj_list:
            main_category_name = main_category_obj.get("name", "").replace(" ", "")

            for kw in self.keyword_list:
                if main_category_name == kw.replace(" ", ""):
                    self.main_category_obj_filter_list.append(main_category_obj)
                    break


    def sub_category_list(self):

        for main_category_obj_filter in self.main_category_obj_filter_list:

            sub_category_obj_list = main_category_obj_filter['children']

            for sub_category_obj in sub_category_obj_list:
                sub_category_name = sub_category_obj['name']
                sub_category_href = sub_category_obj['href']
                url = f"{self.shop_url}{sub_category_href}"
                response = self.api_client.get(url=url, headers=self.headers)
                pattern = r"['\"]category['\"]\s*:\s*['\"]([^'\"]+)['\"]"
                match = re.search(pattern, response)

                sub_category_code = match.group(1) if match else ''

                obj = {
                    '메인카테고리': main_category_obj_filter["name"],
                    '하위카테고리': sub_category_name,
                    '하위카테고리코드': sub_category_code,
                    'url': url,
                    'href': sub_category_href,

                    '상품코드': '',
                    '기본분류': main_category_obj_filter['value'],
                    '분류2': sub_category_obj['value'],
                    '상품명': '',
                    '브랜드': '',
                    '상품설명': '',
                    '모바일상품설명': '',
                    '시중가격': '',
                    '판매가격': '',
                    '판매가능': 1, # 고정
                    '재고수량': 999, # 고정
                    '이미지1': '', # 고정
                    '옵션': '', # 고정
                }
                self.log_signal_func(f"obj : {obj}")
                self.main_sub_category_obj_list.append(obj)


    def get_product_detail(self):

        for base_obj in self.main_sub_category_obj_list:

            category_code = base_obj.get('하위카테고리코드', '')
            category_name = base_obj.get('하위카테고리', '')

            if not category_code:
                self.log_signal_func(f"[보류] 하위카테고리코드 없음: {category_name} / url={base_obj.get('url')}")





            else:
                stop = False
                idx_number_list = set()

                for page in range(1, 10000):

                    if not self.running:
                        return

                    if stop:
                        break

                    params = {
                        'page': page,
                        'pagesize': '24',
                        'category': category_code,
                        'sort': 'recent',
                        "menu_url": f"{base_obj['href']}/",
                        "_": int(time.time() * 1000),
                    }

                    self.log_signal_func(f"[{category_name}] {page}페이지 조회중...")

                    headers_ajax = {
                        "authority": "coco-label.com",
                        "method": "GET",
                        "path": "/ajax/get_shop_list_view.cm",
                        "scheme": "https",

                        "accept": "application/json, text/javascript, */*; q=0.01",
                        "accept-encoding": "gzip, deflate, br, zstd",
                        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",

                        "priority": "u=0, i",
                        "referer": f"https://coco-label.com{base_obj['href']}",

                        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Windows"',

                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "same-origin",

                        "x-requested-with": "XMLHttpRequest",

                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                    }


                    # ✅ /ajax/get_shop_list_view.cm 은 JSON 응답( { html: "..." } )
                    data = self.api_client.get(url=self.shop_detail_url, params=params, headers=headers_ajax)

                    # 🔧 여기 추가 (str → dict)
                    try:
                        data = json.loads(data)
                    except Exception as e:
                        self.log_signal_func(f"[에러] json 파싱 실패: {category_name} page={page} / {e}")
                        break

                    html = data.get('html', '')
                    if not html:
                        self.log_signal_func(f"[종료] html 비어있음: {category_name} page={page}")
                        break

                    soup = BeautifulSoup(html, 'html.parser')
                    items = soup.select('.shop-item')
                    if not items:
                        self.log_signal_func(f"[종료] 아이템 없음: {category_name} page={page}")
                        break

                    for item in items:

                        product_prop = item.get('data-product-properties') or ''
                        try:
                            idx_number = str(json.loads(product_prop).get('idx', '')).strip()
                        except Exception:
                            idx_number = ''

                        if not idx_number:
                            continue

                        if idx_number in idx_number_list:
                            self.log_signal_func(f"[중복] {idx_number} 중복 -> 다음 카테고리로 넘어감")
                            stop = True
                            break

                        idx_number_list.add(idx_number)


                        headers_oms = {
                            "authority": "coco-label.com",
                            "method": "GET",
                            "path": "/ajax/oms/OMS_get_products.cm",
                            "scheme": "https",

                            "accept": "*/*",
                            "accept-encoding": "gzip, deflate, br, zstd",
                            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",

                            "priority": "u=1, i",
                            "referer": f"https://coco-label.com{base_obj['href']}/?idx={idx_number}",

                            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                            "sec-ch-ua-mobile": "?0",
                            "sec-ch-ua-platform": '"Windows"',

                            "sec-fetch-dest": "empty",
                            "sec-fetch-mode": "cors",
                            "sec-fetch-site": "same-origin",

                            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                        }

                        # ✅ 상세 JSON
                        detail_url = f"{self.shop_url}/ajax/oms/OMS_get_product.cm?prod_idx={idx_number}"
                        detail_text = self.api_client.get(url=detail_url, headers=headers_oms)

                        try:
                            data = detail_text.get('data', {})
                        except Exception as e:
                            self.log_signal_func(f"[에러] detail json 파싱 실패: idx={idx_number} / {e}")
                            continue

                        name = data.get('name', '')
                        price = data.get('price', '')
                        price_org = data.get('price_org', '')
                        brand = data.get('brand', '')

                        self.log_signal_func(f"[{category_name}] 크롤링중: {idx_number} / {brand} / {name}")

                        # =========================
                        # 이미지 저장(썸네일 + 상세)
                        # =========================
                        brand_dir = f"{brand}_images" if brand else "NO_BRAND_images"
                        product_dir = f"{idx_number}_images"

                        thumb_excel_link = ''
                        images = data.get('images') or []
                        image_url = data.get('image_url') or {}

                        if images:
                            first_code = images[0]
                            thumb_link = image_url.get(first_code, '')
                            if thumb_link:
                                thumb_paths = self.download_images([thumb_link], brand_dir, product_dir, idx_number, 1)
                                if thumb_paths:
                                    thumb_excel_link = thumb_paths[0]

                        # 상세 이미지 링크들
                        content_html = data.get('content') or ''
                        content_soup = BeautifulSoup(content_html, 'html.parser')
                        detail_img_links = []
                        for img in content_soup.find_all('img'):
                            src = img.get('src')
                            if src:
                                detail_img_links.append(src)

                        detail_img_paths = []
                        if detail_img_links:
                            detail_img_paths = self.download_images(detail_img_links, brand_dir, product_dir, idx_number, 2)

                        img_html = []
                        for p in detail_img_paths:
                            img_html.append(f'<img src="https://plena.kr/data/item/{p}">')
                        final_img_html = "".join(img_html)

                        # =========================
                        # 옵션
                        # =========================
                        value_map = {}
                        for opt in (data.get('options') or []):
                            value_list = opt.get('value_list') or {}
                            for k, v in value_list.items():
                                value_map[k] = v

                        combined_options_list = []

                        if data.get('options_detail'):
                            for detail in (data.get('options_detail') or []):
                                codes = detail.get('value_code_list') or []
                                temp = ""
                                for c in codes:
                                    if c in value_map:
                                        temp += str(value_map[c]).replace(" ", "")
                                if temp:
                                    combined_options_list.append(temp)

                            final_option_content = ",".join(combined_options_list)
                        else:
                            final_option_content = str(data.get('simple_content_plain', '')).replace(" ", "")

                        # =========================
                        # ✅ base_obj 복사해서 값 채우기
                        # =========================
                        row = dict(base_obj)  # shallow copy

                        row['상품코드'] = idx_number
                        row['상품명'] = name
                        row['브랜드'] = brand
                        row['시중가격'] = price_org
                        row['판매가격'] = price
                        row['상품설명'] = final_img_html
                        row['모바일상품설명'] = final_img_html
                        row['이미지1'] = thumb_excel_link
                        row['옵션'] = final_option_content

                        self.result.append(row)

                        # 필요하면 즉시 CSV 저장 (원하면 켜줄게)
                        self.excel_driver.append_to_csv(self.excel_filename, self.result, self.columns)

                self.log_signal_func(f"[완료] {category_name} 처리 끝. 수집={len(idx_number_list)}")


    def download_images(self, image_links, brand_dir, product_dir, idx_number, t):
        # root/src/workers/main/api_coco_label_set_worker.py 기준 -> root/image
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        base_main_dir = os.path.join(root_dir, "image")

        target_full_path = os.path.join(base_main_dir, brand_dir, product_dir)
        if not os.path.exists(target_full_path):
            os.makedirs(target_full_path, exist_ok=True)

        result_paths = []

        parent_dir = os.path.basename(os.path.normpath(brand_dir))
        second_parent_dir = os.path.basename(os.path.normpath(product_dir))

        # 썸네일 이미지
        if t == 1:
            for url in image_links:
                try:
                    r = requests.get(url, timeout=40)
                    if r.status_code != 200:
                        continue

                    img = Image.open(BytesIO(r.content))
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    file_name = f"{idx_number}.jpg"
                    save_path = os.path.join(target_full_path, file_name)
                    img.save(save_path, "JPEG", quality=100, subsampling=0)

                    short_path = f"{parent_dir}/{second_parent_dir}/{file_name}"
                    result_paths.append(short_path)

                except Exception as e:
                    self.log_signal_func(f"[이미지에러] thumb idx={idx_number} url={url} err={e}")

            return result_paths

        # 상세 이미지
        for i, url in enumerate(image_links):
            try:
                r = requests.get(url, timeout=20)
                if r.status_code != 200:
                    continue

                img = Image.open(BytesIO(r.content))
                if img.mode != "RGB":
                    img = img.convert("RGB")

                file_name = f"{idx_number}_{i}.jpg"
                save_path = os.path.join(target_full_path, file_name)
                img.save(save_path, "JPEG", quality=100, subsampling=0)

                short_path = f"{parent_dir}/{second_parent_dir}/{file_name}"
                result_paths.append(short_path)

            except Exception as e:
                self.log_signal_func(f"[이미지에러] detail idx={idx_number} url={url} err={e}")

        return result_paths


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
        self.excel_driver.convert_csv_to_excel_and_delete(self.excel_filename)
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        if self.running:
            self.progress_end_signal.emit()

    # 정지
    def stop(self):
        self.running = False

