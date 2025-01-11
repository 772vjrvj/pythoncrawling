import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

def fetch_naver_cafe_articles(clubid, searchdate, searchBy, query, sortBy, userDisplay, media, option):
    # 기본 URL
    base_url = "https://cafe.naver.com/ArticleSearchList.nhn"

    # URL 파라미터 설정 (쿼리 파라미터에 한글을 그대로 사용)
    params = {
        'search.clubid': clubid,
        'search.searchdate': searchdate,
        'search.searchBy': searchBy,
        'search.query': query,  # 한글 검색어를 그대로 사용
        'search.defaultValue': 1,
        'search.includeAll': '',
        'search.exclude': '',
        'search.include': '',
        'search.exact': '',
        'search.sortBy': sortBy,
        'userDisplay': userDisplay,
        'search.media': media,
        'search.option': option
    }

    # 전체 URL 생성
    full_url = f"{base_url}?{urlencode(params, encoding='euc-kr')}"  # 'euc-kr' 인코딩 사용
    print(f"Requesting URL: {full_url}")

    # 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    # HTTP 요청 보내기
    response = requests.get(full_url, headers=headers)

    # 응답 인코딩을 'euc-kr'로 설정
    response.encoding = 'euc-kr'

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(response.text, 'html.parser')

    # 클래스 이름이 'article-board m-tcol-c'인 두 번째 요소 찾기
    article_boards = soup.find_all('div', class_='article-board m-tcol-c')

    # 두 번째 'article-board m-tcol-c' 요소에서 tr 태그를 찾기
    if len(article_boards) >= 2:
        second_board = article_boards[1]
        rows = second_board.find_all('tr')

        # 각 tr 태그 내용을 출력
        for row in rows:
            print(row.get_text(strip=True))
    else:
        print("두 번째 'article-board m-tcol-c' 요소를 찾을 수 없습니다.")

def main():
    # 함수에 전달할 파라미터 설정
    clubid = '15092639'
    searchdate = '1y'
    searchBy = 1
    query = '당근'  # 한글 '당근'을 그대로 사용
    sortBy = 'date'
    userDisplay = 15
    media = 0
    option = 0

    # 함수 호출
    fetch_naver_cafe_articles(clubid, searchdate, searchBy, query, sortBy, userDisplay, media, option)

if __name__ == "__main__":
    main()
