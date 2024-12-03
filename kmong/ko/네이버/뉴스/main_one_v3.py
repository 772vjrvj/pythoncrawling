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

# 셀레니움 드라이버 세팅
chrome_options = Options()
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--window-size=1080,750")
chrome_options.add_argument("--remote-debugging-port=9222")
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
    '''
})

# 오늘 날짜를 기준으로 최신 10개 뉴스 데이터를 수집
current_date = datetime.now()
date_str = current_date.strftime('%Y%m%d')
header = {'User-agent': user_agent}
news_data = []

while len(news_data) < 10:
    url = f"https://news.naver.com/breakingnews/section/103/238?date={date_str}"
    response = requests.get(url, headers=header)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.select('.sa_item._LAZY_LOADING_WRAP')

    for article in articles:
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
        print(f"상세 시작 url :  {main_url}")
        driver.get(main_url)

        time.sleep(2)
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#newsct_article"))
        )
        content = content_element.text if content_element else ""

        time.sleep(2)
        try:
            like_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".u_likeit_text._count.num"))
            )
            like_count = like_element.text if like_element else "0"
        except Exception:
            like_count = "0"

        try:
            comment_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_cmtcount_button._COMMENT_COUNT_VIEW#comment_count"))
            )
            comment_count = comment_element.text.strip().replace("댓글", "").strip() if comment_element else "0"
            if not comment_count:
                comment_count = "0"
        except Exception:
            comment_count = "0"

        try:
            journalist_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_journalist_name"))
            )
            journalist_name = journalist_element.text if journalist_element else ""
        except Exception:
            journalist_name = ""

        comments = []
        if comment_url:
            print(f"댓글 크롤링 시작 url : {comment_url}")
            driver.get(comment_url)

            try:
                time.sleep(2)
                ul_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "u_cbox_list"))
                )
                li_elements = ul_element.find_elements(By.TAG_NAME, "li")

                for li in li_elements:
                    author = li.find_element(By.CLASS_NAME, "u_cbox_nick").text if li.find_elements(By.CLASS_NAME, "u_cbox_nick") else ""
                    content = li.find_element(By.CLASS_NAME, "u_cbox_contents").text if li.find_elements(By.CLASS_NAME, "u_cbox_contents") else ""
                    date = li.find_element(By.CLASS_NAME, "u_cbox_date").text if li.find_elements(By.CLASS_NAME, "u_cbox_date") else ""

                    if not author or not content or not date:
                        continue

                    comment_obj = {
                        "author": author,
                        "content": content,
                        "reg_date": date
                    }
                    comments.append(comment_obj)

            except Exception as e:
                print(f"댓글 영역을 찾지 못했습니다: {e}")

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
        news_data.append(obj)

    current_date -= timedelta(days=1)
    date_str = current_date.strftime('%Y%m%d')

driver.quit()

# hot 데이터 2개 부분
all_news_data = []
checked_dates = set()  # 중복 방지용 집합

# 오늘과 전날의 데이터를 우선 조회
for _ in range(2):
    date_str = current_date.strftime('%Y%m%d')
    print(f"Fetching data for date: {date_str}")

    url = f"https://news.naver.com/breakingnews/section/103/238?date={date_str}"
    response = requests.get(url, headers=header)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.select('.sa_item._LAZY_LOADING_WRAP')

    for article in articles:
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
        print(f"상세 시작 url :  {main_url}")
        driver.get(main_url)

        time.sleep(2)
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#newsct_article"))
        )
        content = content_element.text if content_element else ""

        time.sleep(2)
        try:
            like_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".u_likeit_text._count.num"))
            )
            like_count = like_element.text if like_element else "0"
        except Exception:
            like_count = "0"

        try:
            comment_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_cmtcount_button._COMMENT_COUNT_VIEW#comment_count"))
            )
            comment_count = comment_element.text.strip().replace("댓글", "").strip() if comment_element else "0"
            if not comment_count:
                comment_count = "0"
        except Exception:
            comment_count = "0"

        try:
            journalist_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_journalist_name"))
            )
            journalist_name = journalist_element.text if journalist_element else ""
        except Exception:
            journalist_name = ""

        comments = []
        if comment_url:
            print(f"댓글 크롤링 시작 url : {comment_url}")
            driver.get(comment_url)

            try:
                time.sleep(2)
                ul_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "u_cbox_list"))
                )
                li_elements = ul_element.find_elements(By.TAG_NAME, "li")

                for li in li_elements:
                    author = li.find_element(By.CLASS_NAME, "u_cbox_nick").text if li.find_elements(By.CLASS_NAME, "u_cbox_nick") else ""
                    content = li.find_element(By.CLASS_NAME, "u_cbox_contents").text if li.find_elements(By.CLASS_NAME, "u_cbox_contents") else ""
                    date = li.find_element(By.CLASS_NAME, "u_cbox_date").text if li.find_elements(By.CLASS_NAME, "u_cbox_date") else ""

                    if not author or not content or not date:
                        continue

                    comment_obj = {
                        "author": author,
                        "content": content,
                        "reg_date": date
                    }
                    comments.append(comment_obj)

            except Exception as e:
                print(f"댓글 영역을 찾지 못했습니다: {e}")

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
        all_news_data.append(obj)

    checked_dates.add(date_str)
    current_date -= timedelta(days=1)

while True:
    if len(all_news_data) >= 2:
        articles_with_comments = [article for article in all_news_data if int(article['comment_count']) > 0]

        if len(articles_with_comments) >= 2:
            top_articles = sorted(articles_with_comments, key=lambda x: int(x['comment_count']), reverse=True)[:2]
            break
        elif len(articles_with_comments) == 1:
            latest_article = all_news_data[-1] if all_news_data[-1] != articles_with_comments[0] else all_news_data[-2]
            top_articles = [articles_with_comments[0], latest_article]
            break
        else:
            top_articles = all_news_data[-2:]
            break

    date_str = current_date.strftime('%Y%m%d')
    if date_str not in checked_dates:
        print(f"Fetching additional data for date: {date_str}")

        url = f"https://news.naver.com/breakingnews/section/103/238?date={date_str}"
        response = requests.get(url, headers=header)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.select('.sa_item._LAZY_LOADING_WRAP')

        for article in articles:
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

            print(f"상세 시작 url :  {main_url}")
            driver.get(main_url)

            time.sleep(2)
            content_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#newsct_article"))
            )
            content = content_element.text if content_element else ""

            time.sleep(2)
            try:
                like_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".u_likeit_text._count.num"))
                )
                like_count = like_element.text if like_element else "0"
            except Exception:
                like_count = "0"

            try:
                comment_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_cmtcount_button._COMMENT_COUNT_VIEW#comment_count"))
                )
                comment_count = comment_element.text.strip().replace("댓글", "").strip() if comment_element else "0"
                if not comment_count:
                    comment_count = "0"
            except Exception:
                comment_count = "0"

            try:
                journalist_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".media_end_head_journalist_name"))
                )
                journalist_name = journalist_element.text if journalist_element else ""
            except Exception:
                journalist_name = ""

            comments = []
            if comment_url:
                print(f"댓글 크롤링 시작 url : {comment_url}")
                driver.get(comment_url)

                try:
                    time.sleep(2)
                    ul_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "u_cbox_list"))
                    )
                    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

                    for li in li_elements:
                        author = li.find_element(By.CLASS_NAME, "u_cbox_nick").text if li.find_elements(By.CLASS_NAME, "u_cbox_nick") else ""
                        content = li.find_element(By.CLASS_NAME, "u_cbox_contents").text if li.find_elements(By.CLASS_NAME, "u_cbox_contents") else ""
                        date = li.find_element(By.CLASS_NAME, "u_cbox_date").text if li.find_elements(By.CLASS_NAME, "u_cbox_date") else ""

                        if not author or not content or not date:
                            continue

                        comment_obj = {
                            "author": author,
                            "content": content,
                            "reg_date": date
                        }
                        comments.append(comment_obj)

                except Exception as e:
                    print(f"댓글 영역을 찾지 못했습니다: {e}")

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
            all_news_data.append(obj)

        checked_dates.add(date_str)

    current_date -= timedelta(days=1)

# 최종 결과 출력
for article in top_articles:
    print(f"Title: {article['title']}, Comments: {article['comment_count']}, URL: {article['main_url']}")

driver.quit()
