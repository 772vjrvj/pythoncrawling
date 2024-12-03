import requests
from bs4 import BeautifulSoup
import re
import math
import urllib.parse
import json


# 전역 변수 설정
total_pages = 0

def fetch_blog_page(blog_id):
    url = f"https://blog.naver.com/PostList.naver?blogId={blog_id}&widgetTypeCall=true&noTrackingCode=true&directAccess=true"
    headers = {
        "authority": "blog.naver.com",
        "method": "GET",
        "path": f"/PostList.naver?blogId={blog_id}&widgetTypeCall=true&noTrackingCode=true&directAccess=true",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": f"https://blog.naver.com/{blog_id}",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "iframe",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    return response.content

# 전체 게시글 수
def extract_numbers_from_elements(content, class_name):
    soup = BeautifulSoup(content, 'html.parser')
    elements = soup.find_all(class_=class_name)
    numbers = []
    for element in elements:
        text = element.get_text()
        numbers.extend(re.findall(r'\d+', text))
    return numbers


def fetch_post_titles(blog_id, current_page):
    url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={blog_id}&viewdate=&currentPage={current_page}&categoryNo=&parentCategoryNo=&countPerPage=10"
    headers = {
        "authority": "blog.naver.com",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            # JSON 데이터를 올바르게 파싱하기 위해 불필요한 백슬래시를 제거
            cleaned_text = re.sub(r'\\(?!["\\/bfnrt])', "", response.text)  # 잘못된 백슬래시 패턴 제거
            data = json.loads(cleaned_text)  # JSON 파싱

            posts = []
            for post in data.get("postList", []):
                title = urllib.parse.unquote(post.get("title", "")).replace("+", " ")
                title = re.sub(r'\s+', ' ', title).strip()
                post_data = {
                    "addDate": post.get("addDate"),
                    "logNo": post.get("logNo"),
                    "title": title,
                    "url": f'https://blog.naver.com/{blog_id}/{post.get("logNo")}'
                }
                posts.append(post_data)
            return posts

        except json.JSONDecodeError as e:
            print("JSONDecodeError 발생:", e)
            print("응답 텍스트:", response.text)
            return []
    else:
        print("Error: 요청이 실패했습니다.")
        return []


def main(blog_id):
    global total_pages
    content = fetch_blog_page(blog_id)

    # 전체 페이지 및 1페이지 글

    # 전체 개수글 수
    numbers = extract_numbers_from_elements(content, "category_title pcol2")

    # 전체 페이지
    if numbers:  # numbers 리스트가 비어있지 않을 경우
        total_pages = math.ceil(int(numbers[0]) / 10)
        print(total_pages)

    if total_pages > 1:
        posts = fetch_post_titles(blog_id, 1)
        print(f"Page {1}:")
        for post in posts:
            print(post)


    # 특정 페이지 검색
    # fetch_post_titles(blog_id, 2)

# 실행
if __name__ == "__main__":
    global blog_id
    blog_id = "772vjrvj"
    main(blog_id)
