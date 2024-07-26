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

def save_to_excel(results_dict, file_name):
    results_list = list(results_dict.values())
    df = pd.DataFrame(results_list)
    df_selected = df[["id", "name", "address", "roadAddress", "abbrAddress", "tel", "entry_place", "entry_city", "page"]].copy()
    df_selected.columns = ["ID", "이름", "주소", "도로명 주소", "상세주소", "전화번호", "place", "city", "page"]
    df_selected["지역"] = df["address"].apply(lambda x: x.split(' ')[0] if pd.notna(x) else "")
    df_selected["도시"] = df["address"].apply(lambda x: x.split(' ')[1] if pd.notna(x) else "")
    df_selected["카테고리"] = "운세,사주"
    df_selected["URL"] = df_selected["ID"].apply(lambda x: f"https://map.naver.com/p/entry/place/{x}")
    df_final = df_selected[["ID", "지역", "도시", "주소", "도로명 주소", "상세주소", "이름", "카테고리", "전화번호", "URL", "place", "city", "page"]]

    try:
        # 기존 파일에 데이터 추가
        book = load_workbook(file_name)
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            startrow = book['Sheet1'].max_row
            df_final.to_excel(writer, index=False, sheet_name='Sheet1', startrow=startrow, header=False)
    except (FileNotFoundError, zipfile.BadZipFile, KeyError):
        # 파일이 없거나 손상된 경우 새로 생성
        df_final.to_excel(file_name, index=False, sheet_name='Sheet1')

    print(f"Data appended to {file_name}")



def main():
    start_time = datetime.now()
    print(f"시작 시간: {start_time.strftime('%Y.%m.%d %H:%M:%S')}")

    cities = [
        {"place": "서울특별시", "city": "종로구"},
        {"place": "서울특별시", "city": "중구"},
        {"place": "서울특별시", "city": "용산구"},
        {"place": "서울특별시", "city": "성동구"},
        {"place": "서울특별시", "city": "광진구"},
        {"place": "서울특별시", "city": "동대문구"},
        {"place": "서울특별시", "city": "중랑구"},
        {"place": "서울특별시", "city": "성북구"},
        {"place": "서울특별시", "city": "강북구"},
        {"place": "서울특별시", "city": "도봉구"},
        {"place": "서울특별시", "city": "노원구"},
        {"place": "서울특별시", "city": "은평구"},
        {"place": "서울특별시", "city": "서대문구"},
        {"place": "서울특별시", "city": "마포구"},
        {"place": "서울특별시", "city": "양천구"},
        {"place": "서울특별시", "city": "강서구"},
        {"place": "서울특별시", "city": "구로구"},
        {"place": "서울특별시", "city": "금천구"},
        {"place": "서울특별시", "city": "영등포구"},
        {"place": "서울특별시", "city": "동작구"},
        {"place": "서울특별시", "city": "관악구"},
        {"place": "서울특별시", "city": "서초구"},
        {"place": "서울특별시", "city": "강남구"},
        {"place": "서울특별시", "city": "송파구"},
        {"place": "서울특별시", "city": "강동구"},
        {"place": "부산광역시", "city": "중구"},
        {"place": "부산광역시", "city": "서구"},
        {"place": "부산광역시", "city": "동구"},
        {"place": "부산광역시", "city": "영도구"},
        {"place": "부산광역시", "city": "부산진구"},
        {"place": "부산광역시", "city": "동래구"},
        {"place": "부산광역시", "city": "남구"},
        {"place": "부산광역시", "city": "북구"},
        {"place": "부산광역시", "city": "강서구"},
        {"place": "부산광역시", "city": "해운대구"},
        {"place": "부산광역시", "city": "사하구"},
        {"place": "부산광역시", "city": "금정구"},
        {"place": "부산광역시", "city": "연제구"},
        {"place": "부산광역시", "city": "수영구"},
        {"place": "부산광역시", "city": "사상구"},
        {"place": "부산광역시", "city": "기장군"},
        {"place": "대구광역시", "city": "중구"},
        {"place": "대구광역시", "city": "동구"},
        {"place": "대구광역시", "city": "서구"},
        {"place": "대구광역시", "city": "남구"},
        {"place": "대구광역시", "city": "북구"},
        {"place": "대구광역시", "city": "수성구"},
        {"place": "대구광역시", "city": "달서구"},
        {"place": "대구광역시", "city": "달성군"},
        {"place": "대구광역시", "city": "군위군"},
        {"place": "인천광역시", "city": "중구"},
        {"place": "인천광역시", "city": "동구"},
        {"place": "인천광역시", "city": "미추홀구"},
        {"place": "인천광역시", "city": "연수구"},
        {"place": "인천광역시", "city": "남동구"},
        {"place": "인천광역시", "city": "부평구"},
        {"place": "인천광역시", "city": "계양구"},
        {"place": "인천광역시", "city": "서구"},
        {"place": "인천광역시", "city": "강화군"},
        {"place": "인천광역시", "city": "옹진군"},
        {"place": "광주광역시", "city": "동구"},
        {"place": "광주광역시", "city": "서구"},
        {"place": "광주광역시", "city": "남구"},
        {"place": "광주광역시", "city": "북구"},
        {"place": "광주광역시", "city": "광산구"},
        {"place": "대전광역시", "city": "중구"},
        {"place": "대전광역시", "city": "서구"},
        {"place": "대전광역시", "city": "동구"},
        {"place": "대전광역시", "city": "유성구"},
        {"place": "대전광역시", "city": "대덕구"},
        {"place": "울산광역시", "city": "중구"},
        {"place": "울산광역시", "city": "남구"},
        {"place": "울산광역시", "city": "동구"},
        {"place": "울산광역시", "city": "북구"},
        {"place": "울산광역시", "city": "울주군"},
        {"place": "세종특별자치시", "city": "조치원읍"},
        {"place": "세종특별자치시", "city": "연기면"},
        {"place": "세종특별자치시", "city": "연동면"},
        {"place": "세종특별자치시", "city": "부강면"},
        {"place": "세종특별자치시", "city": "금남면"},
        {"place": "세종특별자치시", "city": "장군면"},
        {"place": "세종특별자치시", "city": "연서면"},
        {"place": "세종특별자치시", "city": "전의면"},
        {"place": "세종특별자치시", "city": "전동면"},
        {"place": "세종특별자치시", "city": "소정면"},
        {"place": "세종특별자치시", "city": "한솔동"},
        {"place": "세종특별자치시", "city": "새롬동"},
        {"place": "세종특별자치시", "city": "나성동"},
        {"place": "세종특별자치시", "city": "다정동"},
        {"place": "세종특별자치시", "city": "도담동"},
        {"place": "세종특별자치시", "city": "어진동"},
        {"place": "세종특별자치시", "city": "해밀동"},
        {"place": "세종특별자치시", "city": "아름동"},
        {"place": "세종특별자치시", "city": "종촌동"},
        {"place": "세종특별자치시", "city": "고운동"},
        {"place": "세종특별자치시", "city": "보람동"},
        {"place": "세종특별자치시", "city": "대평동"},
        {"place": "세종특별자치시", "city": "소담동"},
        {"place": "세종특별자치시", "city": "반곡동"},
        {"place": "경기도", "city": "수원시 장안구"},
        {"place": "경기도", "city": "수원시 권선구"},
        {"place": "경기도", "city": "수원시 팔달구"},
        {"place": "경기도", "city": "수원시 영통구"},
        {"place": "경기도", "city": "성남시 수정구"},
        {"place": "경기도", "city": "성남시 중원구"},
        {"place": "경기도", "city": "성남시 분당구"},
        {"place": "경기도", "city": "의정부시"},
        {"place": "경기도", "city": "안양시 만안구"},
        {"place": "경기도", "city": "안양시 동안구"},
        {"place": "경기도", "city": "부천시 원미구"},
        {"place": "경기도", "city": "부천시 소사구"},
        {"place": "경기도", "city": "부천시 오정구"},
        {"place": "경기도", "city": "광명시"},
        {"place": "경기도", "city": "동두천시"},
        {"place": "경기도", "city": "평택시"},
        {"place": "경기도", "city": "안산시 상록구"},
        {"place": "경기도", "city": "안산시 단원구"},
        {"place": "경기도", "city": "고양시 덕양구"},
        {"place": "경기도", "city": "고양시 일산동구"},
        {"place": "경기도", "city": "고양시 일산서구"},
        {"place": "경기도", "city": "과천시"},
        {"place": "경기도", "city": "구리시"},
        {"place": "경기도", "city": "남양주시"},
        {"place": "경기도", "city": "오산시"},
        {"place": "경기도", "city": "시흥시"},
        {"place": "경기도", "city": "군포시"},
        {"place": "경기도", "city": "의왕시"},
        {"place": "경기도", "city": "하남시"},
        {"place": "경기도", "city": "용인시 처인구"},
        {"place": "경기도", "city": "용인시 기흥구"},
        {"place": "경기도", "city": "용인시 수지구"},
        {"place": "경기도", "city": "파주시"},
        {"place": "경기도", "city": "이천시"},
        {"place": "경기도", "city": "안성시"},
        {"place": "경기도", "city": "김포시"},
        {"place": "경기도", "city": "화성시"},
        {"place": "경기도", "city": "광주시"},
        {"place": "경기도", "city": "양주시"},
        {"place": "경기도", "city": "포천시"},
        {"place": "경기도", "city": "여주시"},
        {"place": "경기도", "city": "연천군"},
        {"place": "경기도", "city": "가평군"},
        {"place": "경기도", "city": "양평군"},
        {"place": "강원특별자치도", "city": "춘천시"},
        {"place": "강원특별자치도", "city": "원주시"},
        {"place": "강원특별자치도", "city": "강릉시"},
        {"place": "강원특별자치도", "city": "동해시"},
        {"place": "강원특별자치도", "city": "태백시"},
        {"place": "강원특별자치도", "city": "속초시"},
        {"place": "강원특별자치도", "city": "삼척시"},
        {"place": "강원특별자치도", "city": "홍천군"},
        {"place": "강원특별자치도", "city": "횡성군"},
        {"place": "강원특별자치도", "city": "영월군"},
        {"place": "강원특별자치도", "city": "평창군"},
        {"place": "강원특별자치도", "city": "정선군"},
        {"place": "강원특별자치도", "city": "철원군"},
        {"place": "강원특별자치도", "city": "화천군"},
        {"place": "강원특별자치도", "city": "양구군"},
        {"place": "강원특별자치도", "city": "인제군"},
        {"place": "강원특별자치도", "city": "고성군"},
        {"place": "강원특별자치도", "city": "양양군"},
        {"place": "충청북도", "city": "청주시 상당구"},
        {"place": "충청북도", "city": "청주시 흥덕구"},
        {"place": "충청북도", "city": "청주시 서원구"},
        {"place": "충청북도", "city": "청주시 청원구"},
        {"place": "충청북도", "city": "충주시"},
        {"place": "충청북도", "city": "제천시"},
        {"place": "충청북도", "city": "보은군"},
        {"place": "충청북도", "city": "옥천군"},
        {"place": "충청북도", "city": "영동군"},
        {"place": "충청북도", "city": "증평군"},
        {"place": "충청북도", "city": "진천군"},
        {"place": "충청북도", "city": "괴산군"},
        {"place": "충청북도", "city": "음성군"},
        {"place": "충청북도", "city": "단양군"},
        {"place": "충청남도", "city": "천안시 동남구"},
        {"place": "충청남도", "city": "천안시 서북구"},
        {"place": "충청남도", "city": "공주시"},
        {"place": "충청남도", "city": "보령시"},
        {"place": "충청남도", "city": "아산시"},
        {"place": "충청남도", "city": "서산시"},
        {"place": "충청남도", "city": "논산시"},
        {"place": "충청남도", "city": "계룡시"},
        {"place": "충청남도", "city": "당진시"},
        {"place": "충청남도", "city": "금산군"},
        {"place": "충청남도", "city": "부여군"},
        {"place": "충청남도", "city": "서천군"},
        {"place": "충청남도", "city": "청양군"},
        {"place": "충청남도", "city": "홍성군"},
        {"place": "충청남도", "city": "예산군"},
        {"place": "충청남도", "city": "태안군"},
        {"place": "전북특별자치도", "city": "전주시 완산구"},
        {"place": "전북특별자치도", "city": "전주시 덕진구"},
        {"place": "전북특별자치도", "city": "군산시"},
        {"place": "전북특별자치도", "city": "익산시"},
        {"place": "전북특별자치도", "city": "정읍시"},
        {"place": "전북특별자치도", "city": "남원시"},
        {"place": "전북특별자치도", "city": "김제시"},
        {"place": "전북특별자치도", "city": "완주군"},
        {"place": "전북특별자치도", "city": "진안군"},
        {"place": "전북특별자치도", "city": "무주군"},
        {"place": "전북특별자치도", "city": "장수군"},
        {"place": "전북특별자치도", "city": "임실군"},
        {"place": "전북특별자치도", "city": "순창군"},
        {"place": "전북특별자치도", "city": "고창군"},
        {"place": "전북특별자치도", "city": "부안군"},
        {"place": "전라남도", "city": "목포시"},
        {"place": "전라남도", "city": "여수시"},
        {"place": "전라남도", "city": "순천시"},
        {"place": "전라남도", "city": "나주시"},
        {"place": "전라남도", "city": "광양시"},
        {"place": "전라남도", "city": "담양군"},
        {"place": "전라남도", "city": "곡성군"},
        {"place": "전라남도", "city": "구례군"},
        {"place": "전라남도", "city": "고흥군"},
        {"place": "전라남도", "city": "보성군"},
        {"place": "전라남도", "city": "화순군"},
        {"place": "전라남도", "city": "장흥군"},
        {"place": "전라남도", "city": "강진군"},
        {"place": "전라남도", "city": "해남군"},
        {"place": "전라남도", "city": "영암군"},
        {"place": "전라남도", "city": "무안군"},
        {"place": "전라남도", "city": "함평군"},
        {"place": "전라남도", "city": "영광군"},
        {"place": "전라남도", "city": "장성군"},
        {"place": "전라남도", "city": "완도군"},
        {"place": "전라남도", "city": "진도군"},
        {"place": "전라남도", "city": "신안군"},
        {"place": "경상북도", "city": "포항시 남구"},
        {"place": "경상북도", "city": "포항시 북구"},
        {"place": "경상북도", "city": "경주시"},
        {"place": "경상북도", "city": "김천시"},
        {"place": "경상북도", "city": "안동시"},
        {"place": "경상북도", "city": "구미시"},
        {"place": "경상북도", "city": "영주시"},
        {"place": "경상북도", "city": "영천시"},
        {"place": "경상북도", "city": "상주시"},
        {"place": "경상북도", "city": "문경시"},
        {"place": "경상북도", "city": "경산시"},
        {"place": "경상북도", "city": "의성군"},
        {"place": "경상북도", "city": "청송군"},
        {"place": "경상북도", "city": "영양군"},
        {"place": "경상북도", "city": "영덕군"},
        {"place": "경상북도", "city": "청도군"},
        {"place": "경상북도", "city": "고령군"},
        {"place": "경상북도", "city": "성주군"},
        {"place": "경상북도", "city": "칠곡군"},
        {"place": "경상북도", "city": "예천군"},
        {"place": "경상북도", "city": "봉화군"},
        {"place": "경상북도", "city": "울진군"},
        {"place": "경상북도", "city": "울릉군"},
        {"place": "경상남도", "city": "창원시 마산합포구"},
        {"place": "경상남도", "city": "창원시 마산회원구"},
        {"place": "경상남도", "city": "창원시 의창구"},
        {"place": "경상남도", "city": "창원시 성산구"},
        {"place": "경상남도", "city": "창원시 진해구"},
        {"place": "경상남도", "city": "진주시"},
        {"place": "경상남도", "city": "통영시"},
        {"place": "경상남도", "city": "사천시"},
        {"place": "경상남도", "city": "김해시"},
        {"place": "경상남도", "city": "밀양시"},
        {"place": "경상남도", "city": "거제시"},
        {"place": "경상남도", "city": "양산시"},
        {"place": "경상남도", "city": "의령군"},
        {"place": "경상남도", "city": "함안군"},
        {"place": "경상남도", "city": "창녕군"},
        {"place": "경상남도", "city": "고성군"},
        {"place": "경상남도", "city": "남해군"},
        {"place": "경상남도", "city": "하동군"},
        {"place": "경상남도", "city": "산청군"},
        {"place": "경상남도", "city": "함양군"},
        {"place": "경상남도", "city": "거창군"},
        {"place": "경상남도", "city": "합천군"},
        {"place": "제주특별자치도", "city": "제주시"},
        {"place": "제주특별자치도", "city": "서귀포시"}
    ]


    # 결과를 저장할 딕셔너리 (중복 제거를 위해)
    results_dict = {}
    total_count = 0
    batch_number = 1

    # 고유한 파일 이름 생성
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"search_results_{timestamp}.xlsx"

    # 중복 체크를 위한 전체 결과 저장 딕셔너리
    overall_results_dict = {}

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
                address_key = (place.get("address"), place.get("roadAddress"), place.get("abbrAddress"))
                if address_key not in overall_results_dict:
                    overall_results_dict[address_key] = place
                    place['entry_place'] = entry["place"]
                    place['entry_city'] = entry["city"]
                    place['page'] = page
                    total_count += 1

                    # 임시 딕셔너리에 추가
                    results_dict[address_key] = place
                else:
                    existing_place = overall_results_dict[address_key]
                    if existing_place.get('tel') is None:
                        overall_results_dict[address_key] = place
                        place['entry_place'] = entry["place"]
                        place['entry_city'] = entry["city"]
                        place['page'] = page

                        # 임시 딕셔너리에 추가
                        results_dict[address_key] = place

            page += 1
            print(f"100단위 카운트 ============== {len(results_dict)}==================")
            print(f"현재까지 작업한 전체 카운트: {total_count}")

            # 100개마다 저장
            if len(results_dict) >= 100:
                save_to_excel(results_dict, file_name)
                batch_number += 1
                results_dict.clear()

    # 남은 데이터 저장
    if results_dict:
        save_to_excel(results_dict, file_name)

    end_time = datetime.now()
    print(f"종료 시간: {end_time.strftime('%Y.%m.%d %H:%M:%S')}")

    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"총 걸린 시간: {int(hours)}시간 {int(minutes)}분 {int(seconds)}초")
    print(f"최종 작업한 전체 카운트: {total_count}")


if __name__ == "__main__":
    main()

