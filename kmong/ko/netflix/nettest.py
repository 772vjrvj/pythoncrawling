import requests
from bs4 import BeautifulSoup
import re

def fetch_netflix_page(url):
    """
    Netflix 페이지의 HTML을 가져오는 함수.
    요청 헤더는 함수 내에서 정의됨.

    Args:
        url (str): 요청할 Netflix URL.

    Returns:
        BeautifulSoup: HTML 파싱된 결과를 반환.
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        print("페이지 요청 성공!")
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"페이지 요청 중 오류 발생: {e}")
        return None

def extract_netflix_data(soup):
    """
    Netflix 페이지에서 필요한 정보를 추출하여 객체로 반환.

    Args:
        soup (BeautifulSoup): HTML 파싱된 BeautifulSoup 객체.

    Returns:
        dict: 추출된 정보를 담은 객체.
    """
    result = {
        "title": "",
        "year": "",
        "season": "",
        "rating": "",
        "genre": "",
        "summary": "",
        "cast": "",
        "director": "",
        "success": "O",
    }

    try:
        # 메인 컨테이너
        main_container = soup.find("div", class_="default-ltr-cache-kiz1b3 em9qa8x3")

        # Title (h2 태그)
        title_tag = main_container.find("h2", class_="default-ltr-cache-11jsu7c euy28770")
        result["title"] = title_tag.text.strip() if title_tag else ""

        # Year, Season, Rating, Genre
        details_container = main_container.find("div", class_="default-ltr-cache-56ff39 em9qa8x2")
        details_list = details_container.find("ul", class_="default-ltr-cache-1xty6x8 e32lqeb1") if details_container else None

        if details_list:

            li_tags = details_list.find_all("li", class_="default-ltr-cache-1payn3k e32lqeb0")

            if len(li_tags) == 4:

                result["year"] = li_tags[0].text.strip() if len(li_tags) > 0 else ""

                season_text = li_tags[1].text.strip() if len(li_tags) > 1 else ""
                season_text = season_text.replace('\u2068', '').replace('\u2069', '')
                result["season"] = season_text

                rating_text = li_tags[2].text.strip() if len(li_tags) > 2 else ""
                rating_text = rating_text.replace('\u2068', '').replace('\u2069', '')
                result["rating"] = rating_text

                genre_text = li_tags[3].text.strip() if len(li_tags) > 3 else ""
                genre_text = genre_text.replace('\u2068', '').replace('\u2069', '')
                result["genre"] = genre_text

            if len(li_tags) == 3:

                result["year"] = li_tags[0].text.strip() if len(li_tags) > 0 else ""

                rating_text = li_tags[1].text.strip() if len(li_tags) > 1 else ""
                rating_text = rating_text.replace('\u2068', '').replace('\u2069', '')
                result["rating"] = rating_text

                genre_text = li_tags[2].text.strip() if len(li_tags) > 2 else ""
                genre_text = genre_text.replace('\u2068', '').replace('\u2069', '')
                result["genre"] = genre_text

        else:
            result.update({"year": "", "season": "", "rating": "", "genre": ""})


        # Summary (줄거리)
        summary_container = main_container.find("div", class_="default-ltr-cache-18fxwnx em9qa8x0")
        summary_tag = summary_container.find("div", class_="default-ltr-cache-1y7pnva em9qa8x1") if summary_container else None
        summary_span = summary_tag.find("span", class_="default-ltr-cache-v92n84 euy28770") if summary_tag else None
        result["summary"] = summary_span.text.strip() if summary_span else ""

        # Cast and Director
        cast_director_container = summary_container.find("div", class_="default-ltr-cache-1wmy9hl ehsrwgm0") if summary_container else None
        cast_divs = cast_director_container.find_all("div", class_="default-ltr-cache-eywhmi ehsrwgm1") if cast_director_container else []

        # Cast (출연진)
        if len(cast_divs) > 0:
            cast_span = cast_divs[0].find_all("span", class_="default-ltr-cache-3z6sz6 euy28770")
            result["cast"] = cast_span[0].text.strip()
        else:
            result["cast"] = ""

        # Director (감독)
        if len(cast_divs) > 1:
            director_span = cast_divs[1].find_all("span", class_="default-ltr-cache-3z6sz6 euy28770")
            result["director"] = director_span[0].text.strip()
        else:
            result["director"] = ""
    except AttributeError as e:
        print(f"데이터 추출 중 오류 발생: {e}")
        result['success'] = 'X'

    return result

def main():
    url = "https://www.netflix.com/watch/80022580"
    # url = "https://www.netflix.com/kr/title/80002311"
    soup = fetch_netflix_page(url)

    if soup:
        netflix_data = extract_netflix_data(soup)
        if netflix_data:
            print(f"{netflix_data}")
        else:
            print("데이터를 추출하지 못했습니다.")
    else:
        print("페이지 요청 실패.")

if __name__ == "__main__":
    main()
