import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.common.exceptions import NoSuchElementException

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")

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

    return driver

def fetch_reviews(driver, index):
    url = f'https://saladlab.shop/api/widget_sub/boardAlphareview/new/paging?widget_id=17216&index={index}&keyword=&keyword_m=&page_type=w&sort=-created_at&initial=false&filter=%7B%7D&value=12'
    driver.get(url)
    time.sleep(random.uniform(2, 5))  # 2~5초 사이의 랜덤한 시간 동안 대기

    reviews = []

    try:
        widget_w = driver.find_element(By.CLASS_NAME, 'widget_w')
        items = widget_w.find_elements(By.CLASS_NAME, 'widget_item.review')
    except NoSuchElementException:
        print(f"No reviews found on page {index}")
        return reviews

    for item in items:
        review = {}

        stars = item.find_elements(By.CLASS_NAME, 'alph_star_full')
        review['rating'] = len(stars)

        try:
            username = item.find_element(By.CLASS_NAME, 'widget_item_none_username_2').text
        except NoSuchElementException:
            username = "N/A"
        review['username'] = username

        try:
            review_box = item.find_element(By.CLASS_NAME, 'widget_item_review_box')
            badges = review_box.find_elements(By.CLASS_NAME, 'widget_item_badge_box')

            # 배지 텍스트 제외
            for badge in badges:
                driver.execute_script("arguments[0].remove();", badge)

            review['text'] = review_box.text.strip()
        except NoSuchElementException:
            review['text'] = "N/A"

        print(f"review : {review}")
        reviews.append(review)

    return reviews

def main():
    driver = setup_driver()
    all_reviews = []

    try:
        for index in range(1, 5512):
            print(f'Fetching page {index}...')
            reviews = fetch_reviews(driver, index)
            all_reviews.extend(reviews)
            time.sleep(random.uniform(2, 5))  # 2~5초 사이의 랜덤한 시간 동안 대기

    finally:
        driver.quit()

    # 리뷰 데이터를 DataFrame으로 변환
    df = pd.DataFrame(all_reviews)

    # 데이터를 엑셀 파일로 저장
    df.to_excel('reviews.xlsx', index=False)
    print('to_excel end...')

if __name__ == "__main__":
    main()
