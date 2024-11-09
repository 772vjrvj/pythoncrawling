from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd

# HTML 파일을 BeautifulSoup 객체로 읽어들이는 함수
def load_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file, "html.parser")

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

# 콘텐츠 공개 연도 계산 함수
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

    for content in contents:
        data = {
            "콘텐츠 주소": extract_content_url(content),
            "콘텐츠 이미지 URL": extract_content_image_url(content),
            "콘텐츠 명": extract_content_name(content)
        }

        try:
            metadata_line = content.select_one("#metadata-line")
            spans = metadata_line.select("span.inline-metadata-item.style-scope.ytd-video-meta-block") if metadata_line else []
            if len(spans) > 1:
                time_text = spans[1].text.strip()
                data["콘텐츠 공개 연도"] = calculate_content_year(time_text, today).strftime('%Y-%m-%d')
        except:
            data["콘텐츠 공개 연도"] = None

        print(f'data : {data}')
        content_data.append(data)
    return content_data

# 엑셀 파일로 저장하는 함수
def save_to_excel(content_data, file_name="YTN_KOREAN.xlsx"):
    df = pd.DataFrame(content_data)
    df.to_excel(file_name, index=False)

# 메인 함수
def main():
    file_path = "YTN_KOREAN.html"  # HTML 파일 경로 설정
    today = datetime.today()

    # HTML 파일 로드
    soup = load_html_file(file_path)

    # 콘텐츠 리스트 생성
    content_data = create_content_list(soup, today)

    # 엑셀 파일로 저장
    save_to_excel(content_data)

if __name__ == "__main__":
    main()
