from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 셀레니움 드라이버 세팅 함수
def setup_driver():
    chrome_options = Options()
    # 헤드리스 모드로 실행 (원한다면 주석 해제)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--window-size=1080,750")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # 사용자 에이전트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 드라이버 생성
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

# 댓글 정보를 셀레니움으로 크롤링하는 함수
def scrape_comments(driver, comment_url):
    print(f"댓글 크롤링 시작 url : {comment_url}")
    driver.get(comment_url)
    comments_data = []

    try:
        # 댓글 목록이 로드될 때까지 대기
        time.sleep(2)
        ul_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "u_cbox_list"))
        )
        li_elements = ul_element.find_elements(By.TAG_NAME, "li")

        # 각 댓글 항목에서 작성자, 내용, 작성일 추출
        for li in li_elements:
            # 요소가 없으면 공백값으로 처리
            author = li.find_element(By.CLASS_NAME, "u_cbox_nick").text if li.find_elements(By.CLASS_NAME, "u_cbox_nick") else ""
            content = li.find_element(By.CLASS_NAME, "u_cbox_contents").text if li.find_elements(By.CLASS_NAME, "u_cbox_contents") else ""
            date = li.find_element(By.CLASS_NAME, "u_cbox_date").text if li.find_elements(By.CLASS_NAME, "u_cbox_date") else ""

            # 값이 하나라도 없으면 continue
            if not author or not content or not date:
                continue

            comment_obj = {
                "author": author,   # 작성자
                "content": content, # 내용
                "reg_date": date    # 작성일
            }
            print(f"comment_obj : {comment_obj}")
            comments_data.append(comment_obj)

    except Exception as e:
        print(f"댓글 영역을 찾지 못했습니다: {e}")

    return comments_data

# 상세 기사를 셀레니움으로 크롤링하는 함수
def scrape_article_content(driver, url):
    print(f"상세 시작 url :  {url}")
    driver.get(url)


    time.sleep(2)
    # 기사 본문이 로드될 때까지 대기
    content_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#newsct_article"))
    )
    content = content_element.text if content_element else None

    time.sleep(2)
    # 공감 수가 로드될 때까지 대기
    try:
        like_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".u_likeit_text._count.num"))
        )
        like_count = like_element.text if like_element else "0"
    except Exception:
        like_count = "0"

    # 댓글 수가 로드될 때까지 대기
    try:
        comment_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_cmtcount_button._COMMENT_COUNT_VIEW#comment_count"))
        )
        comment_count = comment_element.text.strip().replace("댓글", "").strip() if comment_element else "0"

        # 공백인 경우 "0"으로 처리
        if not comment_count:
            comment_count = "0"

    except Exception:
        comment_count = "0"

    # 기자 이름 추출, 없을 경우 빈 문자열로 처리
    try:
        journalist_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_journalist_name"))
        )
        journalist_name = journalist_element.text if journalist_element else None
    except Exception:
        journalist_name = ""

    return content, journalist_name, like_count, comment_count


# 최신 뉴스 데이터를 수집하는 함수
def get_news_data_today(date_str):
    header = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    news_data = []
    driver = setup_driver()

    print(f"date_str : {date_str} 시작")
    url = f"https://news.naver.com/breakingnews/section/103/238?date={date_str}"

    response = requests.get(url, headers=header)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # 각 기사 아이템을 가져옴
    articles = soup.select('.sa_item._LAZY_LOADING_WRAP')
    for article in articles:
        # 기사 URL 추출
        main_url = article.select_one('.sa_text_title._NLOG_IMPRESSION')['href']
        if not main_url.startswith('http'):
            main_url = 'https://news.naver.com' + main_url

        # 기사 제목 추출
        title = article.select_one('.sa_text_title._NLOG_IMPRESSION .sa_text_strong').get_text(strip=True)

        # 댓글 URL 추출
        comment_url_element = article.select_one('.sa_text_cmt._COMMENT_COUNT_LIST')
        comment_url = comment_url_element['href'] if comment_url_element else None
        if comment_url and not comment_url.startswith('http'):
            comment_url = 'https://news.naver.com' + comment_url

        # 이미지 URL 추출
        image_thumb_element = article.select_one('.sa_thumb_inner .sa_thumb_link._NLOG_IMPRESSION img')
        image_thumb = image_thumb_element.get('data-src') if image_thumb_element else None

        # 상세 기사 및 댓글 데이터 크롤링
        content, journalist_name, like_count, comment_count = scrape_article_content(driver, main_url)
        comments = scrape_comments(driver, comment_url) if comment_url else []

        # 결과 객체 생성
        obj = {
            'date': date_str,
            'title': title,
            'journalist_name': journalist_name,
            'like_count': like_count,
            'content': content,
            'comment_count': comment_count,
            'main_url': main_url,
            'comment_url': comment_url,
            'image_thumb': image_thumb,
            'comments': comments
        }

        print(f"obj : {obj}")
        news_data.append(obj)

    print(f"news_data : {news_data}")
    driver.quit()
    return news_data


# 기사 데이터 수집 함수
def fetch_news_data(page, date_str):
    header = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    }

    url = f"https://news.naver.com/section/template/SECTION_ARTICLE_LIST_FOR_LATEST?sid=103&sid2=238&pageNo={page}&date={date_str}"

    response = requests.get(url, headers=header)
    if response.status_code == 200:
        try:
            json_data = response.json()  # JSON 응답 파싱
            articles_html = json_data.get("renderedComponent", {}).get("SECTION_ARTICLE_LIST_FOR_LATEST", "")

            # 추출된 HTML을 BeautifulSoup으로 파싱
            soup = BeautifulSoup(articles_html, 'html.parser')
            return soup

        except Exception as e:
            print(f"JSON 파싱 중 오류 발생: {e}")
            return None  # 오류 발생 시 None 반환

    return None


def parse_news_data(soup, date_str):
    news_data = []
    driver = setup_driver()

    # 각 기사 아이템을 가져옴
    articles = soup.select('.sa_item._LAZY_LOADING_WRAP')
    print(f" articles len : {len(articles)}")

    for article in articles:
        # 기사 URL 추출
        main_url = article.select_one('.sa_text_title._NLOG_IMPRESSION')['href']
        if not main_url.startswith('http'):
            main_url = 'https://news.naver.com' + main_url

        print(f"main_url : {main_url}")

        # 기사 제목 추출
        title = article.select_one('.sa_text_title._NLOG_IMPRESSION .sa_text_strong').get_text(strip=True)
        print(f"title : {title}")

        # 댓글 URL 추출
        comment_url_element = article.select_one('.sa_text_cmt._COMMENT_COUNT_LIST')
        comment_url = comment_url_element['href'] if comment_url_element else None
        if comment_url and not comment_url.startswith('http'):
            comment_url = 'https://news.naver.com' + comment_url

        print(f"comment_url : {comment_url}")

        # 이미지 URL 추출
        image_thumb_element = article.select_one('.sa_thumb_inner .sa_thumb_link._NLOG_IMPRESSION img')
        image_thumb = image_thumb_element.get('data-src') if image_thumb_element else None
        print(f"image_thumb : {image_thumb}")

        # 상세 기사 및 댓글 데이터 크롤링
        content, journalist_name, like_count, comment_count = scrape_article_content(driver, main_url)
        print(f"journalist_name : {journalist_name}")
        print(f"like_count : {like_count}")
        print(f"comment_count : {comment_count}")

        comments = scrape_comments(driver, comment_url) if comment_url else []

        # 결과 객체 생성
        obj = {
            'date': date_str,
            'title': title,
            'journalist_name': journalist_name,
            'like_count': like_count,
            'content': content,
            'comment_count': comment_count,
            'main_url': main_url,
            'comment_url': comment_url,
            'image_thumb': image_thumb,
            'comments': comments
        }

        print(f"obj : {obj}")
        news_data.append(obj)

    driver.quit()
    return news_data


# 월의 1일부터 오늘까지 모든 뉴스 데이터 수집
def collect_news_data():
    all_news_data = []
    url_set = set()  # 중복 확인을 위한 URL 집합
    current_date = datetime.now()
    start_date = current_date.replace(day=1)

    # 1일부터 오늘까지 날짜 리스트 생성
    date_list = [(start_date + timedelta(days=i)).strftime('%Y%m%d') for i in range((current_date - start_date).days + 1)]
    print(f"date_list all: {date_list}")

    for date_str in date_list:
        print(f"Processing date: {date_str}")
        page = 1
        last_article_id = None

        while True:
            # 해당 날짜 페이지에 대한 기사 soup을 가져온다.
            soup = fetch_news_data(page, date_str)

            articles = soup.select('.sa_item._LAZY_LOADING_WRAP')
            if not articles:
                break

            print(f" articles len : {len(articles)}")


            # 해당날짜의 page는 마지막값이 존재하지 않고 마지막 이후에는 계속 동일 데이터를 가져오므로 비교를 해야한다.
            article_last = articles[-1]
            main_url = article_last.select_one('.sa_text_title._NLOG_IMPRESSION')['href']
            current_article_id = main_url.split("/")[-1]  # 기사 URL에서 ID 추출

            print(f"last_article_id : {current_article_id}")
            print(f"last_article_id : {last_article_id}")

            if last_article_id == current_article_id:
                break  # 동일한 ID가 나오면 while문 종료 마지막 이후 조회로 간주

            last_article_id = current_article_id

            # 실제 데이터 가공
            news_data = parse_news_data(soup, date_str)

            # 중복된 URL을 확인하여 이미 존재하는 기사는 제외
            for article in news_data:
                if article['main_url'] not in url_set:
                    all_news_data.append(article)  # 중복되지 않은 기사만 추가
                    url_set.add(article['main_url'])  # URL 집합에 추가

            print(f"news_data : {news_data}")

            page += 1

    return all_news_data



# 댓글 수 기준 상위 2개의 기사 선택
def get_top_articles(all_news_data):
    # 데이터가 비어있거나 기사가 1개 또는 2개일 경우 그대로 리턴
    if not all_news_data or len(all_news_data) <= 2:
        return all_news_data

    # 댓글 수가 있는 기사를 필터링
    articles_with_comments = [article for article in all_news_data if int(article['comment_count']) > 0]

    if len(articles_with_comments) >= 2:
        # 댓글 수가 있는 기사가 2개 이상이면 상위 2개 선택
        top_articles = sorted(articles_with_comments, key=lambda x: int(x['comment_count']), reverse=True)[:2]
    elif len(articles_with_comments) == 1:
        # 댓글 수가 있는 기사가 1개면 그 기사 + 최신 기사 1개 선택
        latest_article = all_news_data[-1] if all_news_data[-1] != articles_with_comments[0] else all_news_data[-2]
        top_articles = [articles_with_comments[0], latest_article]
    else:
        # 댓글 수가 있는 기사가 없으면 최신 기사 2개 선택
        top_articles = all_news_data[-2:]

    return top_articles



# main 함수
def main():

    print("start")

    # 오늘 날짜를 기준으로 최신 뉴스 데이터를 수집 =============================================
    current_date = datetime.now()
    date_str = current_date.strftime('%Y%m%d')
    news_data = get_news_data_today(date_str)
    ## 실제로는 news_data값을 리턴하면 됨
    print(f"작업 완료 : {news_data}")

    for article in news_data:
        print(f"Title: {article['title']}, Comments: {article['comment_count']}, URL: {article['main_url']}")

    print("==============================================================")

    # hot 데이터 2개 부분 ==================================================================
    # 월1일 부터 현재까지 모든 뉴스 데이터 수집  =============================================
    # 실제로는 top_articles값을 return 하면 됨
    all_news_data = collect_news_data()
    # 댓글 수 상위 2개의 기사 선택 hot
    top_articles = get_top_articles(all_news_data)

    # 결과 출력
    for article in top_articles:
        print(f"Title: {article['title']}, Comments: {article['comment_count']}, URL: {article['main_url']}")


if __name__ == "__main__":
    main()
