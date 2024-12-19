import logging
import random
import time
from datetime import datetime
import pandas as pd
import requests


# pubDateStr을 "yyyyMMdd" 형식으로 변환하는 함수
def convert_pubdate(pubDateStr):
    try:
        return datetime.strptime(pubDateStr, "%Y-%m-%d %H:%M").strftime("%Y%m%d")
    except Exception as e:
        print(f"Error converting date: {e}")
        return None

# content에서 필요한 데이터를 추출하는 함수
def extract_article_info(content, keyword):
    articles = []

    for item in content:
        article = {
            'NEWS': 'China Daily',
            "TITLE": item.get("title", ""),
            "CONTENT": item.get("plainText", ""),
            "DATE": convert_pubdate(item.get("pubDateStr", "")),
            "URL": item.get("url", ""),
            "키워드": keyword,
        }
        print(article)
        articles.append(article)

    return articles



def get_chinadaily(keyword, page):
    url = f"https://newssearch.chinadaily.com.cn/rest/en/search?keywords={keyword}&sort=dp&page={page}&curType=story&type=&channel=&source="  # 실제 API URL로 교체하세요
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "cookie": "wdcid=08a0fc7e523f6404",
        "host": "newssearch.chinadaily.com.cn",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }


    # API 요청
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()  # JSON 응답 파싱

        # "content" 배열에서 데이터 추출
        articles = extract_article_info(data.get("content", []), keyword)

        # 결과 출력 (리스트 형태)
        return articles
    else:
        print("Failed to fetch data:", response.status_code)

def save_to_excel(results):

    # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    # 파일 이름 설정
    file_name = f"신문_{current_time}.xlsx"

    try:
        # 파일이 없으면 새로 생성
        df = pd.DataFrame(results)

        # 엑셀 파일 저장
        df.to_excel(file_name, index=False)

    except Exception as e:
        # 예기치 않은 오류 처리
        logging.error(f"엑셀 저장 실패: {e}")



# main 함수에서 API 요청 및 JSON 파싱
def main():


    all_data_list = []

    # keyword = 'South Korea’s President' # 없음
    # keyword = 'Yoon Suk Yeol'
    # keyword = 'Martial Law'
    keyword = 'Impeachment'
    for page in range(1, 8):
        data = get_chinadaily(keyword, page)
        all_data_list.extend(data)
        time.sleep(random.uniform(1, 2))

    save_to_excel(all_data_list)


if __name__ == "__main__":
    main()
