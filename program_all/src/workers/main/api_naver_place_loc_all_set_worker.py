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
        self.site_name = "네이버 플레이스 전국"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.sess = None
        self.api_client = None
        self.loc_all = None
        self.saved_ids = set()

    # 초기화
    def init(self):
        keyword_str = self.get_setting_value(self.setting, "keyword")
        self.keyword_list = split_comma_keywords(keyword_str)
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

        if self.region:
            self.loc_all_keyword_list()
        else:
            self.only_keywords_keyword_list()
        return True

    # 전국 키워드 조회
    def loc_all_keyword_list(self):
        loc_all_len = len(self.region)
        keyword_list_len = len(self.keyword_list)
        self.total_cnt = loc_all_len * keyword_list_len * 300
        self.total_pages = loc_all_len * keyword_list_len * 15

        self.log_signal_func(f"예상 전체 수 {self.total_cnt} 개")
        self.log_signal_func(f"예상 전체 페이지수 {self.total_pages} 개")

        for index, loc in enumerate(self.region, start=1):
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
            result_ids = []

            while True:
                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                time.sleep(random.uniform(1, 2))

                result = self.fetch_search_results(query, page)
                if not result:
                    break
                result_ids.extend(result)
                self.log_signal_func(f"전국: {locs_index} / {total_locs}, 키워드: {current_query_index} / {total_queries}, 검색어: {query}, 페이지: {page}")
                self.log_signal_func(f"목록: {result}")
                page += 1

            new_ids = list(dict.fromkeys(result_ids))

            results = []

            for idx, place_id in enumerate(new_ids, start=1):
                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                if place_id in self.saved_ids:
                    self.log_signal_func(f"전국: {locs_index} / {total_locs}, 키워드: {current_query_index} / {total_queries}, 검색어: {query}, 수집: {idx} / {len(new_ids)}, 중복 아이디: {place_id}")
                    continue  # ✅ 이미 수집한 ID는 건너뜀

                time.sleep(random.uniform(2, 4))

                place_info = self.fetch_place_info(place_id)
                if not place_info:
                    self.log_signal_func(f"⚠️ ID {place_id}의 상세 정보를 가져오지 못했습니다.")
                    continue

                self.log_signal_func(f"전국: {locs_index} / {total_locs}, 키워드: {current_query_index} / {total_queries}, 검색어: {query}, 수집: {idx} / {len(new_ids)}, 아이디: {place_id}, 이름: {place_info['이름']}")
                results.append(place_info)

            self.saved_ids.update(new_ids)
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
        self.log_signal_func(f"전체 항목 수 {self.total_cnt} 개")
        self.log_signal_func(f"전체 페이지 수 {self.total_pages} 개")

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
            time.sleep(random.uniform(1, 2))

        if result_list:
            self.excel_driver.append_to_csv(self.csv_filename, result_list, self.columns)

    # 드라이버 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)
        self.loc_all = self.file_driver.read_json_array_from_resources("naver_loc_all.json")

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
            page_all = 0
            result_ids = []

            for index, keyword in enumerate(self.keyword_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                page = 1
                while True:
                    if not self.running:
                        self.log_signal_func("크롤링이 중지되었습니다.")
                        break
                    time.sleep(random.uniform(1, 2))

                    self.log_signal_func(f"전체 {index}/{len(self.keyword_list)}, keyword: {keyword}, page: {page}")

                    result = self.fetch_search_results(keyword, page)
                    if not result:
                        break
                    result_ids.extend(result)

                    page += 1
                    page_all += 1

            all_ids_list = list(dict.fromkeys(result_ids))
            self.log_signal_func(f"전체 : {all_ids_list}")
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
        url = "https://pcmap-api.place.naver.com/graphql"

        headers = {
            "method": "POST",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko",
            "content-type": "application/json",
            # "cookie": self.place_cookie,
            "referer": "https://pcmap.place.naver.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }
        payload = [{
            "operationName": "getPlacesList",
            "variables": {
                "useReverseGeocode": True,
                "input": {
                    "query": keyword,
                    "start": (page - 1) * 100 + 1,
                    "display": 100,
                    "adult": True,
                    "spq": True,
                    "queryRank": "",
                    "x": "",
                    "y": "",
                    "clientX": "",
                    "clientY": "",
                    "deviceType": "pcmap",
                    "bounds": ""
                },
                "isNmap": True,
                "isBounds": True,
                "reverseGeocodingInput": {
                    "x": "",
                    "y": ""
                }
            },
            "query": "query getPlacesList($input: PlacesInput, $isNmap: Boolean!, $isBounds: Boolean!, $reverseGeocodingInput: ReverseGeocodingInput, $useReverseGeocode: Boolean = false) {  businesses: places(input: $input) {    total    items {      id      name      normalizedName      category      cid      detailCid {        c0        c1        c2        c3        __typename      }      categoryCodeList      dbType      distance      roadAddress      address      fullAddress      commonAddress      bookingUrl      phone      virtualPhone      businessHours      daysOff      imageUrl      imageCount      x      y      poiInfo {        polyline {          shapeKey {            id            name            version            __typename          }          boundary {            minX            minY            maxX            maxY            __typename          }          details {            totalDistance            arrivalAddress            departureAddress            __typename          }          __typename        }        polygon {          shapeKey {            id            name            version            __typename          }          boundary {            minX            minY            maxX            maxY            __typename          }          __typename        }        __typename      }      subwayId      markerId @include(if: $isNmap)      markerLabel @include(if: $isNmap) {        text        style        stylePreset        __typename      }      imageMarker @include(if: $isNmap) {        marker        markerSelected        __typename      }      oilPrice @include(if: $isNmap) {        gasoline        diesel        lpg        __typename      }      isPublicGas      isDelivery      isTableOrder      isPreOrder      isTakeOut      isCvsDelivery      hasBooking      naverBookingCategory      bookingDisplayName      bookingBusinessId      bookingVisitId      bookingPickupId      baemin {        businessHours {          deliveryTime {            start            end            __typename          }          closeDate {            start            end            __typename          }          temporaryCloseDate {            start            end            __typename          }          __typename        }        __typename      }      yogiyo {        businessHours {          actualDeliveryTime {            start            end            __typename          }          bizHours {            start            end            __typename          }          __typename        }        __typename      }      isPollingStation      hasNPay      talktalkUrl      visitorReviewCount      visitorReviewScore      blogCafeReviewCount      bookingReviewCount      streetPanorama {        id        pan        tilt        lat        lon        __typename      }      naverBookingHubId      bookingHubUrl      bookingHubButtonName      newOpening      newBusinessHours {        status        description        dayOff        dayOffDescription        __typename      }      coupon {        total        promotions {          promotionSeq          couponSeq          conditionType          image {            url            __typename          }          title          description          type          couponUseType          __typename        }        __typename      }      mid      hasMobilePhoneNumber      hiking {        distance        startName        endName        __typename      }      __typename    }    optionsForMap @include(if: $isBounds) {      ...OptionsForMap      displayCorrectAnswer      correctAnswerPlaceId      __typename    }    searchGuide {      queryResults {        regions {          displayTitle          query          region {            rcode            __typename          }          __typename        }        isBusinessName        __typename      }      queryIndex      types      __typename    }    queryString    siteSort    __typename  }  reverseGeocodingAddr(input: $reverseGeocodingInput) @include(if: $useReverseGeocode) {    ...ReverseGeocodingAddr    __typename  }}fragment OptionsForMap on OptionsForMap {  maxZoom  minZoom  includeMyLocation  maxIncludePoiCount  center  spotId  keepMapBounds  __typename}fragment ReverseGeocodingAddr on ReverseGeocodingResult {  rcode  region  __typename}"
        }]

        try:
            res = self.api_client.post(url=url, headers=headers, json=payload)
            if not isinstance(res, list) or not res or not isinstance(res[0], dict):
                return []

            items = res[0].get("data", {}).get("businesses", {}).get("items", [])
            if not isinstance(items, list):
                return []

            return [item.get("id") for item in items if isinstance(item, dict) and item.get("id")]
        except Exception as e:
            self.log_signal_func(f"[에러] fetch_search_results 실패: {e}")
            return []
    
    # 숫자 체크
    def clean_number(self, value):
        try:
            num = float(value)
            return "" if num == 0 else num
        except (ValueError, TypeError):
            return ""

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
                'referer': f"https://m.place.naver.com/place/{place_id}",
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }

            response = self.api_client.get(url=url, headers=headers)

            if not response:
                self.log_signal_func(f"⚠️ Place ID {place_id} 응답 없음.")
                return None

            soup = BeautifulSoup(response, 'html.parser')
            script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))

            if not script_tag or not script_tag.string:
                self.log_signal_func(f"⚠️ Place ID {place_id}의 스크립트 태그 없음 또는 비어 있음.")
                return None

            match = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
            if not match:
                self.log_signal_func(f"⚠️ Place ID {place_id}의 JSON 파싱 실패.")
                return None

            try:
                data = json.loads(match.group(1))
            except Exception as e:
                self.log_signal_func(f"⚠️ Place ID {place_id} JSON decode 실패: {e}")
                return None

            if not isinstance(data, dict):
                self.log_signal_func(f"⚠️ Place ID {place_id} data가 dict가 아님: {type(data)}")
                return None

            # 기본 정보 추출
            base = data.get(f"PlaceDetailBase:{place_id}", {})
            name = base.get("name", "")
            road = base.get("road", "")
            address = base.get("address", "")
            roadAddress = base.get("roadAddress", "")
            category = base.get("category", "")
            conveniences = base.get("conveniences", [])
            phone = base.get("phone", "")
            virtualPhone = base.get("virtualPhone", "")

            # 방문자 리뷰 정보
            review_stats = data.get(f"VisitorReviewStatsResult:{place_id}", {})
            review = review_stats.get("review", {}) or {}
            analysis = review_stats.get("analysis", {}) or {}

            visitorReviewsScore = self.clean_number(review.get("avgRating", ""))
            visitorReviewsTotal = self.clean_number(review.get("totalCount", ""))
            voted_keyword = analysis.get("votedKeyword") or {}
            fsasReviewsTotal = self.clean_number(voted_keyword.get("userCount", ""))

            # 영업시간 정보
            root_query = data.get("ROOT_QUERY", {})
            place_detail_key = f'placeDetail({{"input":{{"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

            if place_detail_key not in root_query:
                place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

            business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"shopWindow\"]})", [])
            if not business_hours:
                business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"jto\",\"shopWindow\"]})", [])

            new_business_hours_json = root_query.get(place_detail_key, {}).get("newBusinessHours", [])
            if not new_business_hours_json:
                new_business_hours_json = root_query.get(place_detail_key, {}).get("newBusinessHours({\"format\":\"restaurant\"})", [])

            # 사이트 URL 정보
            urls = []
            homepages = root_query.get(place_detail_key, {}).get('shopWindow', {}).get("homepages", "")
            if homepages:
                for item in homepages.get("etc", []):
                    urls.append(item.get("url", ""))
                repr_data = homepages.get("repr")
                if repr_data:
                    repr_url = repr_data.get("url", "")
                    if repr_url:
                        urls.append(repr_url)

            # 카테고리 분리
            category_list = category.split(',') if category else ["", ""]
            main_category = category_list[0] if len(category_list) > 0 else ""
            sub_category = category_list[1] if len(category_list) > 1 else ""

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
                "이용시간1": self.format_new_business_hours(new_business_hours_json),
                "이용시간2": self.format_business_hours(business_hours),
                "카테고리": category,
                "URL": f"https://m.place.naver.com/place/{place_id}/home",
                "지도": f"https://map.naver.com/p/entry/place/{place_id}",
                "편의시설": ', '.join(conveniences) if conveniences else '',
                "가상번호": virtualPhone,
                "전화번호": phone,
                "사이트": urls,
                "주소지정보": road
            }

            return result

        except requests.exceptions.RequestException as e:
            self.log_signal_func(f"❌ 네트워크 에러: Place ID {place_id}: {e}")
        except Exception as e:
            self.log_signal_func(f"❌ 처리 중 에러: Place ID {place_id}: {e}")

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

