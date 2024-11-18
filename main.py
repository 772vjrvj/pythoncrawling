import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import json


def read_excel(file_path):
    """엑셀 파일을 읽어 콘텐츠 주소 컬럼을 반환"""
    df = pd.read_excel(file_path)
    return df


def get_video_date_from_url(url):

    headers = {
        "authority": "www.youtube.com",
        "method": "GET",
        "scheme": "https",
        "cookie": "VISITOR_INFO1_LIVE=OBTTetow8B8; VISITOR_PRIVACY_METADATA=CgJLUhIEGgAgPg%3D%3D; SID=g.a000qQg26ICQNafFFGoYAX1kdB4m6HivJT-j4nyzLtJameG_gy6zDvVlU6ZKW33245KpcHdYrAACgYKAf8SARISFQHGX2MimPOJf7A3N8LE1Azft_PHThoVAUF8yKpZmSPlaGtqNXcZa13JtQM_0076; __Secure-1PSID=g.a000qQg26ICQNafFFGoYAX1kdB4m6HivJT-j4nyzLtJameG_gy6z0f1nO9_KTf4dNTAD8fuJYgACgYKAeASARISFQHGX2MibJEiDo_XSw66UgB2eTCm3RoVAUF8yKqH2yU-k9ibZ4Z1jWH46rU90076; __Secure-3PSID=g.a000qQg26ICQNafFFGoYAX1kdB4m6HivJT-j4nyzLtJameG_gy6zbNyBPVCXSHUt6EwHt_tURgACgYKAdoSARISFQHGX2Mi6BCAM_88x-v-4yhsdk-1VBoVAUF8yKqh_5bMVorliLZWIjQQFhq60076; HSID=AaUOOp-d5t6OUZdis; SSID=A_j0cXO4Psbw9R3qQ; APISID=fCG7rjuT4y7C391H/AjFxrBz3W1Hl3P010; SAPISID=ESsynRKARsqwUNEC/AYoTitd_hzgodd6o4; __Secure-1PAPISID=ESsynRKARsqwUNEC/AYoTitd_hzgodd6o4; __Secure-3PAPISID=ESsynRKARsqwUNEC/AYoTitd_hzgodd6o4; LOGIN_INFO=AFmmF2swRQIgbEwMY0io4W01eotxXJJuvY_sZSieKc8Cmg3Sbr45ZlACIQCoF3gRGBzFfCzNiveCJHv92RhtKTuiA3y7OaGNxVAc-w:QUQ3MjNmeWk1Z19YU016VlMtZW96eFhhTUF0Qld6UlhMYW9ESGFNT2VkZ0RiaG1jaFRuSENqTmVINHVuZ2xEdWFfQzZYeXNIRmRJYnc0Y1lsdGJycHRkVjcxcmUwZ3hMeHNkRlhDSHNUTklvV0ZPdHg2WlBwTVZUeGRQSjJUUHNIeGNSVjduY2NFMVNQRWdCUHRGT0F1b1dLZ3cxTHIxcjhR; YSC=r5_YTr7kVi0; PREF=tz=Asia.Seoul&f7=100; __Secure-1PSIDTS=sidts-CjEBQT4rX_5pT7d6TVhJ0n4yfDWHYUiC0ZSne2bkjQLgoqEatTWeMOXt3pjpdMsgsqLnEAA; __Secure-3PSIDTS=sidts-CjEBQT4rX_5pT7d6TVhJ0n4yfDWHYUiC0ZSne2bkjQLgoqEatTWeMOXt3pjpdMsgsqLnEAA; ST-xuwub9=session_logininfo=AFmmF2swRQIgbEwMY0io4W01eotxXJJuvY_sZSieKc8Cmg3Sbr45ZlACIQCoF3gRGBzFfCzNiveCJHv92RhtKTuiA3y7OaGNxVAc-w%3AQUQ3MjNmeWk1Z19YU016VlMtZW96eFhhTUF0Qld6UlhMYW9ESGFNT2VkZ0RiaG1jaFRuSENqTmVINHVuZ2xEdWFfQzZYeXNIRmRJYnc0Y1lsdGJycHRkVjcxcmUwZ3hMeHNkRlhDSHNUTklvV0ZPdHg2WlBwTVZUeGRQSjJUUHNIeGNSVjduY2NFMVNQRWdCUHRGT0F1b1dLZ3cxTHIxcjhR; SIDCC=AKEyXzXjAjWQOnRvpWniepz5zEL8h-cK1914G-VXTYLddC9c5ZRp6poPfxFkVQC5juc4U4xeCw; __Secure-1PSIDCC=AKEyXzVoDQXB7I3aCyn29y_jJxeLWVW5qb39Gb30p7IhALAmSgAbdS2kr2LzAYn5qG2MHJDd; __Secure-3PSIDCC=AKEyXzV3pqsr46QcIIfP6nse6RXP2bYqRgsI7czqpcV8Hs3GywrMeFQ9e5h3UbGUgdIQiYhISQ",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.119 Safari/537.36"
    }

    """URL에서 GET 요청을 보내고 날짜를 추출하여 반환"""
    try:
        # GET 요청 보내기
        response = requests.get(url, headers)
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

                    # 날짜 추출
                    contents = yt_initial_data.get("contents", {}).get("twoColumnWatchNextResults", {}).get("results", {}).get("results", {}).get("contents", [])
                    for content in contents:
                        date_text = content.get("videoPrimaryInfoRenderer", {}).get("dateText", {}).get("simpleText", "")
                        if date_text:
                            return date_text
        else:
            print(f"Failed to retrieve {url}: {response.status_code}")
    except Exception as e:
        print(f"Error while processing {url}: {e}")
    return None


def extract_dates_from_urls(df):

    """엑셀에서 URL을 순회하면서 각 URL에 대해 날짜를 추출"""
    date_list = []
    for index, url in enumerate(df['콘텐츠 주소']):
        date = get_video_date_from_url(url)

        # date가 없다면 공백을 출력하고 공백값을 추가
        if date:
            print(f"Index: {index}, Date: {date}")
            date_list.append(date)
        else:
            print(f"Index: {index}, Date: (공백)")
            date_list.append('')  # 공백값을 append

        # 500개마다 엑셀 파일 업데이트
        if (index + 1) % 500 == 0:
            save_dates_to_excel(date_list, '유튜브_결과_날짜.xlsx')
            date_list = []  # 날짜 리스트 초기화

    # 남은 데이터 엑셀에 저장
    if date_list:
        save_dates_to_excel(date_list, '유튜브_결과_날짜.xlsx')


def save_dates_to_excel(date_list, output_file):
    """추출된 날짜 리스트를 엑셀 파일로 저장"""
    output_df = pd.DataFrame(date_list, columns=['Video Date'])
    output_df.to_excel(output_file, index=False, mode='a', header=not pd.io.common.file_exists(output_file))
    print(f"엑셀 파일로 결과가 저장되었습니다: {output_file}")


def main():
    """메인 함수에서 엑셀 파일을 읽고, URL에서 날짜를 추출하여 엑셀로 저장"""
    file_path = '유튜브 날짜.xlsx'  # 엑셀 파일 경로를 입력하세요.

    # 엑셀 파일에서 데이터 읽기
    df = read_excel(file_path)

    # URL에서 날짜 추출
    extract_dates_from_urls(df)


if __name__ == '__main__':
    main()
