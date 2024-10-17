import requests
import random
import time

# 함수로 분리
def get_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "content-length": "178",
        "content-type": "application/x-www-form-urlencoded",
        "host": "im.diningcode.com",
        "origin": "https://www.diningcode.com",
        "referer": "https://www.diningcode.com/",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

def get_payload(query, page):
    return {
        "query": query,
        "addr": "",
        "keyword": "",
        "order": "r_score",
        "distance": "",
        "rn_search_flag": "on",
        "search_type": "poi_search",
        "lat": "",
        "lng": "",
        "rect": "",
        "s_type": "",
        "token": "",
        "mode": "poi",
        "dc_flag": "1",
        "page": page,
        "size": "20"
    }

def fetch_search_results(query, page):
    url = "https://im.diningcode.com/API/isearch/"
    headers = get_headers()
    payload = get_payload(query, page)

    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def fetch_place_info(place_id):
    # place_id에 대한 추가 정보를 가져오는 로직이 필요할 경우 구현
    pass

def new_print(message):
    print(message)

# 메인 함수
def main(query):
    try:
        page = 1
        results = []
        all_ids = set()

        new_print("크롤링 시작")
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
            time.sleep(random.uniform(2, 3))

        all_ids_list = list(all_ids)
        total_count = len(all_ids_list)
        new_print(f"전체 매물 수 : {total_count}")

        for idx, place_id in enumerate(all_ids_list, start=1):
            print(f'place_id : {place_id}')
            place_info = fetch_place_info(place_id)
            if place_info:
                place_info["가게번호"] = place_id
                place_info["검색어"] = query
                place_info["식당이름"] = query.split()[-1]
                new_print(place_info)
                results.append(place_info)
                time.sleep(random.uniform(2, 3))

        return results

    except Exception as e:
        print(f"Unexpected error: {e}")

