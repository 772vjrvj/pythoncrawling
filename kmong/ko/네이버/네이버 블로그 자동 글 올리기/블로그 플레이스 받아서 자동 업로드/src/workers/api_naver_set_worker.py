from PyQt5.QtCore import QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
import random

# API
class ApiNaverSetLoadWorker(QThread):
    api_data_received = pyqtSignal(object)  # API 호출 결과를 전달하는 시그널

    def __init__(self, url_list, cookie, query='', parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.cookie = cookie
        self.query = query

    def run(self):
        for idx, place_id in enumerate(self.url_list, start=1):
            place_info = self.fetch_place_info(place_id)
            if place_info:
                reviews_info = self.fetch_reviews(place_id)
                place_info["리뷰"] = reviews_info.get("reviews", [])
                place_info["리뷰 분석"] = reviews_info.get("stats", [])
                place_info["공유 URL"] = self.fetch_link_url(place_id)
                place_info["블로그 제목"] = f"{self.query} / {place_info['이름']} / 운영시간 가격 주차리뷰"
                image_urls = self.fetch_photos(place_id)
                os.makedirs('place_images', exist_ok=True)
                for i, image_url in enumerate(image_urls, start=1):
                    self.download_image(image_url, f'place_images/{i}.jpg')
                place_info['이미지 URLs'] = image_urls
                place_info["블로그 게시글"] = self.print_place_info(place_info)

                self.parent.add_log(f"번호 : {idx}, 이름 : {place_info['이름']}")


                time.sleep(random.uniform(1, 2))


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
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, cookies=self.cookie)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))

                if script_tag:
                    json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
                    if json_text:
                        data = json.loads(json_text.group(1))

                        address = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")
                        name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")
                        virtualPhone = data.get(f"PlaceDetailBase:{place_id}", {}).get("virtualPhone", "")

                        prices = []
                        for key, value in data.items():
                            if key.startswith(f"Menu:{place_id}"):
                                prices.append(value)

                        facilities = []
                        for key, value in data.items():
                            if key.startswith("InformationFacilities:"):
                                facilities.append(value)


                        root_query = data.get("ROOT_QUERY", {})
                        place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                        information = root_query.get(place_detail_key, {}).get('description({"source":["shopWindow","jto"]})', "")

                        business_hours = root_query.get(place_detail_key, {}).get('businessHours({"source":["tpirates","jto","shopWindow"]})', [])

                        new_business_hours = root_query.get(place_detail_key, {}).get('newBusinessHours', [])

                        url = f"https://m.place.naver.com/place/{place_id}/home"
                        map_url = f"https://map.naver.com/p/entry/place/{place_id}"

                        result = {
                            "아이디": place_id,
                            "이름": name,
                            "주소": address,
                            "가상번호": virtualPhone,
                            "금액": prices,
                            "편의": facilities,
                            "영업시간": business_hours,
                            "새로운 영업시간": new_business_hours,
                            "정보": information,
                            "정보 URL": url,
                            "지도 URL": map_url
                        }

                        return result

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
        except Exception as e:
            print(f"Error processing data for Place ID: {place_id}: {e}")
        return None


    def fetch_reviews(self, place_id):
        try:
            url = "https://api.place.naver.com/place/graphql"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ko-KR,ko;q=0.9',
                'Origin': f'https://m.place.naver.com',
                'Referer': f'https://m.place.naver.com/place/{place_id}/home'
            }

            payload = [
                {
                    "operationName": "getVisitorReviews",
                    "variables": {
                        "input": {
                            "businessId": place_id,
                            "businessType": "place",
                            "size": 7,
                            "page": 1,
                            "includeContent": True,
                            "cidList": ["222412", "222415", "222446", "1004920"]
                        }
                    },
                    "query": """
                    query getVisitorReviews($input: VisitorReviewsInput) {
                      visitorReviews(input: $input) {
                        items {
                          id
                          rating
                          author {
                            nickname
                            imageUrl
                          }
                          body
                          created
                          tags
                          media {
                            type
                            thumbnail
                          }
                        }
                        total
                      }
                    }"""
                },
                {
                    "operationName": "getVisitorReviewStats",
                    "variables": {
                        "businessType": "place",
                        "id": place_id
                    },
                    "query": """
                    query getVisitorReviewStats($id: String, $businessType: String = "place") {
                      visitorReviewStats(input: {businessId: $id, businessType: $businessType}) {
                        id
                        name
                        review {
                          avgRating
                          totalCount
                        }
                        analysis {
                          votedKeyword {
                            totalCount
                            reviewCount
                            userCount
                            details {
                              code
                              iconUrl
                              displayName
                              count
                            }
                          }
                        }
                      }
                    }"""
                }
            ]

            response = requests.post(url, headers=headers, json=payload, cookies=self.cookie)
            response.raise_for_status()

            review_data = response.json()

            if review_data and len(review_data) > 1:
                visitor_reviews_data = review_data[0].get("data", {}).get("visitorReviews", {})
                visitor_reviews = visitor_reviews_data.get("items", []) if visitor_reviews_data else []

                analysis_data = review_data[1].get("data", {}).get("visitorReviewStats", {})
                voted_keyword_data = analysis_data.get("analysis", {}) if analysis_data else {}

                # 여기서 votedKeyword가 None일 때를 추가로 처리
                voted_keyword_details = (
                    voted_keyword_data.get("votedKeyword", {}).get("details", [])
                    if voted_keyword_data.get("votedKeyword") is not None
                    else []
                )

                return {
                    "reviews": visitor_reviews,
                    "stats": voted_keyword_details
                }
            else:
                print(f"No review data available for Place ID: {place_id}")
                return {"reviews": [], "stats": []}

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch reviews for Place ID: {place_id}. Error: {e}")
            return {"reviews": [], "stats": []}
        except Exception as e:
            print(f"Error while processing data for Place ID: {place_id}: {e}")
            return {"reviews": [], "stats": []}


    def fetch_photos(self, place_id):
        url = "https://api.place.naver.com/graphql"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Origin': 'https://m.place.naver.com',
            'Referer': f'https://m.place.naver.com/place/{place_id}/home'
        }
        payload = [
            {
                "operationName": "getPhotoViewerItems",
                "variables": {
                    "input": {
                        "businessId": place_id,
                        "businessType": "restaurant",
                        "cursors": [
                            {"id": "biz"},
                            {"id": "cp0"},
                            {"id": "visitorReview"},
                            {"id": "clip"},
                            {"id": "imgSas"}
                        ],
                        "excludeAuthorIds": [],
                        "excludeSection": [],
                        "excludeClipIds": [],
                        "dateRange": ""
                    }
                },
                "query": """
                query getPhotoViewerItems($input: PhotoViewerInput) {
                  photoViewer(input: $input) {
                    cursors {
                      id
                      startIndex
                      hasNext
                      lastCursor
                      __typename
                    }
                    photos {
                      viewId
                      originalUrl
                      width
                      height
                      title
                      text
                      desc
                      link
                      date
                      photoType
                      mediaType
                      option {
                        channelName
                        dateString
                        playCount
                        likeCount
                        __typename
                      }
                      to
                      relation
                      logId
                      author {
                        id
                        nickname
                        from
                        imageUrl
                        objectId
                        url
                        borderImageUrl
                        __typename
                      }
                      votedKeywords {
                        code
                        iconUrl
                        iconCode
                        displayName
                        __typename
                      }
                      visitCount
                      originType
                      isFollowing
                      businessName
                      rating
                      externalLink {
                        title
                        url
                        __typename
                      }
                      sourceTitle
                      moment {
                        channelId
                        contentId
                        momentId
                        gdid
                        blogRelation
                        statAllowYn
                        category
                        docNo
                        __typename
                      }
                      video {
                        videoId
                        videoUrl
                        trailerUrl
                        __typename
                      }
                      music {
                        artists
                        title
                        __typename
                      }
                      clip {
                        viewerHash
                        __typename
                      }
                      __typename
                    }
                    __typename
                  }
                }
                """
            }
        ]
        image_urls = []
        try:
            response = requests.post(url, json=payload, headers=headers, cookies=self.cookie)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            data = response.json()

            # 원하는 데이터 추출 예시 (originalUrl만 추출)
            photos = data[0].get('data', {}).get('photoViewer', {}).get('photos', [])
            for photo in photos:
                image_urls.append(photo.get('originalUrl'))

            return image_urls[:5]

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return image_urls


    def fetch_link_url(self, place_id):
        url = "https://me2do.naver.com/common/requestJsonpV2"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "me2do.naver.com",
            "referer": f"https://pcmap.place.naver.com/{place_id}/home?from=map&fromPanelNum=1&additionalHeight=76&timestamp=202410090914",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "script",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        }
        params = {
            "_callback": "window.spi_9197316230",
            "svcCode": "0022",
            "url": f"https://m.place.naver.com/share?id={place_id}&tabsPath=%2Fhome&appMode=detail"
        }
        link_url = ""
        try:
            # GET 요청 보내기
            response = requests.get(url, headers=headers, params=params, cookies=self.cookie)

            # 응답 내용에서 콜백 함수 제거 (JSON 부분만 추출하기 위해 정규 표현식 사용)
            jsonp_data = response.text
            json_data = re.search(r'window\.spi_9197316230\((.*)\)', jsonp_data).group(1)

            # 추출된 JSON 문자열을 파이썬 딕셔너리로 변환
            data = json.loads(json_data)

            # 필요한 'url' 값 출력
            print(data['result']['url'])
            link_url = data['result']['url']
            return link_url

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return link_url


    def download_image(self, image_url, save_path):
        try:
            img_data = requests.get(image_url).content
            with open(save_path, 'wb') as handler:
                handler.write(img_data)
        except Exception as e:
            print(f"Failed to download {image_url}: {e}")


    def print_place_info(self, place_info):
        try:
            # 각 항목을 포맷
            formatted_address = self.format_address(place_info.get("주소", ""))
            formatted_phone = self.format_phone_number(place_info.get("가상번호", ""), place_info.get("이름", ""))
            formatted_price = self.format_price(place_info.get("금액", []))
            formatted_facilities = self.format_facilities(place_info.get("편의", []))
            # formatted_business_hours = format_business_hours(place_info.get("영업시간", []))
            formatted_new_business_hours = self.format_new_business_hours(place_info.get("새로운 영업시간", []))
            formatted_information = self.extract_information(place_info.get("정보", []))
            formatted_reviews = self.format_review_analysis(place_info.get("리뷰 분석", []))
            map_url = place_info.get("지도", "")

            # 유효한 항목만을 리스트에 추가
            sections = [
                formatted_address,
                formatted_new_business_hours,
                # formatted_business_hours,
                formatted_phone,
                formatted_price,
                formatted_facilities,
                formatted_information,
                formatted_reviews,
                f"🗺️ 지도\n{formatted_address}" if formatted_address else ""
            ]

            # 유효한 항목을 합치고, 각 항목 사이에 3개의 엔터를 추가
            content = "\n\n\n\n".join(section for section in sections if section)

            return content.strip()  # 앞뒤 공백 제거
        except Exception:
            return ""


    def format_review_analysis(review_analysis):
        formatted_items = []
        try:
            top_items = review_analysis[:7]
            for item in top_items:
                count = item.get('count', 0)
                display_name = item.get('displayName', '')
                if count and display_name:
                    if count == 1:
                        formatted_items.append(f"- 1명의 방문자가 \"{display_name}\"라고 언급했습니다.")
                    else:
                        formatted_items.append(f"- {count}명의 방문자분들이 \"{display_name}\"라고 언급했습니다.")
        except Exception:
            return ""
        return "⭐ 방문자 후기\n" + '\n'.join(formatted_items).strip() if formatted_items else ""


    def format_address(self, address):
        try:
            return f"📍 {address}".strip() if address else ""
        except Exception:
            return ""


    def format_phone_number(self, virtual_number, name=''):
        try:
            if virtual_number:
                formatted_phone = (f"📞 전화번호\n"
                                   f"{virtual_number}\n"
                                   f"‘{name}’(으)로 연결되는 스마트콜 번호입니다.\n"
                                   f"업체 전화번호 {virtual_number}".strip())
                return formatted_phone
            return ""
        except Exception:
            return ""


    def format_price(self, prices):
        formatted_prices = []
        try:
            for price_info in prices:
                name = price_info.get('name', '')
                price = price_info.get('price', '')
                if name and price:
                    try:
                        formatted_price = f"{int(price):,}원"
                        formatted_prices.append(f"- {name} {formatted_price}")
                    except ValueError:
                        continue
        except Exception:
            return ""
        return "💵 금액\n" + '\n'.join(formatted_prices).strip() if formatted_prices else ""


    def format_facilities(self, facilities):
        try:
            facility_names = [facility.get('name', '') for facility in facilities]
            return "🏷️ 편의\n" + ', '.join(facility_names).strip() if facility_names else ""
        except Exception:
            return ""


    def format_business_hours(self, business_hours):
        formatted_hours = []
        try:
            for hour in business_hours:
                day = hour.get('day', '')
                start_time = hour.get('startTime', '')
                end_time = hour.get('endTime', '')
                if day and start_time and end_time:
                    formatted_hours.append(f"{day} {start_time} - {end_time}")
        except Exception:
            return ""
        return "⏰ 영업시간\n" + '\n'.join(formatted_hours).strip() if formatted_hours else ""


    def format_new_business_hours(self, new_business_hours):
        formatted_hours = []
        try:
            if new_business_hours:
                for item in new_business_hours:
                    status_description = item.get('businessStatusDescription', {})
                    status = status_description.get('status', '')
                    description = status_description.get('description', '')

                    if status:
                        formatted_hours.append(status)
                    if description:
                        formatted_hours.append(description)

                    for info in item.get('businessHours', []):
                        day = info.get('day', '')
                        business_hours = info.get('businessHours', {})
                        start_time = business_hours.get('start', '')
                        end_time = business_hours.get('end', '')

                        break_hours = info.get('breakHours', [])
                        break_times = [f"{bh.get('start', '')} - {bh.get('end', '')}" for bh in break_hours]
                        break_times_str = ', '.join(break_times) + ' 브레이크타임' if break_times else ''

                        if day:
                            formatted_hours.append(day)
                        if start_time and end_time:
                            formatted_hours.append(f"{start_time} - {end_time}")
                        if break_times_str:
                            formatted_hours.append(break_times_str)
        except Exception:
            return ""
        return "⏰ 영업시간\n" + '\n'.join(formatted_hours).strip() if formatted_hours else ""


    def extract_information(self, information):
        try:
            return f"ℹ️ {information}".strip() if information else ""
        except Exception:
            return ""