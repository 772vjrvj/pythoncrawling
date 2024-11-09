import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 공통 헤더
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "cookie": "ACEUCI=1; ACEUCI=1; portal_visited=20241109041401813001; org.springframework.web.servlet.i18n.CookieLocaleResolver.LOCALE=ko; JSESSIONID=5vDqEB7pY39ZkpcG7yNJ9Bs34ZSyD39zw2oJZ8uBxvp4f2L1vrIDPm8UrAHQcAjj.blue1_servlet_engine1; ACEFCID=UID-672E62F7CF671048EACE546D; _ga=GA1.1.859242966.1731093240; AUFAH1A45931692707=1731093240136334028|2|1731093240136334028|1|1731093239905234028; ACEUACS=1731093239905234028; AUAH1A45931692707=1731097002678702851%7C3%7C1731093240136334028%7C1%7C1731093239905234028%7C1; _ga_C8W44QRLHV=GS1.1.1731097002.2.1.1731097275.4.0.0; ASAH1A45931692707=1731097002678702851%7C1731097275423701211%7C1731097002678702851%7C0%7Cbookmark; ARAH1A45931692707=httpswwwkoreannetportalglobalpgnewslocaldomodelistarticleLimit10articleoffset10bookmark; RT=\"z=1&dm=www.korean.net&si=2e6c3380-5413-4448-a9ad-49c7a645d1a5&ss=m394cosf&sl=0&tt=0&bcn=%2F%2F684d0d46.akstat.io%2F\"",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}

# 페이지 요청 함수
def fetch_page_content(url, offset):
    full_url = f"{url}?mode=list&&articleLimit=10&article.offset={offset}"
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    return response.text

# 이미지 URL 가져오는 함수
def fetch_image_url(content_url):
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

    for index, row in enumerate(rows):
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
            content["콘텐츠 주소"] = f"{base_url}{href}"

            # 콘텐츠 이미지 URL
            article_no = href.split("articleNo=")[1]
            content_url = f"{base_url}?mode=view&articleNo={article_no}"  # '.do' 없이 구성
        content["콘텐츠 이미지 URL"] = fetch_image_url(content_url)
        print(f'index : {index}, content : {content}')
        data_list.append(content)
        time.sleep(0.1)  # 요청 간 딜레이 추가

    return data_list

# 엑셀 저장 함수
def save_to_excel(data_list, filename="코리아넷.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"엑셀 파일 '{filename}'로 저장되었습니다.")

# 메인 함수
def main():
    all_data = []

    # URL 목록과 페이지 범위
    urls = [
        # {"url": "https://www.korean.net/portal/global/pg_news_local.do", "pages": 2, "category": "해외통신원 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_local.do", "pages": 280, "category": "해외통신원 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_group.do", "pages": 138, "category": "재외동포단체 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_hanin.do", "pages": 10, "category": "한인회 운영사례"}
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
