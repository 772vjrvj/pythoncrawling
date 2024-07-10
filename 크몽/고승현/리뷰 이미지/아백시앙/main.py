import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import pandas as pd

# 드라이버 세팅
def setup_driver():
    try:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Run in headless mode if necessary
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--incognito")  # Use incognito mode

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
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None

def get_review_data(driver, next_index):
    data = []
    reviews = driver.find_elements(By.CLASS_NAME, "card-head._card_head._img_wrap")

    for index, review in enumerate(reviews):
        review.click()
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "clearfix._review_modal_body"))
        )

        item = {}

        # Extract review details
        try:
            modal_right = driver.find_element(By.CLASS_NAME, "modal-right.float_l")
            write_info = modal_right.find_elements(By.CSS_SELECTOR, ".no-margin.text-13.body_font_color_60.write_info.clearfix span")
            item['번호'] = (next_index * 16) + index + 1
            item['아이디'] = write_info[0].text
            item['작성일'] = write_info[1].text
            item['페이지'] = next_index
            item['내부 번호'] = index + 1

            content_element = modal_right.find_element(By.CLASS_NAME, "txt")
            content_html = content_element.get_attribute('innerHTML')

            best = 'O' if 'review_best' in content_html else 'X'
            item['내용'] = content_html.replace('<span class="badge review_best">BEST</span>', '').strip()
            item['BEST'] = best
        except NoSuchElementException:
            pass

        # Extract image URLs
        try:
            modal_left = driver.find_element(By.CLASS_NAME, "modal-left.float_l")

            images = modal_left.find_elements(By.TAG_NAME, "img")


            images = modal_left.find_elements(By.CSS_SELECTOR, ".owl-item:not(.cloned) img")
            for idx, img in enumerate(images):
                item[f'이미지url-{idx+1}'] = img.get_attribute('src')
        except NoSuchElementException:
            pass

        print(f"item : {item}")
        data.append(item)

        driver.find_element(By.ID, "review_detail_close").click()
        time.sleep(1)

    return data

def navigate_and_collect_reviews(driver):
    all_data = []
    next_index = 0
    while True:
        try:
            all_data.extend(get_review_data(driver, next_index))

            pagination = driver.find_element(By.CLASS_NAME, "pagination")
            pages = pagination.find_elements(By.TAG_NAME, "li")

            next_page = None
            for page in pages:
                if "active" in page.get_attribute("class"):
                    next_index = pages.index(page) + 1
                    if next_index < len(pages):
                        next_page = pages[next_index]
                        break

            if next_page is None:
                next_page = driver.find_element(By.CSS_SELECTOR, 'li[aria-label="Next"]')

            next_link = next_page.find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", next_link)

            WebDriverWait(driver, 10).until(EC.staleness_of(pagination))
            time.sleep(2)

        except (NoSuchElementException, TimeoutException):
            print("No more pages or an error occurred during pagination.")
            break

    return all_data

def main():
    driver = setup_driver()
    if driver is not None:
        url = "https://avecchien.imweb.me/REVIEW/?q=YToyOntzOjEyOiJrZXl3b3JkX3R5cGUiO3M6MzoiYWxsIjtzOjQ6InBhZ2UiO2k6OTt9&page=1&only_photo=Y"
        driver.get(url)
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "card-head._card_head._img_wrap")))

        all_data = navigate_and_collect_reviews(driver)

        driver.quit()

        # 수집된 데이터 엑셀로 저장
        df = pd.DataFrame(all_data)
        df.to_excel('avecchien_reviews.xlsx', index=False)

        print("Data saved to avecchien_reviews.xlsx")

if __name__ == "__main__":
    main()
