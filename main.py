import requests
import json
import time
import random
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import zipfile

# 검색 쿼리 생성
def generate_query(place, city):
    return f"{place} {city} 운세 사주"

# 검색 결과를 가져오는 함수
def fetch_search_results(query, page):
    url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
    print(f"url : {url}")
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Cookie': 'NNB=KJRADCOI5CJGM; NAC=3JEFBMw72ynA; BUC=qrDJrb9ae5JFFJnP2us_jD1AfsTGoTu_xyovmNGfYDo=',
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

# 엑셀 데이터를 불러와서 딕셔너리로 변환하는 함수
def load_excel_to_dict(file_name):
    df = pd.read_excel(file_name)
    overall_results_dict = {}
    for _, row in df.iterrows():
        address_key = (row.get("지역"), row.get("도시"), row.get("상세주소"))
        overall_results_dict[address_key] = row.to_dict()
    return overall_results_dict

# 중복 제거 및 데이터 가공 함수
def process_data(overall_results_dict):
    processed_dict = {}
    for key, value in overall_results_dict.items():
        place, city, abbr_address = key
        if not place:
            place = city if city else abbr_address if abbr_address else ""
        value["도시"] = city
        value["지역"] = place

        existing_entry = processed_dict.get((city, value["상세주소"]))
        if existing_entry:
            if existing_entry.get('전화번호') is None and value.get('전화번호') is not None:
                processed_dict[(city, value["상세주소"])] = value
            elif existing_entry.get('전화번호') is None and value.get('전화번호') is None:
                processed_dict[(city, value["상세주소"])] = value
        else:
            processed_dict[(city, value["상세주소"])] = value
    return processed_dict

# 엑셀에 저장하는 함수
def save_to_excel(results_dict, file_name):
    results_list = list(results_dict.values())
    df = pd.DataFrame(results_list)
    df_selected = df[["ID", "지역", "도시", "주소", "도로명 주소", "상세주소", "이름", "카테고리", "전화번호", "URL", "place", "city", "page"]]

    try:
        # 기존 파일에 데이터 추가
        book = load_workbook(file_name)
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            startrow = book['Sheet1'].max_row
            df_selected.to_excel(writer, index=False, sheet_name='Sheet1', startrow=startrow, header=False)
    except (FileNotFoundError, zipfile.BadZipFile, KeyError):
        # 파일이 없거나 손상된 경우 새로 생성
        df_selected.to_excel(file_name, index=False, sheet_name='Sheet1')

    print(f"Data appended to {file_name}")

def main(new_yn, file_name, cities):
    start_time = datetime.now()
    print(f"시작 시간: {start_time.strftime('%Y.%m.%d %H:%M:%S')}")

    # 결과를 저장할 딕셔너리 (중복 제거를 위해)
    results_dict = {}
    total_count = 0
    batch_number = 1

    # 고유한 파일 이름 생성
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file_name = f"search_results_{timestamp}.xlsx"

    # 중복 체크를 위한 전체 결과 저장 딕셔너리
    overall_results_dict = {}

    if new_yn == "N":
        overall_results_dict = load_excel_to_dict(file_name)

    for entry in cities:
        place = entry["place"]
        city = entry["city"]
        query = generate_query(place, city)
        page = 1

        while True:
            # 랜덤으로 2~4초 딜레이
            time.sleep(random.uniform(2, 4))

            result = fetch_search_results(query, page)
            print(f"query : {query}, page : {page}")
            if result is None or "error" in result:
                print(f"error result : {result}")
                break
            try:
                places = result.get("result", {}).get("place", {}).get("list", [])
            except AttributeError as e:
                print(f"Error accessing keys: {e}")
                break
            print(f"places len : {len(places)}")

            if not places:
                break

            for place in places:

                new_place = {}

                address = place.get("address")
                road_address = place.get("roadAddress")
                abbr_address = place.get("abbrAddress")

                new_place["주소"] = address
                new_place["도로명 주소"] = road_address
                new_place["상세주소"] = abbr_address

                # address가 없는 경우 road_address로 대체
                actual_address = address if address else (road_address if road_address else "")

                place_region = actual_address.split(' ')[0] if pd.notna(actual_address) and len(actual_address.split(' ')) > 0 else ""
                place_city = actual_address.split(' ')[1] if pd.notna(actual_address) and len(actual_address.split(' ')) > 1 else ""

                address_key = (place_region, place_city, abbr_address)
                new_place["ID"] = place.get("id")
                new_place["지역"] = place_region
                new_place["도시"] = place_city
                new_place["이름"] = place.get("name")
                new_place["카테고리"] = "운세,사주"
                new_place["전화번호"] = place.get("tel")
                new_place["URL"] = f"https://map.naver.com/p/entry/place/{new_place['ID']}"
                new_place["place"] = entry["place"]
                new_place["city"] = entry["city"]
                new_place["page"] = page

                if address_key not in overall_results_dict:
                    overall_results_dict[address_key] = new_place
                    total_count += 1

                    # 임시 딕셔너리에 추가
                    results_dict[address_key] = new_place
                else:
                    existing_place = overall_results_dict[address_key]
                    if existing_place.get('전화번호') is None and new_place.get('전화번호') is not None:
                        overall_results_dict[address_key] = new_place

                        # 임시 딕셔너리에 추가
                        results_dict[address_key] = new_place


            page += 1
            print(f"100단위 카운트 ============== {len(results_dict)}==================")
            print(f"현재까지 작업한 전체 카운트: {total_count}")

            # 100개마다 저장
            if len(results_dict) >= 100:
                save_to_excel(results_dict, output_file_name)
                batch_number += 1
                results_dict.clear()

    # 남은 데이터 저장
    if results_dict:
        save_to_excel(results_dict, output_file_name)

    end_time = datetime.now()
    print(f"종료 시간: {end_time.strftime('%Y.%m.%d %H:%M:%S')}")

    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"총 걸린 시간: {int(hours)}시간 {int(minutes)}분 {int(seconds)}초")
    print(f"최종 작업한 전체 카운트: {total_count}")

if __name__ == "__main__":

    cities = [
        {"place": "강원도", "city": "춘천시"},
        {"place": "강원도", "city": "원주시"},
        {"place": "강원도", "city": "강릉시"},
        {"place": "강원도", "city": "동해시"},
        {"place": "강원도", "city": "태백시"},
        {"place": "강원도", "city": "속초시"},
        {"place": "강원도", "city": "삼척시"},
        {"place": "강원도", "city": "홍천군"},
        {"place": "강원도", "city": "횡성군"},
        {"place": "강원도", "city": "영월군"},
        {"place": "강원도", "city": "평창군"},
        {"place": "강원도", "city": "정선군"},
        {"place": "강원도", "city": "철원군"},
        {"place": "강원도", "city": "화천군"},
        {"place": "강원도", "city": "양구군"},
        {"place": "강원도", "city": "인제군"},
        {"place": "강원도", "city": "고성군"},
        {"place": "강원도", "city": "양양군"}
    ]

    main("Y", "", cities)
