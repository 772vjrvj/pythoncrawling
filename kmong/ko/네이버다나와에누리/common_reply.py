import calendar
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# 리뷰수 단위 테스트

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    chrome_options.add_argument("--lang=en-US")  # Set language to English
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                });
            '''
        })
        return driver
    except Exception as e:
        print(f"Error setting up the driver: {e}")
        return None

def previous_month_date(today):
    current_day = today.day
    current_month = today.month
    current_year = today.year

    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_year = current_year

    last_day_of_previous_month = calendar.monthrange(previous_year, previous_month)[1]

    start_date_of_previous_month = today.replace(
        year=previous_year,
        month=previous_month,
        day=min(current_day, last_day_of_previous_month)
    )

    return start_date_of_previous_month

def check_previous_month_add(today, start_date_of_previous_month, input_date):
    date_object = datetime.strptime(input_date.strip(), '%y.%m.%d.')
    if start_date_of_previous_month <= date_object <= today:
        return 1
    elif date_object > today:
        return 0
    else:
        return -1

def get_month_review_cnt(driver, naver_url, email_data):
    driver.get(naver_url)
    time.sleep(3)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    month_review_cnt = 0

    try:
        element = driver.find_element(By.CSS_SELECTOR, 'a[data-shp-contents-id="최신순"]')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        element.click()
        time.sleep(2)
    except Exception as e:
        print("Initial sort button click error:", e)
        return month_review_cnt

    group_page = 0
    today = datetime.now()  # 현재 날짜 및 시간
    start_date_of_previous_month = previous_month_date(today)

    while True:
        for page_num in range(1, 11):  # 한 번에 최대 10페이지까지 탐색
            try:
                page_button = driver.find_element(By.CSS_SELECTOR, f'a[data-shp-contents-id="{group_page + page_num}"]')
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_button)
                page_button.click()
                time.sleep(2)

                review_items = driver.find_elements(By.CSS_SELECTOR, '.reviewItems_list_review__q726A li')

                for li in review_items:
                    try:
                        div_date = li.find_element(By.CLASS_NAME, "reviewItems_etc_area__3VUjt")
                        span_tags = div_date.find_elements(By.CSS_SELECTOR, '.reviewItems_etc__9ej69')

                        input_date = span_tags[2].text.strip()

                        check = check_previous_month_add(today, start_date_of_previous_month, input_date)

                        if check == -1:
                            print("-1 returned, stopping.")
                            return month_review_cnt

                        month_review_cnt += check

                        if month_review_cnt > email_data['리뷰수']:
                            print("Review count exceeded, stopping.")
                            return month_review_cnt
                    except Exception as e:
                        print(f"Review item parsing error: {e}")

                print(f'month_review_cnt: {month_review_cnt}')

            except Exception as e:
                print(f"Page {page_num} click failed or not found: {e}")
                return month_review_cnt

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, '.pagination_next__3_3ip')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            next_button.click()
            group_page += 10
            time.sleep(2)
        except Exception:
            print("Reached last pagination group.")
            return month_review_cnt

def main():
    email_data = {'리뷰수': 30}
    naver_url = "https://search.shopping.naver.com/catalog/51929476255"
    driver = setup_driver()

    if driver is None:
        print("Driver setup failed. Exiting.")
        return

    global_month_review_cnt = get_month_review_cnt(driver, naver_url, email_data)
    print(f'global_month_review_cnt : {global_month_review_cnt}')

    if global_month_review_cnt > email_data['리뷰수']:
        result = f"{email_data['리뷰수']}+"
    else:
        result = f"{email_data['리뷰수']}"

    print(f'result : {result}')
    driver.quit()

if __name__ == "__main__":
    main()
