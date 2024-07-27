import requests
import json
import time
import random
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import zipfile

# 검색 쿼리 생성
def generate_query(place, city, keyword):
    return f"{place} {city} {keyword}"

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

# 엑셀에 저장하는 함수
def save_to_excel(results_dict, file_name):
    results_list = list(results_dict.values())
    df = pd.DataFrame(results_list)
    df_selected = df[["ID", "지역", "도시", "주소", "도로명 주소", "상세주소", "이름", "카테고리", "전화번호", "URL", "Page", "검색 키워드", "검색 지역", "검색 도시"]]

    try:
        # 기존 파일에 데이터 추가
        book = load_workbook(file_name)
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            if 'Sheet1' in book.sheetnames:
                startrow = book['Sheet1'].max_row
            else:
                startrow = 0
            df_selected.to_excel(writer, index=False, sheet_name='Sheet1', startrow=startrow, header=startrow == 0)
    except (FileNotFoundError, zipfile.BadZipFile, KeyError):
        # 파일이 없거나 손상된 경우 새로 생성
        df_selected.to_excel(file_name, index=False, sheet_name='Sheet1')

    print(f"Data appended to {file_name}")

def main(new_yn, file_name, cities, keywords):
    start_time = datetime.now()
    print(f"시작 시간: {start_time.strftime('%Y.%m.%d %H:%M:%S')}")

    # 결과를 저장할 딕셔너리 (중복 제거를 위해)
    results_dict = {}
    new_total_count = 0
    old_total_count = 0
    batch_number = 1

    # 고유한 파일 이름 생성
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file_name = f"search_results_{timestamp}.xlsx"

    # 중복 체크를 위한 전체 결과 저장 딕셔너리
    overall_results_dict = {}

    if new_yn == "N":
        overall_results_dict = load_excel_to_dict(file_name)
        old_total_count = len(overall_results_dict)
        print(f"기존 작업에 추가 overall_results_dict len : {len(overall_results_dict)}")

    for keyword in keywords:
        print(f"keyword : {keyword}")

        for entry in cities:
            place = entry["sd_nm"]
            city = entry["sgg_nm"]
            query = generate_query(place, city, keyword)
            page = 1

            while True:
                print(f"========================[시작]========================")
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
                    new_place["카테고리"] = ", ".join(place.get("category", []))
                    new_place["전화번호"] = place.get("tel")
                    new_place["URL"] = f"https://map.naver.com/p/entry/place/{new_place['ID']}"
                    new_place["Page"] = page
                    new_place["검색 키워드"] = keyword
                    new_place["검색 지역"] = entry["sd_nm"]
                    new_place["검색 도시"] = entry["sgg_nm"]

                    if address_key not in overall_results_dict:
                        overall_results_dict[address_key] = new_place
                        new_total_count += 1

                        # 임시 딕셔너리에 추가
                        results_dict[address_key] = new_place
                    else:
                        existing_place = overall_results_dict[address_key]
                        if existing_place.get('전화번호') is None and new_place.get('전화번호') is not None:
                            overall_results_dict[address_key] = new_place

                            # 임시 딕셔너리에 추가
                            results_dict[address_key] = new_place

                page += 1
                print(f"===== 500단위 카운트 : {len(results_dict)}")
                # print(f"===== 현재까지 작업한 기존 전체 카운트: {old_total_count}")
                # print(f"===== 현재까지 작업한 신규 전체 카운트: {new_total_count}")
                print(f"===== 현재까지 작업한 total 전체 카운트: {new_total_count + old_total_count}")

                # 500개마다 저장
                if len(results_dict) >= 500:
                    save_to_excel(results_dict, output_file_name)
                    batch_number += 1
                    results_dict.clear()

                print(f"========================[종료]========================")

    # 남은 데이터 저장
    if results_dict:
        save_to_excel(results_dict, output_file_name)

    end_time = datetime.now()
    print(f"종료 시간: {end_time.strftime('%Y.%m.%d %H:%M:%S')}")

    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"총 걸린 시간: {int(hours)}시간 {int(minutes)}분 {int(seconds)}초")
    print(f"최종 작업한 전체 카운트: {new_total_count + old_total_count}")


if __name__ == "__main__":

    cities = [
        {"sd_nm": "서울", "sgg_nm": "종로구"},
        {"sd_nm": "서울", "sgg_nm": "중구"},
        {"sd_nm": "서울", "sgg_nm": "용산구"},
        {"sd_nm": "서울", "sgg_nm": "성동구"},
        {"sd_nm": "서울", "sgg_nm": "광진구"},
        {"sd_nm": "서울", "sgg_nm": "동대문구"},
        {"sd_nm": "서울", "sgg_nm": "중랑구"},
        {"sd_nm": "서울", "sgg_nm": "성북구"},
        {"sd_nm": "서울", "sgg_nm": "강북구"},
        {"sd_nm": "서울", "sgg_nm": "도봉구"},
        {"sd_nm": "서울", "sgg_nm": "노원구"},
        {"sd_nm": "서울", "sgg_nm": "은평구"},
        {"sd_nm": "서울", "sgg_nm": "서대문구"},
        {"sd_nm": "서울", "sgg_nm": "마포구"},
        {"sd_nm": "서울", "sgg_nm": "양천구"},
        {"sd_nm": "서울", "sgg_nm": "강서구"},
        {"sd_nm": "서울", "sgg_nm": "구로구"},
        {"sd_nm": "서울", "sgg_nm": "금천구"},
        {"sd_nm": "서울", "sgg_nm": "영등포구"},
        {"sd_nm": "서울", "sgg_nm": "동작구"},
        {"sd_nm": "서울", "sgg_nm": "관악구"},
        {"sd_nm": "서울", "sgg_nm": "서초구"},
        {"sd_nm": "서울", "sgg_nm": "강남구"},
        {"sd_nm": "서울", "sgg_nm": "송파구"},
        {"sd_nm": "서울", "sgg_nm": "강동구"},
        {"sd_nm": "부산", "sgg_nm": "중구"},
        {"sd_nm": "부산", "sgg_nm": "서구"},
        {"sd_nm": "부산", "sgg_nm": "동구"},
        {"sd_nm": "부산", "sgg_nm": "영도구"},
        {"sd_nm": "부산", "sgg_nm": "부산진구"},
        {"sd_nm": "부산", "sgg_nm": "동래구"},
        {"sd_nm": "부산", "sgg_nm": "남구"},
        {"sd_nm": "부산", "sgg_nm": "북구"},
        {"sd_nm": "부산", "sgg_nm": "해운대구"},
        {"sd_nm": "부산", "sgg_nm": "사하구"},
        {"sd_nm": "부산", "sgg_nm": "금정구"},
        {"sd_nm": "부산", "sgg_nm": "강서구"},
        {"sd_nm": "부산", "sgg_nm": "연제구"},
        {"sd_nm": "부산", "sgg_nm": "수영구"},
        {"sd_nm": "부산", "sgg_nm": "사상구"},
        {"sd_nm": "부산", "sgg_nm": "기장군"},
        {"sd_nm": "대구", "sgg_nm": "중구"},
        {"sd_nm": "대구", "sgg_nm": "동구"},
        {"sd_nm": "대구", "sgg_nm": "서구"},
        {"sd_nm": "대구", "sgg_nm": "남구"},
        {"sd_nm": "대구", "sgg_nm": "북구"},
        {"sd_nm": "대구", "sgg_nm": "수성구"},
        {"sd_nm": "대구", "sgg_nm": "달서구"},
        {"sd_nm": "대구", "sgg_nm": "달성군"},
        {"sd_nm": "인천", "sgg_nm": "중구"},
        {"sd_nm": "인천", "sgg_nm": "동구"},
        {"sd_nm": "인천", "sgg_nm": "미추홀구"},
        {"sd_nm": "인천", "sgg_nm": "연수구"},
        {"sd_nm": "인천", "sgg_nm": "남동구"},
        {"sd_nm": "인천", "sgg_nm": "부평구"},
        {"sd_nm": "인천", "sgg_nm": "계양구"},
        {"sd_nm": "인천", "sgg_nm": "서구"},
        {"sd_nm": "인천", "sgg_nm": "강화군"},
        {"sd_nm": "인천", "sgg_nm": "옹진군"},
        {"sd_nm": "광주", "sgg_nm": "동구"},
        {"sd_nm": "광주", "sgg_nm": "서구"},
        {"sd_nm": "광주", "sgg_nm": "남구"},
        {"sd_nm": "광주", "sgg_nm": "북구"},
        {"sd_nm": "광주", "sgg_nm": "광산구"},
        {"sd_nm": "대전", "sgg_nm": "동구"},
        {"sd_nm": "대전", "sgg_nm": "중구"},
        {"sd_nm": "대전", "sgg_nm": "서구"},
        {"sd_nm": "대전", "sgg_nm": "유성구"},
        {"sd_nm": "대전", "sgg_nm": "대덕구"},
        {"sd_nm": "울산", "sgg_nm": "중구"},
        {"sd_nm": "울산", "sgg_nm": "남구"},
        {"sd_nm": "울산", "sgg_nm": "동구"},
        {"sd_nm": "울산", "sgg_nm": "북구"},
        {"sd_nm": "울산", "sgg_nm": "울주군"},
        {"sd_nm": "경기도", "sgg_nm": "수원시 장안구"},
        {"sd_nm": "경기도", "sgg_nm": "수원시 권선구"},
        {"sd_nm": "경기도", "sgg_nm": "수원시 팔달구"},
        {"sd_nm": "경기도", "sgg_nm": "수원시 영통구"},
        {"sd_nm": "경기도", "sgg_nm": "성남시 수정구"},
        {"sd_nm": "경기도", "sgg_nm": "성남시 중원구"},
        {"sd_nm": "경기도", "sgg_nm": "성남시 분당구"},
        {"sd_nm": "경기도", "sgg_nm": "의정부시"},
        {"sd_nm": "경기도", "sgg_nm": "안양시 만안구"},
        {"sd_nm": "경기도", "sgg_nm": "안양시 동안구"},
        {"sd_nm": "경기도", "sgg_nm": "부천시"},
        {"sd_nm": "경기도", "sgg_nm": "광명시"},
        {"sd_nm": "경기도", "sgg_nm": "평택시"},
        {"sd_nm": "경기도", "sgg_nm": "동두천시"},
        {"sd_nm": "경기도", "sgg_nm": "안산시 상록구"},
        {"sd_nm": "경기도", "sgg_nm": "안산시 단원구"},
        {"sd_nm": "경기도", "sgg_nm": "고양시 덕양구"},
        {"sd_nm": "경기도", "sgg_nm": "고양시 일산동구"},
        {"sd_nm": "경기도", "sgg_nm": "고양시 일산서구"},
        {"sd_nm": "경기도", "sgg_nm": "과천시"},
        {"sd_nm": "경기도", "sgg_nm": "구리시"},
        {"sd_nm": "경기도", "sgg_nm": "남양주시"},
        {"sd_nm": "경기도", "sgg_nm": "오산시"},
        {"sd_nm": "경기도", "sgg_nm": "시흥시"},
        {"sd_nm": "경기도", "sgg_nm": "군포시"},
        {"sd_nm": "경기도", "sgg_nm": "의왕시"},
        {"sd_nm": "경기도", "sgg_nm": "하남시"},
        {"sd_nm": "경기도", "sgg_nm": "용인시 처인구"},
        {"sd_nm": "경기도", "sgg_nm": "용인시 기흥구"},
        {"sd_nm": "경기도", "sgg_nm": "용인시 수지구"},
        {"sd_nm": "경기도", "sgg_nm": "파주시"},
        {"sd_nm": "경기도", "sgg_nm": "이천시"},
        {"sd_nm": "경기도", "sgg_nm": "안성시"},
        {"sd_nm": "경기도", "sgg_nm": "김포시"},
        {"sd_nm": "경기도", "sgg_nm": "화성시"},
        {"sd_nm": "경기도", "sgg_nm": "광주시"},
        {"sd_nm": "경기도", "sgg_nm": "양주시"},
        {"sd_nm": "경기도", "sgg_nm": "포천시"},
        {"sd_nm": "경기도", "sgg_nm": "여주시"},
        {"sd_nm": "경기도", "sgg_nm": "연천군"},
        {"sd_nm": "경기도", "sgg_nm": "가평군"},
        {"sd_nm": "경기도", "sgg_nm": "양평군"},
        {"sd_nm": "강원도", "sgg_nm": "춘천시"},
        {"sd_nm": "강원도", "sgg_nm": "원주시"},
        {"sd_nm": "강원도", "sgg_nm": "강릉시"},
        {"sd_nm": "강원도", "sgg_nm": "동해시"},
        {"sd_nm": "강원도", "sgg_nm": "태백시"},
        {"sd_nm": "강원도", "sgg_nm": "속초시"},
        {"sd_nm": "강원도", "sgg_nm": "삼척시"},
        {"sd_nm": "강원도", "sgg_nm": "홍천군"},
        {"sd_nm": "강원도", "sgg_nm": "횡성군"},
        {"sd_nm": "강원도", "sgg_nm": "영월군"},
        {"sd_nm": "강원도", "sgg_nm": "평창군"},
        {"sd_nm": "강원도", "sgg_nm": "정선군"},
        {"sd_nm": "강원도", "sgg_nm": "철원군"},
        {"sd_nm": "강원도", "sgg_nm": "화천군"},
        {"sd_nm": "강원도", "sgg_nm": "양구군"},
        {"sd_nm": "강원도", "sgg_nm": "인제군"},
        {"sd_nm": "강원도", "sgg_nm": "고성군"},
        {"sd_nm": "강원도", "sgg_nm": "양양군"},
        {"sd_nm": "충청북도", "sgg_nm": "청주시 상당구"},
        {"sd_nm": "충청북도", "sgg_nm": "청주시 서원구"},
        {"sd_nm": "충청북도", "sgg_nm": "청주시 흥덕구"},
        {"sd_nm": "충청북도", "sgg_nm": "청주시 청원구"},
        {"sd_nm": "충청북도", "sgg_nm": "충주시"},
        {"sd_nm": "충청북도", "sgg_nm": "제천시"},
        {"sd_nm": "충청북도", "sgg_nm": "보은군"},
        {"sd_nm": "충청북도", "sgg_nm": "옥천군"},
        {"sd_nm": "충청북도", "sgg_nm": "영동군"},
        {"sd_nm": "충청북도", "sgg_nm": "증평군"},
        {"sd_nm": "충청북도", "sgg_nm": "진천군"},
        {"sd_nm": "충청북도", "sgg_nm": "괴산군"},
        {"sd_nm": "충청북도", "sgg_nm": "음성군"},
        {"sd_nm": "충청북도", "sgg_nm": "단양군"},
        {"sd_nm": "충청남도", "sgg_nm": "천안시 동남구"},
        {"sd_nm": "충청남도", "sgg_nm": "천안시 서북구"},
        {"sd_nm": "충청남도", "sgg_nm": "공주시"},
        {"sd_nm": "충청남도", "sgg_nm": "보령시"},
        {"sd_nm": "충청남도", "sgg_nm": "아산시"},
        {"sd_nm": "충청남도", "sgg_nm": "서산시"},
        {"sd_nm": "충청남도", "sgg_nm": "논산시"},
        {"sd_nm": "충청남도", "sgg_nm": "계룡시"},
        {"sd_nm": "충청남도", "sgg_nm": "당진시"},
        {"sd_nm": "충청남도", "sgg_nm": "금산군"},
        {"sd_nm": "충청남도", "sgg_nm": "부여군"},
        {"sd_nm": "충청남도", "sgg_nm": "서천군"},
        {"sd_nm": "충청남도", "sgg_nm": "청양군"},
        {"sd_nm": "충청남도", "sgg_nm": "홍성군"},
        {"sd_nm": "충청남도", "sgg_nm": "예산군"},
        {"sd_nm": "충청남도", "sgg_nm": "태안군"},
        {"sd_nm": "전라북도", "sgg_nm": "전주시 완산구"},
        {"sd_nm": "전라북도", "sgg_nm": "전주시 덕진구"},
        {"sd_nm": "전라북도", "sgg_nm": "군산시"},
        {"sd_nm": "전라북도", "sgg_nm": "익산시"},
        {"sd_nm": "전라북도", "sgg_nm": "정읍시"},
        {"sd_nm": "전라북도", "sgg_nm": "남원시"},
        {"sd_nm": "전라북도", "sgg_nm": "김제시"},
        {"sd_nm": "전라북도", "sgg_nm": "완주군"},
        {"sd_nm": "전라북도", "sgg_nm": "진안군"},
        {"sd_nm": "전라북도", "sgg_nm": "무주군"},
        {"sd_nm": "전라북도", "sgg_nm": "장수군"},
        {"sd_nm": "전라북도", "sgg_nm": "임실군"},
        {"sd_nm": "전라북도", "sgg_nm": "순창군"},
        {"sd_nm": "전라북도", "sgg_nm": "고창군"},
        {"sd_nm": "전라북도", "sgg_nm": "부안군"},
        {"sd_nm": "전라남도", "sgg_nm": "목포시"},
        {"sd_nm": "전라남도", "sgg_nm": "여수시"},
        {"sd_nm": "전라남도", "sgg_nm": "순천시"},
        {"sd_nm": "전라남도", "sgg_nm": "나주시"},
        {"sd_nm": "전라남도", "sgg_nm": "광양시"},
        {"sd_nm": "전라남도", "sgg_nm": "담양군"},
        {"sd_nm": "전라남도", "sgg_nm": "곡성군"},
        {"sd_nm": "전라남도", "sgg_nm": "구례군"},
        {"sd_nm": "전라남도", "sgg_nm": "고흥군"},
        {"sd_nm": "전라남도", "sgg_nm": "보성군"},
        {"sd_nm": "전라남도", "sgg_nm": "화순군"},
        {"sd_nm": "전라남도", "sgg_nm": "장흥군"},
        {"sd_nm": "전라남도", "sgg_nm": "강진군"},
        {"sd_nm": "전라남도", "sgg_nm": "해남군"},
        {"sd_nm": "전라남도", "sgg_nm": "영암군"},
        {"sd_nm": "전라남도", "sgg_nm": "무안군"},
        {"sd_nm": "전라남도", "sgg_nm": "함평군"},
        {"sd_nm": "전라남도", "sgg_nm": "영광군"},
        {"sd_nm": "전라남도", "sgg_nm": "장성군"},
        {"sd_nm": "전라남도", "sgg_nm": "완도군"},
        {"sd_nm": "전라남도", "sgg_nm": "진도군"},
        {"sd_nm": "전라남도", "sgg_nm": "신안군"},
        {"sd_nm": "경상북도", "sgg_nm": "포항시 남구"},
        {"sd_nm": "경상북도", "sgg_nm": "포항시 북구"},
        {"sd_nm": "경상북도", "sgg_nm": "경주시"},
        {"sd_nm": "경상북도", "sgg_nm": "김천시"},
        {"sd_nm": "경상북도", "sgg_nm": "안동시"},
        {"sd_nm": "경상북도", "sgg_nm": "구미시"},
        {"sd_nm": "경상북도", "sgg_nm": "영주시"},
        {"sd_nm": "경상북도", "sgg_nm": "영천시"},
        {"sd_nm": "경상북도", "sgg_nm": "상주시"},
        {"sd_nm": "경상북도", "sgg_nm": "문경시"},
        {"sd_nm": "경상북도", "sgg_nm": "경산시"},
        {"sd_nm": "경상북도", "sgg_nm": "군위군"},
        {"sd_nm": "경상북도", "sgg_nm": "의성군"},
        {"sd_nm": "경상북도", "sgg_nm": "청송군"},
        {"sd_nm": "경상북도", "sgg_nm": "영양군"},
        {"sd_nm": "경상북도", "sgg_nm": "영덕군"},
        {"sd_nm": "경상북도", "sgg_nm": "청도군"},
        {"sd_nm": "경상북도", "sgg_nm": "고령군"},
        {"sd_nm": "경상북도", "sgg_nm": "성주군"},
        {"sd_nm": "경상북도", "sgg_nm": "칠곡군"},
        {"sd_nm": "경상북도", "sgg_nm": "예천군"},
        {"sd_nm": "경상북도", "sgg_nm": "봉화군"},
        {"sd_nm": "경상북도", "sgg_nm": "울진군"},
        {"sd_nm": "경상북도", "sgg_nm": "울릉군"},
        {"sd_nm": "경상남도", "sgg_nm": "창원시 의창구"},
        {"sd_nm": "경상남도", "sgg_nm": "창원시 성산구"},
        {"sd_nm": "경상남도", "sgg_nm": "창원시 마산합포구"},
        {"sd_nm": "경상남도", "sgg_nm": "창원시 마산회원구"},
        {"sd_nm": "경상남도", "sgg_nm": "창원시 진해구"},
        {"sd_nm": "경상남도", "sgg_nm": "진주시"},
        {"sd_nm": "경상남도", "sgg_nm": "통영시"},
        {"sd_nm": "경상남도", "sgg_nm": "사천시"},
        {"sd_nm": "경상남도", "sgg_nm": "김해시"},
        {"sd_nm": "경상남도", "sgg_nm": "밀양시"},
        {"sd_nm": "경상남도", "sgg_nm": "거제시"},
        {"sd_nm": "경상남도", "sgg_nm": "양산시"},
        {"sd_nm": "경상남도", "sgg_nm": "의령군"},
        {"sd_nm": "경상남도", "sgg_nm": "함안군"},
        {"sd_nm": "경상남도", "sgg_nm": "창녕군"},
        {"sd_nm": "경상남도", "sgg_nm": "고성군"},
        {"sd_nm": "경상남도", "sgg_nm": "남해군"},
        {"sd_nm": "경상남도", "sgg_nm": "하동군"},
        {"sd_nm": "경상남도", "sgg_nm": "산청군"},
        {"sd_nm": "경상남도", "sgg_nm": "함양군"},
        {"sd_nm": "경상남도", "sgg_nm": "거창군"},
        {"sd_nm": "경상남도", "sgg_nm": "합천군"},
        {"sd_nm": "제주도", "sgg_nm": "제주시"},
        {"sd_nm": "제주도", "sgg_nm": "서귀포시"}
    ]

    keywords = ["운세", "점집"]
    new_yn = "Y"
    file_name = "search_results_20240727142846.xlsx"

    main(new_yn, file_name, cities, keywords)
