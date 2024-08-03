import requests
from bs4 import BeautifulSoup
import re
import time
import random
import pandas as pd
import json
import os

def send_post_request(url, payload):
    """POST 요청을 보내고 응답을 반환하는 함수"""
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # 요청 성공 여부 확인
        return response.text
    except requests.RequestException as e:
        print(f"HTTP 요청 에러: {e}")
        return None

def parse_html_for_ids(html, page_index):
    """HTML을 파싱하여 필요한 ID들을 추출하는 함수"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 정규 표현식 패턴: javascript:dmoelRequst('2018-40');
        pattern = re.compile(r"javascript:dmoelRequst\('([^']+)'\);")

        results = []
        for td in soup.find_all("td", class_="txt_left elli"):
            a_tag = td.find("a")
            if a_tag and 'href' in a_tag.attrs:
                match = pattern.search(a_tag['href'])
                if match:
                    results.append(match.group(1))

        print(f"Page {page_index}: Collected IDs - {results}")
        return results
    except Exception as e:
        print(f"HTML 파싱 에러: {e}")
        return []

def parse_institution_details(eclstNo, page_num, detail_index):
    url = "https://edu.kead.or.kr/aisd/search/EclstProfile.do"
    payload = {'eclstNo': eclstNo, 'pageNum': 1}
    response_text = send_post_request(url, payload)
    if response_text is None:
        return None

    soup = BeautifulSoup(response_text, 'html.parser')
    details = {}

    try:
        t_con_sections = soup.find_all("div", class_="t-con")
        if len(t_con_sections) < 5:
            print(f"Expected at least 5 t-con sections for institution {eclstNo}, but found {len(t_con_sections)}")
            return None

        # 교육기관 정보
        profile_section = t_con_sections[0]
        img_tag = profile_section.find("span", class_="profile-info").find("img")
        if img_tag:
            img_url = img_tag['src']
            if not img_url.startswith('http'):
                img_url = 'https://edu.kead.or.kr' + img_url
            details["이미지 URL"] = img_url
        else:
            details["이미지 URL"] = ""

        table_rows = profile_section.find("table", class_="view-table type-2").find("tbody").find_all("tr")
        for row in table_rows:
            ths = row.find_all("th")
            tds = row.find_all("td")
            for th, td in zip(ths, tds):
                th_text = th.text.strip()
                td_text = td.text.strip()
                if th_text in ["교육기관명", "교육종목", "연락처", "이메일", "소재지", "홈페이지"]:
                    details[th_text] = td_text
                elif th_text == "활동지역":
                    details["활동지역"] = ", ".join([li.text.strip() for li in td.find("ul").find_all("li")])
                elif th_text == "활동요일":
                    details["활동요일"] = ", ".join([li.text.strip() for li in td.find("ul").find_all("li")])

        # 홍보자료
        promo_section = t_con_sections[1]
        promo_rows = promo_section.find("table", class_="view-table type-2").find("tbody").find_all("tr")
        for row in promo_rows:
            ths = row.find_all("th")
            tds = row.find_all("td")
            for th, td in zip(ths, tds):
                th_text = th.text.strip()
                td_text = td.text.strip()
                if th_text in ["샘플 강의 동영상", "홍보자료1", "홍보자료2"]:
                    details[th_text] = td_text

        # 기관소개
        intro_section = t_con_sections[2]
        intro_rows = intro_section.find("table", class_="view-table type-2").find("tbody").find_all("tr")
        for row in intro_rows:
            ths = row.find_all("th")
            tds = row.find_all("td")
            for th, td in zip(ths, tds):
                th_text = th.text.strip()
                td_text = td.find("textarea").text.strip() if td.find("textarea") else td.text.strip()
                if th_text in ["주요연혁", "주요활동"]:
                    details[th_text] = td_text


        # 강의소개
        lecture_section = t_con_sections[3]
        lecture_rows = lecture_section.find("table", class_="view-table type-2").find("tbody").find_all("tr")
        for row in lecture_rows:
            ths = row.find_all("th")
            tds = row.find_all("td")
            for th, td in zip(ths, tds):
                th_text = th.text.strip()
                td_text = td.find("textarea").text.strip() if td.find("textarea") else td.text.strip()
                if th_text in ["강의소개", "강의목차"]:
                    details[th_text] = td_text


        # 최근 교육 실적
        recent_education_section = t_con_sections[4]
        recent_education_table = recent_education_section.find("table", class_="list-table")
        education_records = []
        no_records = recent_education_table.find("td", class_="ac")
        if no_records and "등록된 내용이 없습니다." in no_records.text:
            education_records.append({
                "교육일자": "",
                "교육시간": "",
                "교육 의뢰 기관": "",
                "교육장소": ""
            })
        else:
            for row in recent_education_table.find("tbody").find_all("tr"):
                record = {
                    "교육일자": row.find_all("td")[0].text.strip(),
                    "교육시간": row.find_all("td")[1].text.strip(),
                    "교육 의뢰 기관": row.find_all("td")[2].text.strip(),
                    "교육장소": row.find_all("td")[3].text.strip()
                }
                education_records.append(record)
        details["최근 교육 실적"] = json.dumps(education_records, ensure_ascii=False)


    except Exception as e:
        print(f"상세 정보 파싱 에러: {e} for eclstNo {eclstNo}")
        return None

    print(f"Detail {detail_index}: {details}")
    return details

def save_to_excel(all_details, file_name="institution_details.xlsx"):
    df = pd.DataFrame(all_details)

    # 순서 맞추기: 교육기관 정보 -> 홍보자료 -> 강의소개 -> 기관소개 -> 최근 교육 실적 -> 페이지
    ordered_columns = [
        '교육기관명', '교육종목', '연락처', '이메일', '이미지 URL',
        '한줄소개', '홈페이지', '활동요일', '활동지역', '소재지',
        '샘플 강의 동영상', '홍보자료1', '홍보자료2',
        '주요연혁', '주요활동',
        '강의소개', '강의목차',
        '최근 교육 실적'
    ]

    # 빈 데이터프레임에 컬럼 추가
    for col in ordered_columns:
        if col not in df.columns:
            df[col] = ''

    df = df[ordered_columns]

    if os.path.exists(file_name):
        # 기존 파일이 있을 경우 데이터 추가
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            startrow = writer.sheets['Sheet1'].max_row  # 기존 데이터의 마지막 행 번호
            df.to_excel(writer, index=False, header=False, startrow=startrow)
    else:
        # 기존 파일이 없을 경우 새로운 파일 생성
        df.to_excel(file_name, index=False)

def main():
    url = "https://edu.kead.or.kr/aisd/search/EclstSearchList.do"
    page_num = 1
    all_ids = []
    id_index = 1


    # 교육기관 ID 수집
    while True:
        payload = {'pageNum': page_num, 'pageType': 'SEARCH'}
        response_text = send_post_request(url, payload)
        if response_text is not None:
            ids = parse_html_for_ids(response_text, id_index)
            if not ids:
                break
            all_ids.extend(ids)
            break
            page_num += 1
            id_index += 1
            time.sleep(2)  # 2~3초 랜덤하게 쉬기
        else:
            print("데이터를 가져오지 못했습니다.")
            break

    all_details = []
    file_count = 1
    detail_index = 1

    # 각 교육기관에 대한 상세 정보 수집
    for index, eclstNo in enumerate(all_ids, start=1):
        print(f"Processing institution {index}: {eclstNo}")
        details = parse_institution_details(eclstNo, index, detail_index)
        if details:
            all_details.append(details)
            print(f"Finished processing institution {index}: {eclstNo}")
            detail_index += 1

        # 100개마다 엑셀 파일로 저장
        if index % 100 == 0:
            save_to_excel(all_details, "장애인 교육기관.xlsx")
            file_count += 1
            all_details = []  # 저장 후 리스트 초기화

        time.sleep(2)  # 2~3초 랜덤하게 쉬기

    # 남은 데이터 저장
    if all_details:
        save_to_excel(all_details, "장애인 교육기관.xlsx")

if __name__ == "__main__":
    main()
