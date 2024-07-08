import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import random
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


def get_links_from_page(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "a.post_link_wrap._fade_link")
        links = [elem.get_attribute('href') for elem in elements]
        return links
    except NoSuchElementException:
        print("Element not found!")
        return []


def click_pagination_and_collect_links(driver):
    all_links = []
    while True:
        all_links.extend(get_links_from_page(driver))

        try:
            pagination = driver.find_element(By.CSS_SELECTOR, "ul.pagination")
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

    return all_links


def extract_data_from_page(driver, url):
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 3))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "write")))

        data = {}

        try:
            write_elem = driver.find_element(By.CLASS_NAME, "write")
            data['아이디'] = write_elem.text
        except NoSuchElementException:
            data['아이디'] = ""

        try:
            content_elems = driver.find_elements(By.CLASS_NAME, "margin-top-xxl")
            if content_elems:
                content_elem = content_elems[-1]
                data['내용'] = content_elem.text

                img_elements = content_elem.find_elements(By.TAG_NAME, "img")
                for idx, img in enumerate(img_elements):
                    data[f'이미지url-{idx+1}'] = img.get_attribute('src')
            else:
                data['내용'] = ""
        except NoSuchElementException:
            data['내용'] = ""
        data['URL'] = url

        print(f"data : {data}")

        return data
    except TimeoutException:
        print(f"Loading the page {url} took too much time!")
        return None


def main():
    driver = setup_driver()
    if driver is not None:
        url = "https://balboa-world.com/review"
        driver.get(url)
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post_link_wrap")))

        all_links = click_pagination_and_collect_links(driver)

        all_data = []
        for link in all_links:
            data = extract_data_from_page(driver, link)
            if data:
                all_data.append(data)

        driver.quit()

        # 수집된 데이터 엑셀로 저장
        df = pd.DataFrame(all_data)
        df.to_excel('balboa_data.xlsx', index=False)

        print("Data saved to balboa_data.xlsx")

if __name__ == "__main__":
    main()
