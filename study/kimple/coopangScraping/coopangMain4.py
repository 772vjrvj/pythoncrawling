from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import warnings
import time
import random
import csv

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

AUTH = 'brd-customer-hl_7b5686a6-zone-scraping_browser1:1myeocpnrd19'
SBR_WEBDRIVER = f'https://{AUTH}@zproxy.lum-superproxy.io:9515'

host = "brd.superproxy.io:22225"
user_name = "brd-customer-hl_7b5686a6-zone-web_unlocker1"
password = "rl3in84k3t57"
proxy_url = f"https://{user_name}:{password}@{host}"

proxies = {"http": proxy_url, "https": proxy_url}

print(proxy_url)

keyword = input("검색할 제품 입력 : ")

link_list = []
with open(f"coupang_{keyword}.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["제품명", "가격", "링크"])
    for page_num in range(1, 2):
        print(f"<<<<<{page_num}페이지>>>>>")
        url = f"https://www.coupang.com/np/search?component=&q={keyword}&page={page_num}&listSize=36"
        print(url)
        print()
        response = requests.get(url, proxies=proxies, verify=False)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        #광고까지 가져옴
        # items = soup.select(".search-product")
        items = soup.select("[class=search-product]")

        print(len(items))

        for index, item in enumerate(items):

            name = item.select_one(".name").text
            price = item.select_one(".price-value")
            if not price:
                continue
            else:
                price = price.text

            link = f"https://coupang.com{item.a['href']}"

            link_list.append(link)

            writer.writerow([name, price, link])

            print(f"index : {index}")
            print(f"{name} : {price}")
            print(link)
            print()


print(link_list)
print(len(link_list))

for url in link_list:

    print('Connecting to Scraping Browser...')
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        print('Connected! Navigating...')
        driver.implicitly_wait(5)
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        brand = soup.select_one(".prod-brand-name")
        brand = "" if not brand else brand.text.strip()

        title = soup.select_one(".prod-buy-header__title")
        title = "" if not title else title.text.strip()

        seller = soup.select_one(".prod-sale-vendor-name")
        seller = "로켓배송" if not seller else seller.text.strip()

        prod_sale_price = soup.select_one(".prod_sale-price") #현재 판매가
        prod_coupon_price = soup.select_one(".prod-coupon-price") #현재 할인가

        if prod_sale_price and prod_sale_price.select_one(".total-price"):
            prod_sale_price = prod_sale_price.select_one(".total-price").text.strip()
        else:
            prod_sale_price = ""


        if prod_coupon_price and prod_coupon_price.select_one(".total-price"):
            prod_coupon_price = prod_coupon_price.select_one(".total-price").text.strip()
        else:
            prod_coupon_price = ""

        print(url)
        print(f"브랜드: {brand}, 제품명: {title}, 현재 판매가: {prod_sale_price}, 회원 판매가: {prod_coupon_price}")

        prod_option_item = soup.select(".prod-option__item") # 옵션

        if prod_option_item:
            option_list = []
            for item in prod_option_item:
                title = item.select_one(".title").string.strip()
                value = item.select_one(".value").string.strip()
                option_list.append(f"{title}: {value}")
            prod_option_item = ", ".join(option_list)
            print(prod_option_item)
        else:
            prod_option_item = ""

        prod_description = soup.select(".prod-description .prod-attr-item") # 상세정보

        if prod_description:
            description_list = []
            for description in prod_description:
                description_list.append(description.string.strip())
            prod_description = ", ".join(description_list)
            print(prod_description)
        else:
            prod_description = ""

        # 리뷰 ======================================================================================

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

                for e, review in enumerate(reviews, 1):

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

                    print(f"======{data_page_num}페이지 {e}번 리뷰=====")
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

                # 다음 페이지 버튼 클릭
                try:
                    review_btn = driver.find_element(By.CSS_SELECTOR, f".js_reviewArticlePageBtn[data-page='{data_page_num}']")
                    review_btn.click()
                    time.sleep(random.uniform(2,3))
                except NoSuchElementException:
                    break




        print()