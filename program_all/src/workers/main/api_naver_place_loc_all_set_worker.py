import json
import random
import re
import threading
import time
from urllib.parse import urlparse, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from bs4 import BeautifulSoup

from src.utils.config import NAVER_LOC_ALL
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url  # 서버 URL 및 설정 정보


class ApiNaverPlaceLocAllSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()

        self.place_cookie = None
        self.columns = None
        self.csv_filename = None
        self.cookies = None
        self.keyword_list = None
        self.checked = None
        self.site_name = "네이버 플레이스 전국"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.sess = None
        self.before_pro_value = 0
        self.api_client = None
        self.loc_all = NAVER_LOC_ALL
        self.saved_ids = set()

    # 초기화
    def init(self):
        keyword_str = self.get_setting_value(self.setting, "keyword")
        self.keyword_list = split_comma_keywords(keyword_str)
        self.checked = self.get_setting_value(self.setting, "loc_all")
        self.driver_set()
        self.get_cookie()
        self.log_signal_func(f"선택 항목 : {self.columns}")
        return True

    # 프로그램 실행
    def main(self):

        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 수 계산을 시작합니다. 잠시만 기다려주세요.")

        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)

        df = pd.DataFrame(columns=self.columns)
        df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

        if self.checked:
            self.loc_all_keyword_list()
        else:
            self.only_keywords_keyword_list()
        return True

    # 전국 키워드 조회
    def loc_all_keyword_list(self):

        loc_all_len = len(self.loc_all)
        keyword_list_len = len(self.keyword_list)
        self.total_cnt = loc_all_len * keyword_list_len * 300
        self.total_pages = loc_all_len * keyword_list_len * 15

        self.log_signal_func(f"예상 전체 업체수 {self.total_cnt} 개")
        self.log_signal_func(f"예상 전체 페이지수 {self.total_pages} 개")

        for index, loc in enumerate(self.loc_all, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            name = f'{loc["시도"]} {loc["시군구"]} {loc["읍면동"]} '

            for idx, query in enumerate(self.keyword_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                full_name = name + query
                self.log_signal_func(f"전국: {index} / {loc_all_len}, 키워드: {idx} / {keyword_list_len}, 검색어: {full_name}")
                self.loc_all_keyword_list_detail(full_name, keyword_list_len, idx, loc_all_len, index)

    # 전국 상세
    def loc_all_keyword_list_detail(self, query, total_queries, current_query_index, total_locs, locs_index):
        try:
            page = 1
            results = []

            # 새롭게 등장한 아이디 모음
            current_ids = set()

            while True:
                time.sleep(random.uniform(2, 4))

                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                result = self.fetch_search_results(query, page)
                if not isinstance(result, dict):
                    self.log_signal_func(f"API 응답 오류 또는 형식 이상: {type(result)} → {result}")
                    break

                place_section = result.get("result", {})
                if not isinstance(place_section, dict):
                    self.log_signal_func(f"'result' 데이터 없음")
                    break

                place_data = place_section.get("place", {})
                if not isinstance(place_data, dict):
                    self.log_signal_func(f"'place' 데이터 없음")
                    break

                place_list = place_data.get("list", [])
                if not isinstance(place_list, list):
                    self.log_signal_func(f"'list' 데이터 없음")
                    break

                ids_this_page = {place.get("id") for place in place_list if isinstance(place, dict) and place.get("id")}

                self.log_signal_func(f"전국: {locs_index} / {total_locs}, 키워드: {current_query_index} / {total_queries}, 검색어: {query}, 페이지: {page}")
                self.log_signal_func(f"목록: {ids_this_page}")

                if not ids_this_page:
                    break

                current_ids.update(ids_this_page)
                page += 1

            # 누적된 전체 ID에서 새롭게 등장한 ID만 필터링
            new_ids = current_ids - self.saved_ids  # ← 핵심 차집합
            self.saved_ids.update(new_ids)  # 누적

            for idx, place_id in enumerate(new_ids, start=1):
                time.sleep(random.uniform(2, 4))

                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                place_info = self.fetch_place_info(place_id)
                if not place_info:
                    self.log_signal_func(f"⚠️ ID {place_id}의 상세 정보를 가져오지 못했습니다.")
                    continue

                self.log_signal_func(f"전국: {locs_index} / {total_locs}, 키워드: {current_query_index} / {total_queries}, 검색어: {query}, 수집: {idx} / {len(new_ids)}, 아이디: {place_id}, 이름: {place_info['이름']}")
                results.append(place_info)

            # 새 항목만 CSV에 저장
            self.excel_driver.append_to_csv(self.csv_filename, results, self.columns)

            self.current_cnt = locs_index * current_query_index * 300
            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

        except Exception as e:
            self.log_signal_func(f"loc_all_keyword_list_detail 크롤링 에러: {e}")


    # 키워드만 조회
    def only_keywords_keyword_list(self):
        result_list = []
        all_ids_list = self.total_cnt_cal()
        self.log_signal_func(f"전체 업체수 {self.total_cnt} 개")
        self.log_signal_func(f"전체 페이지수 {self.total_pages} 개")

        for index, place_id in enumerate(all_ids_list, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            obj = self.fetch_place_info(place_id)
            result_list.append(obj)
            if index % 5 == 0:
                self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns)

            self.current_cnt = self.current_cnt + 1
            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

            self.log_signal_func(f"현재 페이지 {self.current_cnt}/{self.total_cnt} : {obj}")
            time.sleep(random.uniform(2, 3))

        if result_list:
            self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns)

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

    # 전체 갯수 조회
    def total_cnt_cal(self):
        try:

            all_ids = set()
            page_all = 0
            for index, keyword in enumerate(self.keyword_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                page = 1
                self.log_signal_func(f"키워드 {index}/{len(self.keyword_list)}: {keyword}")

                # 키워드에 매핑되는 아이디 수집
                while True:
                    time.sleep(random.uniform(1, 2))

                    if not self.running:  # 실행 상태 확인
                        self.log_signal_func("크롤링이 중지되었습니다.")
                        break

                    result = self.fetch_search_results(keyword, page)
                    if not isinstance(result, dict):
                        self.log_signal_func(f"API 응답 오류 또는 형식 이상: {type(result)} → {result}")
                        break

                    place_section = result.get("result", {})
                    if not isinstance(place_section, dict):
                        self.log_signal_func(f"'result' 데이터 없음")
                        break

                    place_data = place_section.get("place", {})
                    if not isinstance(place_data, dict):
                        self.log_signal_func(f"'place' 데이터 없음")
                        break

                    place_list = place_data.get("list", [])
                    if not isinstance(place_list, list):
                        self.log_signal_func(f"'list' 데이터 없음")
                        break

                    ids_this_page = [place.get("id") for place in place_list if isinstance(place, dict) and place.get("id")]
                    self.log_signal_func(f"목록: {ids_this_page}")

                    if not ids_this_page:
                        break

                    all_ids.update(ids_this_page)
                    page += 1
                    page_all += 1

            all_ids_list = list(all_ids)
            self.total_cnt = len(all_ids_list)
            self.total_pages = page_all
            return all_ids_list

        except Exception as e:
            self.log_signal_func(f"Error calculating total count: {e}")
            return None

    # 쿠키
    def get_cookie(self):
        name = 'place'
        url = f"{server_url}/place-cookie/select/{name}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        place_cookie = self.api_client.get(url=url, headers=headers)

        if place_cookie:
            cookie_value = place_cookie.get("cookie")
            if cookie_value:
                self.place_cookie = cookie_value
            else:
                self.log_func("❌ 쿠키 값이 없습니다.")
        else:
            self.log_func("❌ place_cookie 조회 실패")


        # 목록조회
        
    # 플레이스 목록
    def fetch_search_results(self, keyword, page):
        url = f"https://map.naver.com/p/api/search/allSearch?query={keyword}&type=all&searchCoord=&boundary=&page={page}"
        headers = {
            'Referer': 'https://map.naver.com/p/search',  # ✅ 반드시 필요
            'Cookie': self.place_cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }
        response = self.api_client.get(url=url, headers=headers)
        return response

    # 상세조회
    def fetch_place_info(self, place_id):
        try:
            url = f"https://m.place.naver.com/place/{place_id}"
            headers = {
                'authority': 'm.place.naver.com',
                'method': 'GET',
                'scheme': 'https',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'priority': 'u=0, i',
                'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'referer': '',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }
            response = self.api_client.get(url=url, headers=headers)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))
    
                if script_tag:
                    json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
                    if json_text:
                        data = json.loads(json_text.group(1))
                        name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")
                        road = data.get(f"PlaceDetailBase:{place_id}", {}).get("road", "")
                        address = data.get(f"PlaceDetailBase:{place_id}", {}).get("address", "")
                        roadAddress = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")
                        category = data.get(f"PlaceDetailBase:{place_id}", {}).get("category", "")
                        conveniences = data.get(f"PlaceDetailBase:{place_id}", {}).get("conveniences", [])
                        virtualPhone = data.get(f"PlaceDetailBase:{place_id}", {}).get("virtualPhone", [])
                        visitorReviewsScore = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsScore", "")
                        visitorReviewsTotal = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsTotal", "")
    
                        root_query = data.get("ROOT_QUERY", {})
                        place_detail_key = f'placeDetail({{"input":{{"deviceType":"pc","id":"{place_id}","isNx":false}}}})'
    
                        # 기본 place_detail_key 값이 없으면 checkRedirect 포함된 key로 재시도
                        if place_detail_key not in root_query:
                            place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'
    
                        fsasReviewsTotal = root_query.get(place_detail_key, {}).get('fsasReviews', {}).get("total", "")
                        if not fsasReviewsTotal:
                            fsasReviewsTotal = root_query.get(place_detail_key, {}).get("fsasReviews({\"fsasReviewsType\":\"restaurant\"})", {}).get("total", "")
    
                        # business_hours 초기 시도
                        business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"shopWindow\"]})", [])
    
                        # business_hours 값이 없으면 다른 source를 시도
                        if not business_hours:
                            business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"jto\",\"shopWindow\"]})", [])
    
                        new_business_hours_json = root_query.get(place_detail_key, {}).get('newBusinessHours', [])
    
                        if not new_business_hours_json:
                            new_business_hours_json = root_query.get(place_detail_key, {}).get("newBusinessHours({\"format\":\"restaurant\"})", [])
    
                        # 별점, 방문자 리뷰 수, 블로그 리뷰 수가 0이거나 없으면 공백 처리
                        visitorReviewsScore = visitorReviewsScore if visitorReviewsScore and visitorReviewsScore != "0" else ""
                        visitorReviewsTotal = visitorReviewsTotal if visitorReviewsTotal and visitorReviewsTotal != "0" else ""
                        fsasReviewsTotal = fsasReviewsTotal if fsasReviewsTotal and fsasReviewsTotal != "0" else ""
    
                        # category를 대분류와 소분류로 나누기
                        category_list = category.split(',') if category else ["", ""]
                        main_category = category_list[0] if len(category_list) > 0 else ""
                        sub_category = category_list[1] if len(category_list) > 1 else ""
    
                        url = f"https://m.place.naver.com/place/{place_id}/home"
                        map_url = f"https://map.naver.com/p/entry/place/{place_id}"
    
                        urls = []
                        homepages = root_query.get(place_detail_key, {}).get('shopWindow', {}).get("homepages", "")
                        if homepages:
                            # etc 배열에서 url 가져오기
                            for item in homepages.get("etc", []):
                                urls.append(item.get("url", ""))
    
                            # repr의 url 가져오기
                            repr_data = homepages.get("repr")
                            repr_url = repr_data.get("url", "") if repr_data else ""
                            if repr_url:
                                urls.append(repr_url)
    
                        result = {
                            "아이디": place_id,
                            "이름": name,
                            "주소(지번)": address,
                            "주소(도로명)": roadAddress,
                            "대분류": main_category,
                            "소분류": sub_category,
                            "별점": visitorReviewsScore,
                            "방문자리뷰수": visitorReviewsTotal,
                            "블로그리뷰수": fsasReviewsTotal,
                            "이용시간1": self.format_business_hours(business_hours),
                            "이용시간2": self.format_new_business_hours(new_business_hours_json),
                            "카테고리": category,
                            "URL": url,
                            "지도": map_url,
                            "편의시설": ', '.join(conveniences) if conveniences else '',
                            "전화번호": virtualPhone,
                            "사이트": urls,
                            "주소지정보": road
                        }
    
                        return result

            self.current_cnt = self.current_cnt + 1
            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

        except requests.exceptions.RequestException as e:
            self.log_signal_func(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
        except Exception as e:
            self.log_signal_func(f"Error processing data for Place ID: {place_id}: {e}")
        return None

    # 영업시간 함수1
    def format_business_hours(self, business_hours):
        formatted_hours = []
        try:
            if business_hours:
                for hour in business_hours:
                    day = hour.get('day', '') or ''
                    start_time = hour.get('startTime', '') or ''
                    end_time = hour.get('endTime', '') or ''
                    if day and start_time and end_time:
                        formatted_hours.append(f"{day} {start_time} - {end_time}")
        except Exception as e:
            self.log_signal_func(f"Unexpected error: {e}")
            return ""
        return '\n'.join(formatted_hours).strip() if formatted_hours else ""

    # 영업시간 함수2
    def format_new_business_hours(self, new_business_hours):
        formatted_hours = []
        try:
            if new_business_hours:
                for item in new_business_hours:
                    status_description = item.get('businessStatusDescription', {}) or {}
                    status = status_description.get('status', '') or ''
                    description = status_description.get('description', '') or ''
    
                    if status:
                        formatted_hours.append(status)
                    if description:
                        formatted_hours.append(description)
    
                    for info in item.get('businessHours', []) or []:
                        day = info.get('day', '') or ''
                        business_hours = info.get('businessHours', {}) or {}
                        start_time = business_hours.get('start', '') or ''
                        end_time = business_hours.get('end', '') or ''
    
                        break_hours = info.get('breakHours', []) or []
                        break_times = [f"{bh.get('start', '') or ''} - {bh.get('end', '') or ''}" for bh in break_hours]
                        break_times_str = ', '.join(break_times) + ' 브레이크타임' if break_times else ''
    
                        last_order_times = info.get('lastOrderTimes', []) or []
                        last_order_times_str = ', '.join([f"{lo.get('type', '')}: {lo.get('time', '')}" for lo in last_order_times]) + ' 라스트오더' if last_order_times else ''
    
                        if day:
                            formatted_hours.append(day)
                        if start_time and end_time:
                            formatted_hours.append(f"{start_time} - {end_time}")
                        if break_times_str:
                            formatted_hours.append(break_times_str)
                        if last_order_times_str:
                            formatted_hours.append(last_order_times_str)
        except Exception as e:
            self.log_signal_func(f"영업시간 에러: {e}", "ERROR")
            return ""
        return '\n'.join(formatted_hours).strip() if formatted_hours else ""

    # 정지
    def stop(self):
        self.running = False

