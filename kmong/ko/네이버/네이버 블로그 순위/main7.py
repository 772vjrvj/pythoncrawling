import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def fetch_naver_blog_list(query, page):
    url = "https://s.search.naver.com/p/review/48/search.naver"

    # 페이로드를 딕셔너리 형태로 정의
    payload = {
        "ssc": "tab.blog.all",
        "api_type": 8,
        "query": f"{query}",
        "start": f"{page + 1}",
        "sm": "tab_hty.top",
        "prank": f'{page}',
        "ngn_country": "KR"
    }
    query_encoding = quote(query)

    # 헤더 설정
    headers = {
        "authority": "s.search.naver.com",
        "method": "GET",
        "path": "/p/review/48/search.naver",
        "scheme": "https",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": "",
        "origin": "https://search.naver.com",
        "referer": f"https://search.naver.com/search.naver?sm=tab_hty.top&ssc=tab.blog.all&query={query_encoding}&oquery={query_encoding}&tqi=iyLxLlqo1awssNDx7HsssssstkG-146063",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers, params=payload)
    if response.status_code == 200:
        # JSON 응답 파싱
        json_data = response.json()
        contents = json_data.get("contents", "")

        # HTML 파싱
        soup = BeautifulSoup(contents, 'html.parser')

        # class="detail_box" 안에 있는 title_area의 a 태그 찾기
        detail_boxes = soup.find_all(class_="detail_box")
        results = []  # 제목과 LogNo를 담을 리스트

        for box in detail_boxes:
            title_area = box.find(class_="title_area")
            if title_area:
                a_tag = title_area.find('a')
                if a_tag:
                    # 제목 텍스트 추출
                    title_text = a_tag.get_text(separator=' ', strip=True)  # 띄어쓰기를 유지
                    # href 속성에서 LogNo 추출
                    href = a_tag['href']
                    log_no = href.split('/')[-1]  # URL의 마지막 부분이 LogNo
                    results.append({"title": title_text, "log_no": log_no})

        return results  # 제목과 LogNo의 딕셔너리 리스트를 반환
    else:
        print(f"Error: {response.status_code}")

def find_log_no_index(query, main_log_no):
    page = 0  # 초기 페이지 설정 (0부터 시작)
    while True:
        titles = fetch_naver_blog_list(query, page)
        print(titles)  # 디버깅을 위한 출력

        if titles:
            for index, title in enumerate(titles):
                if title['log_no'] == main_log_no:
                    return (30 * page) + (index + 1)  # (30 * page) + index + 1 반환
            page += 1  # 일치하지 않으면 페이지를 1 증가 (30씩 증가시키기 위해)
        else:
            break  # 결과가 없으면 종료
        time.sleep(1)

if __name__ == "__main__":
    query = '투다리'
    main_log_no = '223614340673'
    result_index = find_log_no_index(query, main_log_no)
    print(result_index)