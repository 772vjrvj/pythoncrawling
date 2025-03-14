import requests
from bs4 import BeautifulSoup
import pandas as pd

# 페이지 요청 함수
def fetch_page_content(url, page_no, payload_base):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    payload = payload_base.copy()
    payload["p_pageno"] = page_no
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return response.text

# 데이터 파싱 함수
def parse_content(html, page_no, category):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".temp_table01 tbody tr")
    data_list = []

    for index, row in enumerate(rows):

        columns = row.find_all("td")
        content = {
            "콘텐츠 명": "",
            "콘텐츠 분류": "글",
            "공개일자": "",
            "노출매체": "스터디코리안 웹사이트",
            "퀄리티": "",
            "콘텐츠 대상지역": "",
            "콘텐츠 내용": "",
            "콘텐츠 저작권 소유처": "스터디코리안",
            "라이선스": "제작 저작권 소유",
            "콘텐츠 시청 방법": "스터디코리안 웹사이트",
            "이미지 url": "",
            "콘텐츠 주소": "",
            "카테고리": category
        }

        # 3번째 td의 "now_school_L" 클래스 내의 dt 태그 안에 a 태그 안의 span 태그의 텍스트
        content["콘텐츠 명"] = columns[2].find(class_="now_school_L").find("dt").find("a").find("span").get_text(strip=True)

        location_dd = columns[2].find(class_="now_school_L").find("dd", class_="school")
        if location_dd:
            # location_dd 텍스트에서 첫 번째 단어만 추출 (예: "[러시아/카잔볼가한글학교]"에서 "러시아"만)
            location_text = location_dd.get_text(strip=True)
            country_name = location_text.split('/')[0].replace('[', '').strip()  # '러시아'만 추출하고 '[' 제거
            content["콘텐츠 대상지역"] = country_name

        content["콘텐츠 내용"] = (
            "재외동포 인터뷰"
            if "인터뷰" in content["콘텐츠 명"]
            else f"({content['콘텐츠 대상지역']}) 재외동포 일상"
        )

        content["콘텐츠 분류"] = "인터뷰" if "인터뷰" in content["콘텐츠 명"] else "글"

        # 2번째 td에서 이미지 URL과 상세 URL 생성
        img_tag = columns[1].find("img")
        if img_tag and 'src' in img_tag.attrs:
            content["이미지 url"] = "https://study.korean.net" + img_tag["src"]

        onclick_attr = columns[1].find("a")["onclick"]
        if onclick_attr:
            p_bdseq, p_dispnum = onclick_attr.split("'")[1], onclick_attr.split("'")[3]
            content["콘텐츠 주소"] = (
                f"https://study.korean.net/servlet/action.cmt.StudentNewsAction?"
                f"p_tabseq=161&p_process=view&p_bdseq={p_bdseq}&p_pageno={page_no}&p_dispnum={p_dispnum}&p_menuCd=m404"
            )

        # 6번째 td의 공개 연도 텍스트
        content["공개일자"] = columns[5].get_text(strip=True)
        print(f"index : {index}, content : {content}")
        data_list.append(content)


    return data_list

# 엑셀 저장 함수
def save_to_excel(data_list, filename="스터디코리안 학생소식.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"엑셀 파일 '{filename}'로 저장되었습니다.")

# 메인 함수
def main():
    all_data = []

    # 1. 스터디코리안 학생소식 167페이지
    student_url = "https://study.korean.net/servlet/action.cmt.StudentNewsAction"
    student_payload = {
        "p_tabseq": 161,
        "p_process": "listPage",
        "p_menuCd": "m404"
    }
    for page_no in range(1, 168):  # 1부터 167까지
        print(f"스터디코리안 학생소식 - 페이지 {page_no} 처리 중...")
        html = fetch_page_content(student_url, page_no, student_payload)
        page_data = parse_content(html, page_no, "스터디코리안 학생소식")
        all_data.extend(page_data)



    # 2. 스터디코리안 한글학교 소식 445페이지
    school_url = "https://study.korean.net/servlet/action.cmt.EventAction"
    school_payload = {
        "p_process": "listPage",
        "p_menuCd": "m401"
    }
    for page_no in range(1, 446):  # 1부터 445까지
        print(f"스터디코리안 한글학교 소식 - 페이지 {page_no} 처리 중...")
        html = fetch_page_content(school_url, page_no, school_payload)
        page_data = parse_content(html, page_no, "스터디코리안 한글학교 소식")
        all_data.extend(page_data)


    # 엑셀 저장
    save_to_excel(all_data)

if __name__ == "__main__":
    main()
