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


class Api1004yaSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()

        self.columns = None
        self.csv_filename = None
        self.site_name = "1004ya"
        self.site_url = "https://www.1004ya.net"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.sess = None
        self.api_client = None
        self.saved_ids = set()
        self.base_url = "https://www.1004ya.net/bbs/board.php?bo_table=b49&bannertab2=76%4096%40" # 전국
        self.detail_url = "https://www.1004ya.net/bbs/board.php?bo_table=b49" # 상세

    # 초기화
    def init(self):
        self.driver_set()
        return True


    # 프로그램 실행
    def main(self):
        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.columns = ["SHOP_ID", "SHOP_NAME", "SHOP_PHONE", "TITLE", "LATITUDE", "LONGITUDE", "ADDR_JIBUN", "ADDR_ROAD", "ADDR_EXTRA", "SHOP_INTRO"]

        df = pd.DataFrame(columns=self.columns)
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")
        self.total_pages = self.get_total_page()
        self.total_cnt = self.total_pages * 30
        self.log_signal_func(f"전체 페이지 수 : {self.total_pages}")
        self.get_shop_list()
        return True


    def get_shop_list(self):
        result_list = []
        try:
            for page in range(1, self.total_pages+1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                shop_ids = self.get_shop_ids(page)

                if len(shop_ids) == 0:
                    break

                for i, shop_id in enumerate(shop_ids, start=1):
                    if not self.running:  # 실행 상태 확인
                        self.log_signal_func("크롤링이 중지되었습니다.")
                        break
                    obj = self.get_detail(shop_id)
                    result_list.append(obj)
                    self.current_cnt += 1
                    self.log_signal_func(f"현재 ID({shop_id}): Page {page} / {self.total_pages}, Shop : {i}/{len(shop_ids)}")
                    self.log_signal_func(f"SHOP_NAME : {obj['SHOP_NAME']}, SHOP_PHONE : {obj['SHOP_PHONE']}")
                    pro_value = (self.current_cnt / self.total_cnt) * 1000000
                    self.progress_signal.emit(self.before_pro_value, pro_value)
                    self.before_pro_value = pro_value

                self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns)

        except Exception as e:
            self.log_signal_func(f"❌ 키워드 추출 중 오류 발생: {e}")


    def get_total_page(self):
        url = f"{self.base_url}&page=1"

        headers = {
            "authority": "www.1004ya.net",
            "method": "GET",
            "path": "/bbs/board.php?bo_table=b49&bannertab2=76%4096%40&page=1",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "priority": "u=0, i",
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

        last_page = 0

        try:
            res = self.api_client.get(url=url, headers=headers)
            if not res:
                return last_page

            soup = BeautifulSoup(res, 'html.parser')

            # 1. <nobr>맨끝</nobr> 태그 찾기
            nobr_tag = soup.find('nobr', string='맨끝')

            if nobr_tag:
                # 2. 부모 <a> 태그 가져오기
                parent_a = nobr_tag.find_parent('a')
                if parent_a and 'href' in parent_a.attrs:
                    href = parent_a['href']
                    # 3. href 안의 모든 page=숫자 추출
                    page_numbers = re.findall(r'page=(\d+)', href)
                    if page_numbers:
                        last_page = int(page_numbers[-1])  # 마지막 page 값
                        self.log_signal_func(f"맨끝 페이지 번호:{last_page}")
                    else:
                        self.log_signal_func("page=숫자 형식이 href에 없습니다.")
                else:
                    self.log_signal_func("<a> 태그가 없습니다.")
            else:
                self.log_signal_func("<nobr>맨끝</nobr> 태그를 찾을 수 없습니다.")

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_category_count 실패: {e}")
        return last_page


    def get_shop_ids(self, page):
        url = f"{self.base_url}&page={page}"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        shop_ids = []
        try:
            res = self.api_client.get(url=url, headers=headers)
            if not res:
                return shop_ids

            soup = BeautifulSoup(res, "html.parser")
            tr_tags = soup.find_all('tr', class_='class_list_tr')

            for tr in tr_tags:
                tr_id = tr.get('id', '')
                match = re.search(r'list_tr_(\d+)', tr_id)
                if match:
                    shop_ids.append(int(match.group(1)))  # 숫자로 변환해 저장 (문자열로 원하면 str로 유지)

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_search_results 실패: {e}")

        return shop_ids


    def get_detail(self, shop_id):
        url = f"{self.detail_url}&wr_id={shop_id}"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        obj = {
            "SHOP_ID": shop_id,
            "SHOP_NAME": "",
            "SHOP_PHONE": "",
            "TITLE": "",
            "LATITUDE": "",
            "LONGITUDE": "",
            "ADDR_JIBUN": "",
            "ADDR_ROAD": "",
            "ADDR_EXTRA": "",
            "SHOP_INTRO": ""
        }

        try:
            res = self.api_client.get(url=url, headers=headers)
            if res:
                soup = BeautifulSoup(res, "html.parser")

                subject = soup.find('td', class_='mw_basic_view_subject')
                h1_tag = subject.find('h1') if subject else None
                obj['TITLE'] = h1_tag.get_text(strip=True) if h1_tag else ''

                head = soup.find('tbody', class_='view_head_display')
                a_tag = head.find('a') if head else None
                obj['SHOP_NAME'] = a_tag.get_text(strip=True) if a_tag else ''

                tel = soup.find('span', class_='tel_01_pc')
                raw_text = tel.get_text(strip=True) if tel else None
                obj['SHOP_PHONE'] = raw_text.replace(' ', '') if raw_text else ''

                # 📍 위도
                lat_input = soup.select_one('form[name="fwrite"] input[name="wr_56"]')
                latitude = lat_input['value'].strip() if lat_input else ''

                # 📍 경도
                lon_input = soup.select_one('form[name="fwrite"] input[name="wr_57"]')
                longitude = lon_input['value'].strip() if lon_input else ''

                # 📍 주소 파싱
                addr_input = soup.select_one('form[name="fwrite"] input[name="wr_59"]')
                addr_value = addr_input['value'].strip() if addr_input else ''

                addr_jibun = ''
                addr_road = ''
                addr_extra = ''

                if addr_value:
                    # 괄호 내부: 도로명 주소 추출
                    match = re.search(r'^(.*?)\((.*?)\)', addr_value)
                    if match:
                        addr_jibun = match.group(1).strip()
                        addr_road = match.group(2).strip()

                    # 슬래시로 위치 설명 분리
                    addr_parts = addr_value.split('/')
                    addr_extra = addr_parts[1].strip() if len(addr_parts) > 1 else ''

                div = soup.find(id="clip_board_view")
                shop_intro = div.get_text(strip=True) if div else ''

                obj['LATITUDE'] = latitude
                obj['LONGITUDE'] = longitude
                obj['ADDR_JIBUN'] = addr_jibun
                obj['ADDR_ROAD'] = addr_road
                obj['ADDR_EXTRA'] = addr_extra
                obj['SHOP_INTRO'] = shop_intro

                # 📍 상세 이미지 수집
                seen = set()
                unique_img_tags = []

                for img in soup.find_all("img", class_="sw-img"):
                    src = img.get("src", "").strip()
                    if src and src not in seen:
                        seen.add(src)
                        unique_img_tags.append(img)

                detail_images = []

                save_dir = os.path.join("images", "1004ya", str(shop_id))
                os.makedirs(save_dir, exist_ok=True)

                for idx, img in enumerate(unique_img_tags, 1):
                    src = img.get("src", "").strip()
                    alt = img.get("alt", "").strip()

                    # 상대경로면 절대경로로 보정
                    if src.startswith("/"):
                        src = self.site_url + src

                    filename = f"{str(shop_id)}_{idx}.jpg"
                    save_path = os.path.join(save_dir, filename)

                    try:
                        # 이미지 다운로드
                        img_res = requests.get(src, timeout=10)
                        if img_res.status_code == 200:
                            with open(save_path, "wb") as f:
                                f.write(img_res.content)

                            detail_images.append({
                                "src": src,
                                "alt": alt,
                                "filename": filename
                            })

                    except Exception as e:
                        self.log_signal_func(f"[이미지 에러] {src} 다운로드 실패: {e}")

                obj["DETAIL_IMAGE"] = detail_images

                return obj

        except Exception as e:
            self.log_signal_func(f"[에러] fetch_detail_result 실패: {e}")
        return obj

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

