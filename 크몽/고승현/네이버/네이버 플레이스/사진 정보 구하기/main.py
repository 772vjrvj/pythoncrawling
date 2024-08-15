import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

def fetch_search_results(query, page):
    url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
    print(f"url : {url}")
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
    if response.status_code != 200:
        return None
    return response.json()


def fetch_place_info(place_id):
    url = f"https://m.place.naver.com/place/{place_id}"

    headers = {
        'authority': 'm.place.naver.com',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
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

        # <script> 태그 안에 있는 JSON-like 데이터 추출
        script_tag = soup.find('script', text=re.compile('window.__APOLLO_STATE__'))
        if script_tag:
            # JSON 데이터를 추출하기 위해 정규 표현식 사용
            json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
            if json_text:
                data = json.loads(json_text.group(1))

                # 1. f"PlaceDetailBase:{place_id}"에서 "roadAddress" 값 추출
                address = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")

                # 2. f"Menu:{place_id}_n" 값들을 "금액" 배열에 담기
                prices = []
                for key, value in data.items():
                    if key.startswith(f"Menu:{place_id}"):
                        prices.append(value)

                # 3. "InformationFacilities:n" 값들을 "편의" 배열에 담기
                facilities = []
                for key, value in data.items():
                    if key.startswith("InformationFacilities:"):
                        facilities.append(value)

                # 4. "ROOT_QUERY" 안에서 이미지 추출
                imageUrls = []  # origin 값을 담을 배열
                root_query = data.get("ROOT_QUERY", {})
                place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'
                images_info = root_query.get(place_detail_key, {}).get('images({"source":["ugcModeling"]})', {}).get("images", [])
                # origin 값만 추출하여 imageUrls 배열에 담기
                for image in images_info:
                    origin_url = image.get("origin")
                    if origin_url:
                        imageUrls.append(origin_url)

                # 5. "businessHours" 정보 추출
                business_hours = root_query.get(place_detail_key, {}).get('businessHours({"source":["tpirates","jto","shopWindow"]})', [])


                URL = f"https://pcmap.place.naver.com/place/{place_id}/home"

                # 결과 출력
                print(f"\n=== Place ID: {place_id} ===")
                print("주소:", address)
                print("금액:", prices)
                print("편의:", facilities)
                print("이미지:", imageUrls)
                print("영업시간:", business_hours)
                print("URL:", URL)

    else:
        print(f"Failed to fetch data for Place ID: {place_id}. Status code: {response.status_code}")


def main():
    all_ids = []  # 모든 id를 저장할 배열
    # query = input("검색어를 입력하세요: ")
    query = "당감동 스터디카페"
    page = 1

    while True:
        result = fetch_search_results(query, page)
        print(f"query: {query}, page: {page}")

        if result is None or "error" in result:
            print(f"error result: {result}")
            break

        # "place" -> "list" 안에 있는 id들을 가져와서 배열에 추가
        place_list = result.get("result", {}).get("place", {}).get("list", [])
        for place in place_list:
            place_id = place.get("id")
            if place_id:
                all_ids.append(place_id)

        # 다음 페이지로 이동
        page += 1
        break
        time.sleep(random.uniform(1, 2))


    # 모든 페이지에서 수집한 id 출력
    print("모든 ID:", all_ids)


    for place_id in all_ids:
        fetch_place_info(place_id)
        # 요청 간 딜레이 추가
        time.sleep(random.uniform(1, 2))  # 1~3초 사이의 랜덤 딜레이


if __name__ == "__main__":
    main()
