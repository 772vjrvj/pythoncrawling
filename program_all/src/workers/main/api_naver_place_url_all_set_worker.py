import json
import random
import threading
import time
import os, re, shutil, requests
import pandas as pd
import pyautogui
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.str_utils import split_comma_keywords
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from src.utils.config import server_url  # 서버 URL 및 설정 정보

class ApiNaverPlaceUrlAllSetLoadWorker(BaseApiWorker):

    LIMIT_IMAGE_SIZE = 1000

    # 초기화
    def __init__(self):
        super().__init__()

        self.url_list = None
        self.place_cookie = None
        self.columns = None
        self.csv_filename = None
        self.cookies = None
        self.keyword_list = None
        self.site_name = "네이버 플레이스 URL"
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.sess = None
        self.api_client = None
        self.saved_ids = set()
        self.image_size = 1000
        self.zip = True

    # 초기화
    def init(self):
        self.data_set()
        self.driver_set()
        self.get_cookie()
        self.log_signal_func(f"선택 항목 : {self.columns}")
        return True

    # 프로그램 실행
    def main(self):

        try:
            self.log_signal_func(f"크롤링 시작. 전체 {len(self.url_list)}개 URL")

            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)

            df = pd.DataFrame(columns=self.columns)
            df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

            results = []
            pattern = re.compile(r"/(\d+)(?=[/?#]|$)")
            for index, url in enumerate(self.url_list, start=1):
                if not self.running:
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                match = pattern.search(url)
                if match:
                    place_id = match.group(1)

                    place_info = self.fetch_place_info(place_id)
                    if not place_info:
                        self.log_signal_func(f"⚠️ ID {place_id}의 상세 정보를 가져오지 못했습니다.")
                        continue

                    self.log_signal_func(f"진행 : {index} / {len(self.url_list)}, 아이디: {place_id}, 이름: {place_info['이름']}")
                    results.append(place_info)

                    pro_value = (index / len(self.url_list)) * 1000000
                    self.progress_signal.emit(self.before_pro_value, pro_value)
                    self.before_pro_value = pro_value

                    if index % 5 == 0:
                        self.excel_driver.append_to_csv(self.csv_filename, results, self.columns)

            self.excel_driver.append_to_csv(self.csv_filename, results, self.columns)
            pro_value = 1000000

            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

        except Exception as e:
            self.log_signal_func(f"크롤링 에러: {e}")

        return True


    # 데이터 세팅
    def data_set(self):
        value = self.get_setting_value(self.setting, "image_size")

        # 숫자인지 확인 (int 변환 시도)
        try:
            num = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"image_size 값이 올바르지 않습니다: {value}")

        # 범위 확인
        if not (1 <= num <= self.LIMIT_IMAGE_SIZE):
            raise ValueError(f"image_size는 1 ~ {self.LIMIT_IMAGE_SIZE} 사이여야 합니다 (현재 값: {num})")

        self.image_size = num
        self.zip = self.get_setting_value(self.setting, "zip")
        self.url_list = [
            str(row[k]).strip()
            for row in self.excel_data_list
            for k in row.keys()
            if k.lower() == "url" and row.get(k) and str(row[k]).strip()
        ]

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


    def build_payload(self, place_id, si=None, lc=None):
        cursors = [
            {"id":"biz"}, {"id":"clip"}, {"id":"cp0"},
            {"id":"aiView"}, {"id":"visitorReview"},
            {"id":"imgSas"}, {"id":"cp"}
        ]
        if si is not None:
            for c in cursors:
                if c["id"] == "imgSas":
                    c["startIndex"] = si
                    if lc is not None:
                        c["lastCursor"] = str(lc)
                        c["hasNext"] = True   # ✅ 이거 넣는 게 안정적
                    break
        return [{
            "operationName": "getPhotoViewerItems",
            "variables": {
                "input": {
                    "businessId": place_id,
                    "businessType": "place",
                    "cursors": cursors,
                    "excludeAuthorIds": [],
                    "excludeSection": [],
                    "excludeClipIds": [],
                    "dateRange": ""
                }
            },
            "query": "query getPhotoViewerItems($input: PhotoViewerInput) {\n  photoViewer(input: $input) {\n    cursors { id startIndex hasNext lastCursor __typename }\n    photos { viewId originalUrl originalDate width height title text desc link date photoType mediaType option { channelName dateString playCount likeCount __typename } to relation logId author { id nickname from imageUrl objectId url borderImageUrl __typename } votedKeywords { code iconUrl iconCode name __typename } visitCount originType isFollowing businessName rating externalLink { title url __typename } sourceTitle moment { channelId contentId momentId gdid blogRelation statAllowYn category docNo __typename } video { videoId videoUrl trailerUrl __typename } music { artists title __typename } clip { serviceType createdAt __typename } __typename }\n    __typename\n  }\n}"
        }]


    # 이미지 다운로드
    def fetch_place_image(self, place_id, name):
        url = "https://api.place.naver.com/place/graphql"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko",
            "content-type": "application/json",
            "referer": f"https://m.place.naver.com/place/{place_id}/photo",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        }

        parts_all = []
        for si, lc in [(None, None), (40, "41"), (60, "61"), (80, "81"), (100, "101")]:
            parts = self.api_client.post(url=url, headers=headers, json=self.build_payload(place_id, si, lc))
            self.log_signal_func(f"이미지 다운로드 {place_id} {si} 호출")
            parts_all.extend(parts)
            time.sleep(random.uniform(.5, 1))

        # photos 모으기
        photos = []
        for part in parts_all:
            pv = part["data"].get("photoViewer")
            if pv:
                photos.extend(pv.get("photos", []))

        # URL 문자열 리스트
        image_url_list = []
        seen = set()
        for p in photos:
            u = p.get("originalUrl")
            if u and u not in seen:
                seen.add(u)
                image_url_list.append(u)

        # 저장 폴더
        safe_name = re.sub(r'[\\/:*?"<>|]+', "_", str(name))
        folder_name = f"{safe_name}({place_id})"
        folder = os.path.join("images", folder_name)
        os.makedirs(folder, exist_ok=True)

        # 용량 제한
        limit_mb = int(getattr(self, "image_size", self.image_size))
        if limit_mb < 1 or limit_mb > self.LIMIT_IMAGE_SIZE:
            raise ValueError(f"image_size는 1 ~ {self.LIMIT_IMAGE_SIZE} 사이여야 합니다.")
        limit_bytes = limit_mb * 1024 * 1024

        # 다운로드
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        total = 0

        for idx, img_url in enumerate(image_url_list, 1):
            path = urlparse(img_url).path
            ext = os.path.splitext(path)[1].lower()
            if not ext or len(ext) > 5:
                ext = ".jpg"
            fname = f"{folder_name}_{idx}{ext}"
            fpath = os.path.join(folder, fname)

            with requests.get(img_url, stream=True, headers={"user-agent": ua}, timeout=20) as r:
                r.raise_for_status()
                cl = r.headers.get("Content-Length")
                if cl:
                    cl = int(cl)
                    if total + cl > limit_bytes:
                        break  # 이 파일부터 한도 초과 → 저장 안 하고 종료

                written = 0
                with open(fpath, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if not chunk:
                            continue
                        if not cl and total + written + len(chunk) > limit_bytes:
                            f.close()
                            try: os.remove(fpath)
                            except Exception: pass
                            # 한도 도달 → 압축만 진행하고 반환
                            break
                        f.write(chunk)
                        written += len(chunk)

            total += written
            if total >= limit_bytes:
                break

        # 마지막: ZIP 압축 (images/{safe_name}({place_id}).zip)
        if self.zip:
            base = os.path.join("images", folder_name)
            try:
                zip_path = shutil.make_archive(base, "zip", root_dir="images", base_dir=folder_name)
                self.log_signal_func(f"압축 완료: {zip_path}")
            except Exception as e:
                self.log_signal_func(f"압축 실패: {e}")

        return image_url_list


    # 상세조회
    def fetch_place_info(self, place_id):
        url = f"https://m.place.naver.com/place/{place_id}"
        try:
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
                'referer': f"{url}",
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

            image_url_list = self.fetch_place_image(place_id, name)

            result = {
                "아이디": place_id,
                "이름": name,
                "이미지" : image_url_list,
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
                "URL": url,
                "지도": f"https://map.naver.com/p/entry/place/{place_id}",
                "편의시설": ', '.join(conveniences) if conveniences else '',
                "가상번호": virtualPhone,
                "전화번호": phone,
                "사이트": urls,
                "주소지정보": road,
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

