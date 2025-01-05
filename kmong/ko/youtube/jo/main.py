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

# 콘텐츠 주소 추출 함수
def extract_content_url(content):
    try:
        thumbnail = content.select_one('a#thumbnail.yt-simple-endpoint.inline-block.style-scope.ytd-thumbnail')
        return "https://www.youtube.com" + thumbnail["href"] if thumbnail else None
    except:
        return None


# 콘텐츠 명 추출 함수
def extract_content_name(content):
    try:
        title_element = content.select_one('#details.style-scope.ytd-rich-grid-media #video-title.style-scope.ytd-rich-grid-media')
        return title_element.text.strip() if title_element else None
    except:
        return None


# 콘텐츠 리스트 생성 함수
def create_content_list(soup, today):
    content_data = []
    contents = soup.select("#contents #content")

    for index, content in enumerate(contents):
        data = {
            "콘텐츠 명": extract_content_name(content),
            "콘텐츠 주소": extract_content_url(content)
        }
        content_data.append(data)
    return content_data

# 엑셀 파일로 저장하는 함수
def save_to_excel(content_data, file_name="조승현2.xlsx"):
    df = pd.DataFrame(content_data)
    df.to_excel(file_name, index=False)

# 메인 함수
def main():
    file_path = "조승현2.html"  # HTML 파일 경로 설정
    today = datetime.today()

    # HTML 파일 로드
    soup = load_html_file(file_path)

    # 콘텐츠 리스트 생성
    content_data = create_content_list(soup, today)

    # # 헤더 설정
    # headers = {
    #     "authority": "www.youtube.com",
    #     "method": "GET",
    #     "scheme": "https",
    #     "cookie": "VISITOR_INFO1_LIVE=OBTTetow8B8; VISITOR_PRIVACY_METADATA=CgJLUhIEGgAgPg%3D%3D; SID=g.a000qQg26ICQNafFFGoYAX1kdB4m6HivJT-j4nyzLtJameG_gy6zDvVlU6ZKW33245KpcHdYrAACgYKAf8SARISFQHGX2MimPOJf7A3N8LE1Azft_PHThoVAUF8yKpZmSPlaGtqNXcZa13JtQM_0076; __Secure-1PSID=g.a000qQg26ICQNafFFGoYAX1kdB4m6HivJT-j4nyzLtJameG_gy6z0f1nO9_KTf4dNTAD8fuJYgACgYKAeASARISFQHGX2MibJEiDo_XSw66UgB2eTCm3RoVAUF8yKqH2yU-k9ibZ4Z1jWH46rU90076; __Secure-3PSID=g.a000qQg26ICQNafFFGoYAX1kdB4m6HivJT-j4nyzLtJameG_gy6zbNyBPVCXSHUt6EwHt_tURgACgYKAdoSARISFQHGX2Mi6BCAM_88x-v-4yhsdk-1VBoVAUF8yKqh_5bMVorliLZWIjQQFhq60076; HSID=AaUOOp-d5t6OUZdis; SSID=A_j0cXO4Psbw9R3qQ; APISID=fCG7rjuT4y7C391H/AjFxrBz3W1Hl3P010; SAPISID=ESsynRKARsqwUNEC/AYoTitd_hzgodd6o4; __Secure-1PAPISID=ESsynRKARsqwUNEC/AYoTitd_hzgodd6o4; __Secure-3PAPISID=ESsynRKARsqwUNEC/AYoTitd_hzgodd6o4; LOGIN_INFO=AFmmF2swRQIgbEwMY0io4W01eotxXJJuvY_sZSieKc8Cmg3Sbr45ZlACIQCoF3gRGBzFfCzNiveCJHv92RhtKTuiA3y7OaGNxVAc-w:QUQ3MjNmeWk1Z19YU016VlMtZW96eFhhTUF0Qld6UlhMYW9ESGFNT2VkZ0RiaG1jaFRuSENqTmVINHVuZ2xEdWFfQzZYeXNIRmRJYnc0Y1lsdGJycHRkVjcxcmUwZ3hMeHNkRlhDSHNUTklvV0ZPdHg2WlBwTVZUeGRQSjJUUHNIeGNSVjduY2NFMVNQRWdCUHRGT0F1b1dLZ3cxTHIxcjhR; YSC=r5_YTr7kVi0; PREF=tz=Asia.Seoul&f7=100; __Secure-1PSIDTS=sidts-CjEBQT4rX_5pT7d6TVhJ0n4yfDWHYUiC0ZSne2bkjQLgoqEatTWeMOXt3pjpdMsgsqLnEAA; __Secure-3PSIDTS=sidts-CjEBQT4rX_5pT7d6TVhJ0n4yfDWHYUiC0ZSne2bkjQLgoqEatTWeMOXt3pjpdMsgsqLnEAA; ST-xuwub9=session_logininfo=AFmmF2swRQIgbEwMY0io4W01eotxXJJuvY_sZSieKc8Cmg3Sbr45ZlACIQCoF3gRGBzFfCzNiveCJHv92RhtKTuiA3y7OaGNxVAc-w%3AQUQ3MjNmeWk1Z19YU016VlMtZW96eFhhTUF0Qld6UlhMYW9ESGFNT2VkZ0RiaG1jaFRuSENqTmVINHVuZ2xEdWFfQzZYeXNIRmRJYnc0Y1lsdGJycHRkVjcxcmUwZ3hMeHNkRlhDSHNUTklvV0ZPdHg2WlBwTVZUeGRQSjJUUHNIeGNSVjduY2NFMVNQRWdCUHRGT0F1b1dLZ3cxTHIxcjhR; SIDCC=AKEyXzXjAjWQOnRvpWniepz5zEL8h-cK1914G-VXTYLddC9c5ZRp6poPfxFkVQC5juc4U4xeCw; __Secure-1PSIDCC=AKEyXzVoDQXB7I3aCyn29y_jJxeLWVW5qb39Gb30p7IhALAmSgAbdS2kr2LzAYn5qG2MHJDd; __Secure-3PSIDCC=AKEyXzV3pqsr46QcIIfP6nse6RXP2bYqRgsI7czqpcV8Hs3GywrMeFQ9e5h3UbGUgdIQiYhISQ",
    #     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "accept-encoding": "gzip, deflate, br, zstd",
    #     "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    #     "cache-control": "max-age=0",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.119 Safari/537.36"
    # }
    #
    # date_list = extract_dates_from_urls(content_data, headers)


    # 엑셀 파일로 저장
    save_to_excel(content_data)


def get_video_date_and_views_from_url(url, headers):
    """URL에서 GET 요청을 보내고 날짜와 조회수를 추출하여 반환"""
    try:
        # GET 요청 보내기
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # ytInitialData 스크립트 찾기
            script_tag = soup.find('script', text=re.compile('ytInitialData'))
            if script_tag:
                # ytInitialData 추출
                yt_initial_data_str = re.search(r'ytInitialData\s*=\s*({.*?});', script_tag.string, re.DOTALL)
                if yt_initial_data_str:
                    yt_initial_data = json.loads(yt_initial_data_str.group(1))

                    # 날짜와 조회수 추출
                    contents = yt_initial_data.get("contents", {}).get("twoColumnWatchNextResults", {}).get("results", {}).get("results", {}).get("contents", [])
                    for content in contents:
                        # 날짜 추출
                        date_text = content.get("videoPrimaryInfoRenderer", {}).get("dateText", {}).get("simpleText", "")

                        # 조회수 추출
                        views_text = content.get("videoPrimaryInfoRenderer", {}).get("viewCount", {}).get("videoViewCountRenderer", {}).get("viewCount", {}).get("simpleText", "")

                        # 둘 중 하나라도 있으면 반환
                        if date_text or views_text:
                            return date_text, views_text
        else:
            print(f"Failed to retrieve {url}: {response.status_code}")
    except Exception as e:
        print(f"Error while processing {url}: {e}")
    return None, None


def extract_dates_from_urls(content_data, headers):
    """엑셀에서 URL을 순회하면서 각 URL에 대해 날짜를 추출"""
    date_list = []
    for index, data in enumerate(content_data):
        url = data['콘텐츠 주소']

        date, view = get_video_date_and_views_from_url(url, headers)

        # date가 없다면 공백을 출력하고 공백값을 추가
        if date:
            print(f"Index: {index}, Date: {date}")
            content_data[index]['날짜'] = date
            date_list.append(date)
        else:
            print(f"Index: {index}, Date: (공백)")
            content_data[index]['날짜'] = ''

        if view:
            print(f"Index: {index}, view: {view}")
            content_data[index]['조회수'] = date
            date_list.append(date)
        else:
            print(f"Index: {index}, 조회수: (공백)")
            content_data[index]['조회수'] = ''

        print(f'content_data : {content_data}')

    return date_list


if __name__ == "__main__":
    main()
