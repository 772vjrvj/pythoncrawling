import requests
from bs4 import BeautifulSoup, Tag
import math
import time
import random

# 공통 헤더 정의
LIST_HEADERS = {
    "authority": "terms.naver.com",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

SEARCH_HEADERS = LIST_HEADERS.copy()

def fetch_list_total_count(url):
    response = requests.get(url, headers=LIST_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    count_text = soup.select_one(".path_area .count").get_text(strip=True)
    total_count = int(''.join(filter(str.isdigit, count_text)))
    return total_count

def fetch_search_total_count(url):
    response = requests.get(url, headers=SEARCH_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    count_text = soup.select_one(".subject_item.selected .count").get_text(strip=True)
    total_count = int(''.join(filter(str.isdigit, count_text)))
    return total_count

def calculate_total_pages(total_count, per_page):
    return math.ceil(total_count / per_page)

def fetch_list_titles_by_page(url, page_num):
    paginated_url = f"{url}&page={page_num}"
    response = requests.get(paginated_url, headers=LIST_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = []
    li_items = soup.select("ul.content_list > li")
    for li in li_items:
        title_tag = li.select_one(".subject .title > a")
        if title_tag:
            # a 태그 전체 텍스트를 가져옴 (strong 태그 없음)
            titles.append(title_tag.get_text(strip=True))
    return titles

def fetch_search_titles_by_page(url, page_num, skip_first=False):
    paginated_url = f"{url}&page={page_num}"
    response = requests.get(paginated_url, headers=SEARCH_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = []
    search_results = soup.select(".search_result_area")
    if page_num == 1 and skip_first:
        search_results = search_results[1:]

    for result in search_results:
        title_tag = result.select_one(".info_area .subject .title > a")
        if title_tag:
            # a 태그 전체 텍스트를 가져옴 (strong 태그 없음)
            titles.append(title_tag.get_text(strip=True))

    return titles




def process_list_url(url):
    total_count = fetch_list_total_count(url)
    print(f'총 추출건수 : {total_count}')
    total_pages = calculate_total_pages(total_count, 15)
    print(f'총 페이지 : {total_pages}')

    all_titles = []
    for page_num in range(1, total_pages + 1):
        page_titles = fetch_list_titles_by_page(url, page_num)
        print(f'{page_num} 페이지: 제목 수 {len(page_titles)}')
        print(f'{page_num} 페이지, 제목 {page_titles}')
        all_titles.extend(page_titles)
        time.sleep(random.uniform(3, 5))

    return all_titles

def process_search_url(url):
    total_count = fetch_search_total_count(url)
    print(f'총 추출건수 : {total_count}')
    total_pages = calculate_total_pages(total_count, 10)
    print(f'총 페이지 : {total_pages}')

    all_titles = []
    for page_num in range(1, total_pages + 1):
        page_titles = fetch_search_titles_by_page(url, page_num, skip_first=(page_num == 1))
        print(f'{page_num} 페이지, 제목 수 {len(page_titles)}')
        print(f'{page_num} 페이지, 제목 : {page_titles}')
        all_titles.extend(page_titles)
        time.sleep(random.uniform(3, 5))

    return all_titles

def main(url):
    if "list.naver" in url:
        all_titles = process_list_url(url)
    elif "search.naver" in url:
        all_titles = process_search_url(url)
    else:
        print("지원하지 않는 URL 형식입니다.")
        return

    print("총 제목 리스트:", all_titles)
    print("총 제목 수:", len(all_titles))

if __name__ == "__main__":
    url = "https://terms.naver.com/search.naver?query=%ED%9B%84%EC%A7%80%EC%82%B0&searchType=text&dicType=&subject="  # URL을 필요에 따라 변경
    main(url)
