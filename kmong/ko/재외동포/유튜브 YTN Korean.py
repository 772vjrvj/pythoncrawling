from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import re


# HTML 파일을 BeautifulSoup 객체로 읽어들이는 함수
def load_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file, "html.parser")

# 콘텐츠 내용
def extract_content_hash_tag(content_url):
    # 요청 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # URL에서 HTML 페이지 가져오기
    response = requests.get(content_url, headers=headers)
    if response.status_code != 200:
        print(f"페이지를 불러오는 데 실패했습니다. 상태 코드: {response.status_code}")
        return None

    # BeautifulSoup으로 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # <script> 태그 중 'ytInitialData' JSON이 포함된 스크립트를 찾기
    script_tag = soup.find("script", string=re.compile("ytInitialData"))
    if not script_tag:
        print("ytInitialData를 포함한 스크립트를 찾을 수 없습니다.")
        return None

    # JSON 데이터 추출 (ytInitialData 이후의 JSON 데이터만 남기기)
    script_content = script_tag.string
    json_data_match = re.search(r'var ytInitialData = ({.*});', script_content)
    if not json_data_match:
        print("ytInitialData JSON을 찾을 수 없습니다.")
        return None

    # JSON 문자열 파싱
    json_data = json.loads(json_data_match.group(1))

    # JSON 데이터 내의 superTitleLink -> runs -> text 값을 추출
    try:
        runs = json_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0]["videoPrimaryInfoRenderer"]["superTitleLink"]["runs"]
        hashtags = [run["text"].replace("#", "") for run in runs if run["text"].strip() != ""]
        # 배열이 1개인 경우에는 그대로 출력하고, 2개 이상인 경우에만 join
        if len(hashtags) == 1:
            result = hashtags[0]
        else:
            result = ', '.join(hashtags[:2])
        return result
    except KeyError:
        print("해당 경로에서 데이터를 찾을 수 없습니다.")
        return None


# 콘텐츠 주소 추출 함수
def extract_content_url(content):
    try:
        thumbnail = content.select_one('a#thumbnail.yt-simple-endpoint.inline-block.style-scope.ytd-thumbnail')
        return "https://www.youtube.com" + thumbnail["href"] if thumbnail else None
    except:
        return None

# 콘텐츠 이미지 URL 추출 함수
def extract_content_image_url(content):
    try:
        img_tag = content.select_one('a#thumbnail img')
        img_url = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-thumb") if img_tag else None
        return img_url
    except:
        return None

# 콘텐츠 명 추출 함수
def extract_content_name(content):
    try:
        title_element = content.select_one('#details.style-scope.ytd-rich-grid-media #video-title.style-scope.ytd-rich-grid-media')
        return title_element.text.strip() if title_element else None
    except:
        return None

# 공개일자 계산 함수
def calculate_content_year(time_text, today):
    if "일 전" in time_text:
        days = int(time_text.split("일")[0].strip())
        return today - timedelta(days=days)
    elif "주 전" in time_text:
        weeks = int(time_text.split("주")[0].strip())
        return today - timedelta(weeks=weeks)
    elif "개월 전" in time_text:
        months = int(time_text.split("개월")[0].strip())
        return today - timedelta(days=months * 30)
    elif "년 전" in time_text:
        years = int(time_text.split("년")[0].strip())
        return today - timedelta(days=years * 365)
    return today

# 콘텐츠 리스트 생성 함수
def create_content_list(soup, today):
    content_data = []
    contents = soup.select("#contents #content")

    for index, content in enumerate(contents):
        data = {
            "콘텐츠 명": extract_content_name(content),
            "콘텐츠 분류": '유튜브 영상',
            "공개일자": '',
            "노출매체": 'YTN Korean 유튜브',
            "퀄리티": '1080p',
            '콘텐츠 대상지역': '세계',
            '콘텐츠 내용': '',
            '콘텐츠 저작권 소유처': 'YTN Korean',
            '라이선스': '제작 저작권 소유',
            '콘텐츠 시청 방법': '유튜브',
            "이미지 url": extract_content_image_url(content),
            "콘텐츠 주소": extract_content_url(content),
        }

        data["콘텐츠 내용"] = extract_content_hash_tag(data["콘텐츠 주소"])

        try:
            metadata_line = content.select_one("#metadata-line")
            spans = metadata_line.select("span.inline-metadata-item.style-scope.ytd-video-meta-block") if metadata_line else []
            if len(spans) > 1:
                time_text = spans[1].text.strip()
                data["공개일자"] = calculate_content_year(time_text, today).strftime('%Y-%m-%d')
        except:
            data["공개일자"] = None

        print(f'index {index}, data : {data}')
        content_data.append(data)
    return content_data

# 엑셀 파일로 저장하는 함수
def save_to_excel(content_data, file_name="스터디코리안 Youtube.xlsx"):
    df = pd.DataFrame(content_data)
    df.to_excel(file_name, index=False)

# 메인 함수
def main():
    file_path = "스터디코리안 Youtube.html"  # HTML 파일 경로 설정
    today = datetime.today()

    # HTML 파일 로드
    soup = load_html_file(file_path)

    # 콘텐츠 리스트 생성
    content_data = create_content_list(soup, today)

    # 엑셀 파일로 저장
    save_to_excel(content_data)

if __name__ == "__main__":
    main()
