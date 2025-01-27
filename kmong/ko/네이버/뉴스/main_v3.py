from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
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
    # chrome_options.add_argument("--disable-gpu")
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

# 뉴스 데이터를 요청하고 파싱하는 함수
def fetch_news_data(date_str):
    header = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    url = f"https://news.naver.com/breakingnews/section/103/238?date={date_str}"

    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.select('.sa_item._LAZY_LOADING_WRAP')
        return articles

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch news data for date {date_str}: {e}")
        return []

# 기사의 상세 정보와 댓글을 추출하는 함수
def scrape_article(driver, article, date_str):
    try:
        main_url = article.select_one('.sa_text_title._NLOG_IMPRESSION')['href']
        if not main_url.startswith('http'):
            main_url = 'https://news.naver.com' + main_url

        title = article.select_one('.sa_text_title._NLOG_IMPRESSION .sa_text_strong').get_text(strip=True)
        comment_url_element = article.select_one('.sa_text_cmt._COMMENT_COUNT_LIST')
        comment_url = comment_url_element['href'] if comment_url_element else ""
        if comment_url and not comment_url.startswith('http'):
            comment_url = 'https://news.naver.com' + comment_url

        image_thumb_element = article.select_one('.sa_thumb_inner .sa_thumb_link._NLOG_IMPRESSION img')
        image_thumb = image_thumb_element.get('data-src') if image_thumb_element else ""

        # 상세 기사 및 댓글 데이터 크롤링
        content, journalist_name, like_count, comment_count = scrape_article_content(driver, main_url)
        comments = scrape_comments(driver, comment_url) if comment_url else []

        return {
            'date': date_str,
            'title': title,
            'journalist_name': journalist_name if journalist_name else "",
            'like_count': like_count,
            'content': content if content else "",
            'comment_count': comment_count,
            'main_url': main_url,
            'comment_url': comment_url,
            'image_thumb': image_thumb,
            'comments': comments
        }

    except Exception as e:
        print(f"Error scraping article data: {e}")
        return None

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
    content = content_element.text if content_element else ""

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
        journalist_name = journalist_element.text if journalist_element else ""
    except Exception:
        journalist_name = ""

    return content, journalist_name, like_count, comment_count

# 특정 날짜의 전체 뉴스 데이터를 가져오는 함수
def get_news_data_today(date_str):
    news_data = []
    driver = setup_driver()

    print(f"date_str : {date_str} 시작")
    articles = fetch_news_data(date_str)

    for article in articles:
        obj = scrape_article(driver, article, date_str)
        if obj:
            news_data.append(obj)

    print(f"news_data : {news_data}")
    driver.quit()
    return news_data

# 특정 날짜의 최신 10개 뉴스 데이터를 가져오는 함수
def get_news_data_until_10(current_date):

    date_str = current_date.strftime('%Y%m%d')

    news_data = []
    driver = setup_driver()

    while len(news_data) < 10:
        articles = fetch_news_data(date_str)
        for article in articles:
            obj = scrape_article(driver, article, date_str)
            if obj:
                news_data.append(obj)

            if len(news_data) >= 10:
                break

        # 다음날로 이동 (전날로 날짜 감소)
        current_date = datetime.strptime(date_str, '%Y%m%d')
        previous_date = current_date - timedelta(days=1)
        date_str = previous_date.strftime('%Y%m%d')

    driver.quit()
    return news_data

# hot2 데이터
def get_top_articles_recent_days(current_date):
    all_news_data = []
    checked_dates = set()  # 중복 방지용 집합

    # 오늘과 전날의 데이터를 우선 조회
    for _ in range(2):
        date_str = current_date.strftime('%Y%m%d')
        if date_str not in checked_dates:
            print(f"Fetching data for date: {date_str}")

            # 해당 날짜의 전체 뉴스 데이터를 가져옴
            news_data = get_news_data_today(date_str)
            if news_data:
                all_news_data.extend(news_data)

            # 중복 방지용 날짜 저장
            checked_dates.add(date_str)

        # 전날로 이동
        current_date -= timedelta(days=1)

    while True:
        if len(all_news_data) >= 2:
            # 댓글 수가 있는 기사를 필터링
            articles_with_comments = [article for article in all_news_data if int(article['comment_count']) > 0]

            if len(articles_with_comments) >= 2:
                # 댓글 수가 있는 기사가 2개 이상이면 상위 2개 선택
                top_articles = sorted(articles_with_comments, key=lambda x: int(x['comment_count']), reverse=True)[:2]
                return top_articles
            elif len(articles_with_comments) == 1:
                # 댓글 수 있는 기사가 1개이면, 그 기사 + 최신 기사 1개 선택
                latest_article = all_news_data[-1] if all_news_data[-1] != articles_with_comments[0] else all_news_data[-2]
                top_articles = [articles_with_comments[0], latest_article]
                return top_articles
            else:
                # 댓글 수 있는 기사가 없다면, 최신 기사 2개 선택
                top_articles = all_news_data[-2:]
                return top_articles

        # 2개보다 적을 경우, 더 이전 날짜의 데이터를 조회
        current_date -= timedelta(days=1)
        date_str = current_date.strftime('%Y%m%d')

        if date_str not in checked_dates:
            print(f"Fetching additional data for date: {date_str}")

            # 해당 날짜의 전체 뉴스 데이터를 가져옴
            news_data = get_news_data_today(date_str)
            if news_data:
                all_news_data.extend(news_data)

            # 중복 방지용 날짜 저장
            checked_dates.add(date_str)
        else:
            print(f"Already checked data for date: {date_str}, skipping to avoid duplicates.")

# main 함수
def main():
    print("start")

    # 오늘 날짜를 기준으로 최신 10개 뉴스 데이터를 수집 =============================================
    current_date = datetime.now()

    # 오늘 날짜의 최신 10개 뉴스를 수집
    news_data = get_news_data_until_10(current_date)

    # 실제로는 news_data값을 리턴하면 됨
    for article in news_data:
        print(f"Title: {article['title']}, Comments: {article['comment_count']}, URL: {article['main_url']}")

    print("==============================================================")

    # hot 데이터 2개 부분 ==================================================================
    # 최근 며칠 내의 'hot' 기사 2개 선택
    top_articles = get_top_articles_recent_days(current_date)

    # 결과 출력
    for article in top_articles:
        print(f"Title: {article['title']}, Comments: {article['comment_count']}, URL: {article['main_url']}")


if __name__ == "__main__":
    main()
