from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException, NoAlertPresentException, TimeoutException, StaleElementReferenceException
import time
import pandas as pd

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 필요 시 headless 모드로 실행
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")  # 시크릿 모드 사용

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

def is_alert_present(driver):
    try:
        driver.switch_to.alert
        return True
    except NoAlertPresentException:
        return False

def get_prd_img_urls(driver):
    prd_img_urls = []
    prd_lists = driver.find_elements(By.CLASS_NAME, "prdList")

    for prd_list in prd_lists:
        prd_imgs = prd_list.find_elements(By.CLASS_NAME, "prdImg")
        for prd_img in prd_imgs:
            try:
                a_element = prd_img.find_element(By.TAG_NAME, "a")
                prd_img_urls.append(a_element.get_attribute('href'))
            except NoSuchElementException:
                continue

    return prd_img_urls

def navigate_pages(driver):
    all_img_urls = []
    current_page = 1

    while True:
        print(f"Scraping page {current_page}")
        prd_img_urls = get_prd_img_urls(driver)
        all_img_urls.extend(prd_img_urls)

        try:
            paging_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "xans-element-.xans-product.xans-product-normalpaging"))
            )
            pages = paging_element.find_elements(By.TAG_NAME, "a")

            next_page = None
            for page in pages:
                if page.text == str(current_page + 1):
                    next_page = page
                    break

            if next_page:
                next_page.click()
                WebDriverWait(driver, 10).until(EC.staleness_of(paging_element))
                current_page += 1
                time.sleep(2)
            else:
                try:
                    next_button_img = driver.find_element(By.CSS_SELECTOR, 'img[alt="다음 페이지"]')
                    next_button_img.click()
                    WebDriverWait(driver, 10).until(EC.staleness_of(paging_element))
                    current_page += 1
                    time.sleep(2)
                except NoSuchElementException:
                    try:
                        next_button_text = driver.find_element(By.XPATH, '//a[text()="NEXT"]')
                        next_button_text.click()
                        WebDriverWait(driver, 10).until(EC.staleness_of(paging_element))
                        current_page += 1
                        time.sleep(2)
                    except NoSuchElementException:
                        print("No more pages.")
                        break

        except NoSuchElementException:
            print("Pagination element not found. Exiting.")
            break
        except StaleElementReferenceException:
            print("StaleElementReferenceException occurred. Retrying...")
            continue

    return all_img_urls

def scrape_product_details(driver, url):
    driver.get(url)
    time.sleep(3)

    product = {}

    try:
        img_area = driver.find_element(By.CLASS_NAME, "xans-element-.xans-product.xans-product-image.imgArea")
        img_tag = img_area.find_element(By.TAG_NAME, "img")
        product["이미지"] = img_tag.get_attribute('src')
    except NoSuchElementException:
        product["이미지"] = None

    try:
        product_info = driver.find_element(By.CLASS_NAME, "product_info")
        tbody = product_info.find_element(By.TAG_NAME, "tbody")
        first_tr = tbody.find_element(By.TAG_NAME, "tr")
        product_name = first_tr.find_element(By.TAG_NAME, "td").text
        product["제품명"] = product_name
    except NoSuchElementException:
        product["제품명"] = None

    print(f"Scraped product details: {product}")
    return product

def main():
    driver = setup_driver()
    if driver is not None:
        base_url = "https://ba-on.com"
        driver.get(base_url)
        time.sleep(3)

        all_products = []

        try:
            # 카테고리 찾기
            category_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "xans-element-.xans-layout.xans-layout-category"))
            )
            # 그 안의 li 요소들 찾기
            li_elements = category_element.find_elements(By.TAG_NAME, "li")

            for idx, li in enumerate(li_elements):
                try:
                    # li 안의 a 요소 찾기
                    a_element = li.find_element(By.TAG_NAME, "a")
                    # a 요소의 텍스트와 URL 가져오기
                    link_text = a_element.text
                    link_url = a_element.get_attribute('href')

                    if link_text and link_url:
                        print(f"Scraping category: {link_text}")
                        driver.get(link_url)
                        time.sleep(3)
                        img_urls = navigate_pages(driver)
                        print(f"Collected {len(img_urls)} image URLs from {link_text}")

                        for img_url in img_urls:
                            product = scrape_product_details(driver, img_url)
                            all_products.append(product)

                except NoSuchElementException:
                    continue
                except StaleElementReferenceException:
                    print("StaleElementReferenceException occurred while processing categories. Retrying...")
                    continue

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            driver.quit()

        # 데이터를 엑셀 파일로 저장
        df = pd.DataFrame(all_products)
        df.to_excel('products.xlsx', index=False)
        print("Data saved to products.xlsx")

if __name__ == "__main__":
    main()
