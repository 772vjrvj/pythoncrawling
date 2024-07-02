from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import random

AUTH = 'brd-customer-hl_7b5686a6-zone-scraping_browser1:1myeocpnrd19'
SBR_WEBDRIVER = f'https://{AUTH}@zproxy.lum-superproxy.io:9515'

def main():
    print('Connecting to Scraping Browser...')
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        print('Connected! Navigating...')
        driver.implicitly_wait(5)
        driver.get('https://www.coupang.com/vp/products/7355580399?itemId=18938714252&vendorItemId=86065251632&q=%EB%85%B8%ED%8A%B8%EB%B6%81&itemsCount=35&searchId=c3c0af5b0289443fa0027ded85e4ee83&rank=9&isAddedCart=')
        time.sleep(random.uniform(2,3))
        driver.find_element(By.NAME, "review").click()
        time.sleep(random.uniform(2,3))

        try:
            # driver.find_element(By.CSS_SELECTOR, ".sdp-review__article__no-review--active") # 등록된 상품평이 없습니다.
            time.sleep(random.uniform(2,3))
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".sdp-review__article__no-review--active"))
            )

            print("등록된 상품평이 없습니다.")
            print()

        except:
            #다음 페이지 넘어가는것도 해보기
            review_btns = driver.find_elements(By.CSS_SELECTOR, ".js_reviewArticlePageBtn")

            if len(review_btns) == 0:
                reviews = driver.find_elements(By.CSS_SELECTOR, ".js_reviewArticleReviewList")
                print(f"상품평 총 {len(reviews)}개")
            else:
                print(f"상품평 총 {len(review_btns)}페이지")
            print()

            data_page_num = 1

            print(f"현재 페이지는 {data_page_num} 입니다.")

            while True:

                reviews = driver.find_elements(By.CSS_SELECTOR, ".sdp-review__article__list.js_reviewArticleReviewList")

                for review in reviews:
                    # 작성자명
                    try:
                        review_user_name = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__user__name.js_reviewUserProfileImage").text
                    except:
                        review_user_name = "없음"

                    # 평점
                    try:
                        rating = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__star-orange.js_reviewArticleRatingValue").get_attribute("data-rating")
                    except:
                        rating = "없음"

                    # 작성일
                    try:
                        review_date = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__reg-date").text
                    except:
                        review_date = "없음"

                    # 제품명
                    try:
                        product_info_name = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__name").text
                    except:
                        product_info_name = "없음"

                    # 제목
                    try:
                        review_headline = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__headline").text
                    except:
                        review_headline = "없음"

                    # 본문
                    try:
                        review_content = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__review__content.js_reviewArticleContent").text
                    except:
                        review_content = "없음"

                    print(f"리뷰어: {review_user_name}")
                    print(f"평점: {rating} 작성일: {review_date}")
                    print(f"제품명: {product_info_name}")
                    print(f"제목: {review_headline}")
                    print(f"본문: {review_content}")
                    print()

                    #설문조사
                    try:
                        survey = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__survey").text
                        print()
                        print(f"{survey}")
                    except:
                        pass
                    print()

                data_page_num += 1

                if data_page_num > len(review_btns):
                    break

                print(f"현재 페이지는 {data_page_num} 입니다.")

                review_btn = driver.find_element(By.CSS_SELECTOR, f".js_reviewArticlePageBtn[data-page='{data_page_num}']")
                review_btn.click()
                time.sleep(random.uniform(2,3))


if __name__ == '__main__':
    main()