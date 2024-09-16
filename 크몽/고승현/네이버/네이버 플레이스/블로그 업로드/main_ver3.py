import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
import os
import pandas as pd
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import timedelta
import threading


# 전역 변수 추가
stop_event = threading.Event()
search_thread = None
time_val = 5

def fetch_search_results(query, page):
    try:
        url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Priority': 'u=0, i',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'referer': '',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch search results: {e}")
    return None


def download_image(image_url, save_path):
    try:
        img_data = requests.get(image_url).content
        with open(save_path, 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")


def fetch_reviews(place_id):
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

        response = requests.post(url, headers=headers, json=payload)
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


def fetch_place_info(place_id):
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

        response = requests.get(url, headers=headers)
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
                        "URL": url,
                        "지도": map_url
                    }

                    return result

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
    except Exception as e:
        print(f"Error processing data for Place ID: {place_id}: {e}")
    return None


def fetch_photos(place_id):
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
        response = requests.post(url, json=payload, headers=headers)
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


def extract_information(information):
    try:
        return f"ℹ️ {information}".strip() if information else ""
    except Exception:
        return ""


def format_address(address):
    try:
        return f"📍 {address}".strip() if address else ""
    except Exception:
        return ""


def format_phone_number(virtual_number, name=''):
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


def format_price(prices):
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


def format_facilities(facilities):
    try:
        facility_names = [facility.get('name', '') for facility in facilities]
        return "🏷️ 편의\n" + ', '.join(facility_names).strip() if facility_names else ""
    except Exception:
        return ""


def format_business_hours(business_hours):
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


def format_new_business_hours(new_business_hours):
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


def print_place_info(place_info):
    try:
        # 각 항목을 포맷
        formatted_address = format_address(place_info.get("주소", ""))
        formatted_phone = format_phone_number(place_info.get("가상번호", ""), place_info.get("이름", ""))
        formatted_price = format_price(place_info.get("금액", []))
        formatted_facilities = format_facilities(place_info.get("편의", []))
        # formatted_business_hours = format_business_hours(place_info.get("영업시간", []))
        formatted_new_business_hours = format_new_business_hours(place_info.get("새로운 영업시간", []))
        formatted_information = extract_information(place_info.get("정보", []))
        formatted_reviews = format_review_analysis(place_info.get("리뷰 분석", []))
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


def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)
    log_text_widget.insert(tk.END, f"{formatted_text}\n")
    log_text_widget.see(tk.END)


def main(query, total_queries, current_query_index):
    try:
        page = 1
        results = []
        all_ids = set()
        all_ids_list = []
        total_count = 0

        new_print(f"크롤링 시작")
        while True:
            if stop_event.is_set():
                return

            result = fetch_search_results(query, page)
            if not result:
                break

            place_list = result.get("result", {}).get("place", {}).get("list", [])
            ids_this_page = [place.get("id") for place in place_list if place.get("id")]

            new_print(f"페이지 : {page}, 목록 : {ids_this_page}")

            if not ids_this_page:
                break

            all_ids.update(ids_this_page)
            page += 1
            time.sleep(random.uniform(1, 2))

        if not stop_event.is_set():
            all_ids_list = list(all_ids)
            total_count = len(all_ids_list)
            new_print(f"전체 매물 수 : {total_count}")

            progress['maximum'] = total_count
            progress['value'] = 0
            set_progress(query, total_queries, current_query_index)

        for idx, place_id in enumerate(all_ids_list, start=1):
            if stop_event.is_set():
                return

            place_info = fetch_place_info(place_id)
            if place_info:
                reviews_info = fetch_reviews(place_id)
                place_info["리뷰"] = reviews_info.get("reviews", [])
                place_info["리뷰 분석"] = reviews_info.get("stats", [])

                name = place_info["이름"]
                image_urls = fetch_photos(place_id)
                os.makedirs(f'images/{query}/{idx}. {name}', exist_ok=True)
                for i, image_url in enumerate(image_urls, start=1):
                    download_image(image_url, f'images/{query}/{idx}. {name}/{name}_{i}.jpg')
                place_info['이미지 URLs'] = image_urls
                results.append(place_info)

                new_print(f"번호 : {idx}, 이름 : {place_info['이름']}")
                time.sleep(random.uniform(1, 2))

                if not stop_event.is_set():
                    progress['value'] += 1
                    set_progress(query, total_queries, current_query_index)

        if not stop_event.is_set():
            progress['maximum'] = total_count
            progress['value'] = total_count
            set_progress(query, total_queries, current_query_index)
            query_no_spaces = query.replace(" ", "")
            save_to_excel(results, query_no_spaces)

    except Exception as e:
        print(f"Unexpected error: {e}")


def set_progress(query, total_queries, current_query_index):
    # 개별 진행률 업데이트
    progress_label.config(text=f"[{query}] 진행률: {progress['value'] / progress['maximum'] * 100:.2f}% ({progress['value']}/{progress['maximum']})")
    remaining_time = (progress['maximum'] - progress['value']) * time_val
    eta = str(timedelta(seconds=remaining_time)).split(".")[0]  # 소수점 제거
    eta_label.config(text=f"예상 소요 시간: {eta}")
    progress.update_idletasks()

    # 전체 진행률 업데이트
    overall_progress_percentage = ((current_query_index + progress['value'] / progress['maximum']) / total_queries) * 100
    overall_progress_label.config(text=f"전체 진행률: {overall_progress_percentage:.2f}%")
    overall_progress['value'] = overall_progress_percentage
    overall_progress.update_idletasks()


def save_to_excel(results, query_no_spaces, mode='w'):
    new_print(f"엑셀 저장 시작...")
    blogs = []
    for result in results:
        blog = {}
        blog["아이디"] = result["아이디"]
        blog["이름"] = result["이름"]
        blog["블로그 제목"] = f"{query_no_spaces} / {result['이름']} / 운영시간 가격 주차리뷰"
        blog["블로그 게시글"] = print_place_info(result)
        # 이미지 링크와 블로그 게시글 생성
        image_urls = result.get("이미지 URLs", [])
        image_links = "\n".join(image_urls[:5])
        blog["주소"] = result["주소"]
        blog["이미지"] = image_links
        blog["정보 URL"] = result["URL"]
        blog["지도 URL"] = result["지도"]
        print(blog["블로그 게시글"])
        blogs.append(blog)

    # 현재 날짜와 시간 구하기
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 파일 이름에 현재 날짜와 시간 추가, 파일 이름을 안전하게 처리
    file_name = sanitize_filename(f'{query_no_spaces}_{timestamp}.xlsx')
    try:
        if mode == 'a':
            existing_df = pd.read_excel(file_name)
            new_df = pd.DataFrame(blogs)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(blogs)
        df.to_excel(file_name, index=False)
    except FileNotFoundError:
        df = pd.DataFrame(blogs)
        df.to_excel(file_name, index=False)

    new_print(f"엑셀 저장 {file_name}")
    # 메시지박스 표시


def sanitize_filename(name):
    # 파일 이름에 사용할 수 없는 문자들을 제거합니다.
    return re.sub(r'[\\/*?:"<>|]', "", name)


def start_app():
    global root, search_entry, search_button, log_text_widget, progress, progress_label, eta_label, overall_progress_label, overall_progress

    root = tk.Tk()
    root.title("네이버 블로그 프로그램")
    root.geometry("700x750")  # 크기 조정

    font_large = ('Helvetica', 10)  # 폰트 크기

    # 옵션 프레임
    option_frame = tk.Frame(root)
    option_frame.pack(fill=tk.X, padx=10, pady=10)

    # 검색어 입력 프레임
    search_frame = tk.Frame(root)
    search_frame.pack(pady=20)

    # 검색어 레이블
    search_label = tk.Label(search_frame, text="검색어:", font=font_large)
    search_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

    # 검색어 입력 필드
    search_entry = tk.Entry(search_frame, font=font_large, width=25)
    search_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    # 검색 버튼
    search_button = tk.Button(search_frame, text="검색", font=font_large, bg="lightgreen", command=on_search)
    search_button.grid(row=0, column=2, padx=5, pady=5)

    # 안내 문구
    guide_label = tk.Label(search_frame, text="* 콤마(,)로 구분하여 검색어를 작성해주세요 *", font=font_large, fg="red")
    guide_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    # 검색 프레임의 열 비율 설정
    search_frame.columnconfigure(1, weight=1)

    # 로그 화면
    log_label = tk.Label(root, text="로그 화면", font=font_large)
    log_label.pack(fill=tk.X, padx=10)

    log_frame = tk.Frame(root)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    x_scrollbar = tk.Scrollbar(log_frame, orient=tk.HORIZONTAL)
    x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    y_scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL)
    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    log_text_widget = tk.Text(log_frame, wrap=tk.NONE, height=10, font=font_large, xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
    log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    x_scrollbar.config(command=log_text_widget.xview)
    y_scrollbar.config(command=log_text_widget.yview)

    # 진행률
    progress_frame = tk.Frame(root)
    progress_frame.pack(fill=tk.X, padx=10, pady=10)

    # 개별 진행률 표시
    progress_label = tk.Label(progress_frame, text="진행률: 0%", font=font_large)
    progress_label.pack(side=tk.TOP, padx=5)

    # 예상 소요 시간
    eta_label = tk.Label(progress_frame, text="예상 소요 시간: 00:00:00", font=font_large)
    eta_label.pack(side=tk.TOP, padx=5)


    # 개별 진행률 게이지 바 (전체 진행률 아래로 이동)
    progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    progress.pack(fill=tk.X, padx=10, pady=(0, 10), expand=True)

    # 전체 진행률 표시 (위로 이동)
    overall_progress_label = tk.Label(progress_frame, text="전체 진행률: 0%", font=font_large)
    overall_progress_label.pack(side=tk.TOP, padx=5)

    # 전체 진행률 게이지 바
    overall_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style="TProgressbar")
    overall_progress.pack(fill=tk.X, padx=10, pady=(0, 10), expand=True)

    root.mainloop()


def run_main(querys):
    try:
        query_list = [q.strip() for q in querys.split(",")]
        total_queries = len(query_list)
        for idx, query in enumerate(query_list):
            if stop_event.is_set():
                break
            new_print(f"검색어: {query} 크롤링 시작", "INFO")
            progress_label.config(text=f"[{query}] 진행률: 0%")
            main(query, total_queries, idx)

        if not stop_event.is_set():
            messagebox.showwarning("경고", "크롤링이 완료되었습니다.")
            search_button.config(bg="lightgreen", fg="black", text="검색")

    except Exception as e:
        new_print(f"Unexpected error in thread: {e}", "ERROR")


def on_search():
    global search_thread, stop_event
    query = search_entry.get().strip()
    if query:
        if search_thread and search_thread.is_alive():
            # 중지 버튼이 클릭되면 작업 중지
            new_print("크롤링 중지")
            stop_event.set()  # 이벤트 설정
            search_button.config(bg="lightgreen", fg="black", text="검색")

            # 진행률 게이지바 초기화
            progress['value'] = 0
            overall_progress['value'] = 0
            progress_label.config(text="진행률: 0%")
            overall_progress_label.config(text="전체 진행률: 0%")
            eta_label.config(text="예상 소요 시간: 00:00:00")
            messagebox.showwarning("경고", "크롤링이 중지되었습니다.")
        else:
            # 시작 버튼 클릭 시 모든 진행률 초기화
            stop_event.clear()  # 이벤트 초기화
            log_text_widget.delete('1.0', tk.END)  # 로그 초기화
            progress['value'] = 0  # 개별 진행률 초기화
            overall_progress['value'] = 0  # 전체 진행률 초기화
            progress_label.config(text="진행률: 0%")
            overall_progress_label.config(text="전체 진행률: 0%")
            eta_label.config(text="예상 소요 시간: 00:00:00")
            search_button.config(bg="red", fg="white", text="중지")
            search_thread = threading.Thread(target=run_main, args=(query,))
            search_thread.start()
    else:
        messagebox.showwarning("경고", "검색어를 입력하세요.")

# 여기에 main 함수와 기타 필요한 함수들을 포함시키세요.

if __name__ == "__main__":
    start_app()
