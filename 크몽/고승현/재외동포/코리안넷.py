import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 페이지 요청 함수
def fetch_page_content(url, offset):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    full_url = f"{url}&article.offset={offset}"
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    return response.text

# 이미지 URL 가져오는 함수
def fetch_image_url(content_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    response = requests.get(content_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    img_tag = soup.select_one(".contents_wrap .contents img")
    if img_tag and 'src' in img_tag.attrs:
        return "https://www.korean.net" + img_tag["src"]
    return ""

# 데이터 파싱 함수
def parse_content(html, base_url, category):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".tbl_type1 tbody tr")
    data_list = []

    for row in rows:
        content = {
            "콘텐츠 이미지 URL": "",
            "콘텐츠 주소": "",
            "콘텐츠 명": "",
            "콘텐츠 공개 연도": "",
            "카테고리": category
        }

        # 콘텐츠 명
        title_tag = row.select_one(".inputTitle")
        if title_tag:
            content["콘텐츠 명"] = title_tag.get_text(strip=True)

        # 콘텐츠 공개 연도
        date_tag = row.select_one(".t1_date.date")
        if date_tag:
            content["콘텐츠 공개 연도"] = date_tag.get_text(strip=True)

        # 콘텐츠 주소
        link_tag = row.select_one(".viewLink")
        if link_tag and 'href' in link_tag.attrs:
            href = link_tag["href"]
            content["콘텐츠 주소"] = f"{base_url}.do{href}"

            # 콘텐츠 이미지 URL
            article_no = href.split("articleNo=")[1]
            content_url = f"{base_url}.do?mode=view&articleNo={article_no}"
            content["콘텐츠 이미지 URL"] = fetch_image_url(content_url)

        data_list.append(content)
        time.sleep(0.1)  # 요청 간 딜레이 추가

    return data_list

# 엑셀 저장 함수
def save_to_excel(data_list, filename="해외통신원_재외동포단체_한인회_소식.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"엑셀 파일 '{filename}'로 저장되었습니다.")

# 메인 함수
def main():
    all_data = []

    # URL 목록과 페이지 범위
    urls = [
        {"url": "https://www.korean.net/portal/global/pg_news_local", "pages": 280, "category": "해외통신원 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_group", "pages": 138, "category": "재외동포단체 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_hanin", "pages": 10, "category": "한인회 운영사례"}
    ]

    # 각 URL별로 데이터 수집
    for item in urls:
        base_url = item["url"]
        category = item["category"]
        max_pages = item["pages"]

        for page_no in range(max_pages):
            offset = page_no * 10
            print(f"{category} - 페이지 {page_no + 1}/{max_pages} 처리 중...")
            html = fetch_page_content(base_url, offset)
            page_data = parse_content(html, base_url, category)
            all_data.extend(page_data)

    # 엑셀 저장
    save_to_excel(all_data)

if __name__ == "__main__":
    main()
