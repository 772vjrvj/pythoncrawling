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
            "콘텐츠 이미지 URL": "",
            "콘텐츠 주소": "",
            "콘텐츠 명": "",
            "콘텐츠 공개 연도": "",
            "카테고리": category
        }

        # 2번째 td에서 이미지 URL과 상세 URL 생성
        img_tag = columns[1].find("img")
        if img_tag and 'src' in img_tag.attrs:
            content["콘텐츠 이미지 URL"] = "https://study.korean.net" + img_tag["src"]

        onclick_attr = columns[1].find("a")["onclick"]
        if onclick_attr:
            p_bdseq, p_dispnum = onclick_attr.split("'")[1], onclick_attr.split("'")[3]
            content["콘텐츠 주소"] = (
                f"https://study.korean.net/servlet/action.cmt.EventAction?"
                f"p_process=view&p_bdseq={p_bdseq}&p_pageno={page_no}&p_dispnum={p_dispnum}&p_menuCd=m404"
            )

        # 3번째 td의 텍스트
        content["콘텐츠 명"] = columns[2].find(class_="now_school_L").find("dt").find("a").find("span").get_text(strip=True)

        # 6번째 td의 공개 연도 텍스트 (예외 처리 추가)
        try:
            content["콘텐츠 공개 연도"] = columns[5].get_text(strip=True)
        except (IndexError, AttributeError):
            content["콘텐츠 공개 연도"] = ""  # 에러 발생 시 공백으로 설정
        print(f"index : {index}, content : {content}")
        data_list.append(content)

    return data_list

# 엑셀 저장 함수
def save_to_excel(data_list, filename="스터디코리안 한글학교.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"엑셀 파일 '{filename}'로 저장되었습니다.")

# 메인 함수
def main():
    all_data = []

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
