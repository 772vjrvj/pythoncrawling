import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
import pandas as pd  # 추가된 부분

def fetch_search_results(query, page):
    try:
        url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'If-None-Match': 'W/"cc8e-p62VZFyMnUKal/n+PziFTq6yy3I"',
            'Priority': 'u=0, i',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
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

                    name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")

                    ## 주소(지번, 도로명)
                    address = data.get(f"PlaceDetailBase:{place_id}", {}).get("address", "")
                    roadAddress = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")

                    ## 대분류 소분류
                    category = data.get(f"PlaceDetailBase:{place_id}", {}).get("category", "")

                    ## 별점
                    visitorReviewsScore = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsScore", "")

                    ## 방문자리뷰수
                    visitorReviewsTotal = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsTotal", "")


                    root_query = data.get("ROOT_QUERY", {})
                    place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                    ## 블로그리뷰수
                    fsasReviewsTotal = root_query.get(place_detail_key, {}).get('fsasReviews', {}).get('fsasReviews', {}).get("total", "")

                    business_hours = root_query.get(place_detail_key, {}).get('businessHours({"source":["tpirates","jto","shopWindow"]})', [])

                    new_business_hours = root_query.get(place_detail_key, {}).get('newBusinessHours', [])

                    url = f"https://m.place.naver.com/place/{place_id}/home"
                    map_url = f"https://map.naver.com/p/entry/place/{place_id}"

                    result = {
                        "이름": name,
                        "주소(지번)": address,
                        "주소(도로명)": roadAddress,
                        "대분류": category,
                        "소분류": category,
                        "별점": visitorReviewsScore,
                        "방문자리뷰수": visitorReviewsTotal,
                        "블로그리뷰수": fsasReviewsTotal,
                        "이용시간1": format_business_hours(business_hours),
                        "이용시간2": format_new_business_hours(new_business_hours),
                        "URL": url,
                        "지도": map_url
                    }

                    return result

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
    except Exception as e:
        print(f"Error processing data for Place ID: {place_id}: {e}")
    return None


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


def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)


def save_to_excel(results, filename="results.xlsx"):
    df = pd.DataFrame(results)
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")


def main(query):
    try:
        page = 1
        results = []
        all_ids = set()

        new_print(f"크롤링 시작")
        while True:
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

        all_ids_list = list(all_ids)
        total_count = len(all_ids_list)
        new_print(f"전체 매물 수 : {total_count}")

        for idx, place_id in enumerate(all_ids_list, start=1):
            place_info = fetch_place_info(place_id)
            if place_info:
                place_info["검색어"] = query
                place_info["식당이름"] = query.split()[-1]
                results.append(place_info)
                new_print(f"번호 : {idx}, 이름 : {place_info['이름']}")
                time.sleep(random.uniform(1, 2))

        # 결과를 엑셀로 저장
        save_to_excel(results, filename=f"서울시 맛집.xlsx")

    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main("서울시 롤링파스타")
