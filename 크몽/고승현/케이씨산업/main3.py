import time
import requests
import json
from bs4 import BeautifulSoup
import math
from datetime import datetime
from openpyxl import Workbook
import pandas as pd
import re

exclude_keywords = [
    "창호교체",
    "소방공사",
    "정보통신공사",
    "전등교체",
    "외벽방수"
]

required_keywords = [
    "신축사업",
    "설계공모",
    "실시설계",
    "공사",
    "설계",
    "용역",
    "설치",
]

priority1_keywords = [
    "모듈러",
    "철골 모듈러",
    "콘크리트 모듈러",
    "모듈러주택",
    "모듈러 건축"
]

priority2_keywords = [
    "기숙사",
    "농산어촌",
    "청년주택",
    "실버타운",
    "임대주택",
    "실버주택",
    "공용실버주택",
    "공공주택사업",
    "농촌보금자리",
    "농업 근로자",
    "계절 근로자",
    "트리하우스",
    "힐링타운",
    "근로자 휴게시설",
    "청년 보금자리",
    "청년 근로자",
    "외국인 근로자",
    "청년하우스",
    "농촌유학타운",
    "간호복지 기숙사",
    "만원주택",
    "외국인 정착",
    "두지역 살기",
    "귀농인의 집",
    "귀농귀촌 활성화",
    "이색숙박시설",
    "청년마을",
    "경로당",
    "지역개발사업",
    "근린생활시설",
    "주거시설",
    "아파트",
    "주택",
    "타운하우스",
    "연립주택",
    "상가주택",
    "마을조성"
]

def newPrint(text):
    print(f"{get_current_time()} - {text}")

def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

# 국방전자조달시스템
def fetch_data_d2b(date_from, date_to, page):
    url = 'https://www.d2b.go.kr/mainBidAnnounceList.json'
    payload = {
        'anmt_name': '',
        'mnuf_code': '',
        'date_from': date_from,
        'date_to': date_to,
        'search_divs': '',
        'gubun': '1',
        'anmt_divs': '',
        'numb_divs': '',
        'dprt_name': '',
        'dprt_code': '',
        'edix_gtag': '',
        'chgDate': '-6m',
        'sch_typeA': 'true',
        'sch_typeB': 'true',
        'sch_typeC': 'true',
        'sch_typeD': 'true',
        'currentPageNo': page
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        newPrint(f"Failed to retrieve data: {response.status_code}")
        newPrint(response.text)
        return None

def save_to_excel_d2b(data, filename='d2b.xlsx'):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Bids"

    headers = [
        # "순번",
        "업무구분",
        "공고구분",
        "공고일자",
        "판단번호(구매요청번호)",
        "입찰건명(사업명)",
        "발주기관",
        "계약방법",
        # "입찰형태",
        "기초예가"
    ]
    sheet.append(headers)

    for item in data:
        row = [
            # item.get("rnum"),       ## 순번
            item.get("divs"),       ## 업무구분
            item.get("codeVld1"),   ## 공고구분
            item.get("anmtDate"),   ## 공고일자
            item.get("dcsnNumb"),
            item.get("rpstItnm"),
            item.get("codeVld3"),
            item.get("codeVld4"),
            # item.get("bidxPrmt"),
            item.get("bsicExpt")
        ]
        sheet.append(row)

    workbook.save(filename)

def d2b():

    date_from = '20231222'
    date_to = '20240622'

    # 전체 갯수 구하기
    totlCntForItems = fetch_data_d2b(date_from, date_to, 1)

    if totlCntForItems:
        totlPage = math.ceil(int(totlCntForItems["totlCnt"]) / 20)
        newPrint(f"전체 페이지 : {totlPage}")

        datas = []

        for page in range(1, int(totlPage) + 1):
            newPrint(f"현재 페이지 : {page}")
            time.sleep(2)
            items = fetch_data_d2b(date_from, date_to, page)

            if items and "list" in items:
                itemList = items["list"]
                filtered_itemList = filter_items(itemList, "rpstItnm")
                datas.extend(filtered_itemList)

        newPrint(f"전체 리스트 len   : {len(datas)}")
        save_to_excel_d2b(datas)


def getSoup(from_order_era_month, from_order_era_year, from_release_dt,
            record_count_per_page, to_order_era_month, to_order_era_year,
            to_release_dt, current_page_no):
    url = "https://www.g2b.go.kr:8101/ep/preparation/orderplan/orderplanPubList.do"

    params = {
        "bizNm": "",
        "downloadRange": "1",
        "fromOrderEra": from_order_era_year + from_order_era_month,
        "fromOrderEraMonth": from_order_era_month,
        "fromOrderEraYear": from_order_era_year,
        "fromReleaseDt": from_release_dt,
        "industry": "",
        "industry1": "",
        "industry2": "",
        "instAddr": "",
        "instCd": "",
        "instNm": "",
        "popId": "",
        "popTaskTypeCd": "",
        "popupYn": "",
        "ppsWay": "",
        "recordCountPerPage": record_count_per_page,
        "taskClCd": "3",
        "taskTypeCd": "",
        "taskTypeCd0": "",
        "taskTypeCd1": "",
        "taskTypeCd2": "",
        "taskTypeCd3": "",
        "taskTypeCd4": "",
        "toOrderEra": to_order_era_year + to_order_era_month,
        "toOrderEraMonth": to_order_era_month,
        "toOrderEraYear": to_order_era_year,
        "toReleaseDt": to_release_dt,
        "totalRecordCount": "1",
        "userCl": "",
        "voTaskClCd": "3",
        "currentPageNo": current_page_no
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Content-Language": "ko-KR",
        "Content-Type": "text/html; charset=EUC-KR",
        "Origin-Agent-Cluster": "?0"
    }

    response = None

    try:
        time.sleep(1)
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # 4xx, 5xx 응답을 예외로 처리
        response.encoding = 'EUC-KR'
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if response is not None:
            print(f"Response text: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

    return None

def getTotalItems(soup):
    # div class가 inforight인 것을 찾기
    info_right_div = soup.find('div', class_='inforight')

    totalItems = 0
    if info_right_div:
        # span class가 page인 것을 찾기
        span_page = info_right_div.find('span', class_='page')
        if span_page:
            span_text = span_page.text
            # "검색건수 :9,467건"에서 숫자만 추출
            match = re.search(r'\d{1,3}(,\d{3})*', span_text)
            if match:
                number_str = match.group()
                totalItems = int(number_str.replace(',', ''))

    return totalItems


current_index = 0

# 나라장터 국가종합전자조달
def fetch_data_g2b(from_order_era_month, from_order_era_year,
                   from_release_dt,
                   record_count_per_page,
                   to_order_era_month, to_order_era_year,
                   to_release_dt,
                   current_page_no):

    global current_index  # 전역 변수 사용 선언

    soup = getSoup(from_order_era_month, from_order_era_year, from_release_dt,
                   record_count_per_page, to_order_era_month, to_order_era_year,
                   to_release_dt, current_page_no)

    if soup is None:
        return []

    # div class가 inforight인 것을 찾기
    totalItems = getTotalItems(soup)
    totalPages = math.ceil(totalItems / int(record_count_per_page))

    newPrint(f"totalItems : {totalItems}")
    newPrint(f"totalPages : {totalPages}")

    data = []

    for current_page_no in range(1, int(totalPages) + 1):
        soup = getSoup(from_order_era_month, from_order_era_year, from_release_dt,
                       record_count_per_page, to_order_era_month, to_order_era_year,
                       to_release_dt, current_page_no)

        # div class가 results인 것 안에 table을 찾고, 그 안에 tbody들을 찾기
        result_div = soup.find('div', class_='results')
        if result_div:
            tbodies = result_div.find_all('tbody')

            object_list = []

            # 각 tbody에 대해 데이터를 추출
            for index, tbody in enumerate(tbodies):

                current_index = current_index +  1

                newPrint(f"================ current_page_no : {current_page_no} / {totalPages} ===========================")
                newPrint(f"================ now_index : {current_index} / {totalItems} =====================================")

                row = {}

                trs = tbody.find_all('tr')

                # 2번째 tr의 2, 3, 4번째 td의 값을 추출
                if len(trs) > 1:
                    second_tr = trs[1]
                    tds = second_tr.find_all('td')
                    if len(tds) >= 4:
                        row['업무'] = tds[1].text.strip()
                        row['발주기관'] = tds[2].text.strip()
                        row['공사명'] = tds[3].text.strip()

                # 3번째 tr의 1, 2, 3, 4, 5, 6, 7, 8번째 td의 값을 추출
                if len(trs) > 2:
                    third_tr = trs[2]
                    tds = third_tr.find_all('td')
                    if len(tds) >= 8:
                        row['유형'] = tds[0].text.strip()
                        row['발주시기'] = tds[1].text.strip()
                        row['조달방식'] = tds[2].text.strip()
                        row['계약방법'] = tds[3].text.strip()
                        row['발주도급금액(집행금액)'] = tds[4].text.strip()
                        row['발주관급자재비(집행잔액)'] = tds[5].text.strip()
                        row['발주기타금액(전년금액)'] = tds[6].text.strip()
                        row['발주합계금액(총부기금액)'] = tds[7].text.strip()

                # 객체 리스트에 추가
                object_list.append(row)

            filtered_items = filter_items(object_list, "공사명")

            newPrint(f"filtered_items : {filtered_items}")

            data.extend(filtered_items)

    print(f"data len : {len(data)}")

    return data


def save_to_excel_g2b(data, filename):
    if not data:
        print("No data to save.")
        return

    df = pd.DataFrame(data)

    # 예상 컬럼명과 매칭
    if len(df.columns) == 11:
        df.columns = ["업무", "발주기관", "공사명", "유형", "발주시기", "조달방식", "계약방법",
                      "발주도급금액(집행금액)", "발주관급자재비(집행잔액)", "발주기타금액(전년금액)", "발주합계금액(총부기금액)"]

    # Save to Excel using xlsxwriter
    df.to_excel(filename, index=False, engine='xlsxwriter')

    print(f"Data saved to {filename}")


def filter_items(items, key):

    filtered_items = []

    for index, item in enumerate(items):
        name = item.get(key, "")
        print(f" index {index} : {name}")

        # exclude_keywords 검사
        if any(keyword in name for keyword in exclude_keywords):
            print("exclude_keywords")
            continue

        # required_keywords 검사
        if not any(keyword in name for keyword in required_keywords):
            print(f"required_keywords")
            continue

        # priority1_keywords 또는 priority2_keywords 검사
        if not (any(keyword in name for keyword in priority1_keywords) or
                any(keyword in name for keyword in priority2_keywords)):
            print(f"priority1_keywords 또는 priority2_keywords 검사")
            continue

        print(f" 살아남은 이름 : {name}")

        filtered_items.append(item)

    return filtered_items

def g2b():
    # Example usage

    from_order_era_month = "06"
    from_order_era_year = "2024"
    from_release_dt = "2023/12/22"
    record_count_per_page = "10"
    to_order_era_month = "07"
    to_order_era_year = "2024"
    to_release_dt = "2024/06/22"

    data = fetch_data_g2b(from_order_era_month, from_order_era_year, from_release_dt,
                          record_count_per_page, to_order_era_month, to_order_era_year,
                          to_release_dt, 1)

    save_to_excel_g2b(data, "g2b_bids.xlsx")



# 나라장터 국가종합전자조달
def main():

    # 국방전자조달시스템
    # d2b()

    # 나라장터 국가종합전자조달
    g2b()



if __name__ == "__main__":
    main()
