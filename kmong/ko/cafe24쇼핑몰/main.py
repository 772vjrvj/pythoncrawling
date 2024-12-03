from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException, WebDriverException, StaleElementReferenceException, UnexpectedAlertPresentException
import time
import pandas as pd
from urllib.parse import urljoin



def setup_driver():
    chrome_options = Options()
    # 필요 시 headless 모드로 실행
    # chrome_options.add_argument("--headless")
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

def get_category_links(driver):
    category_links = []
    try:
        # 카테고리 요소 찾기
        category_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "xans-element-.xans-layout.xans-layout-category"))
        )
        # li 요소들 찾기
        li_elements = category_element.find_elements(By.TAG_NAME, "li")

        # 각 li 요소 내의 a 요소를 찾아 링크 텍스트와 URL을 객체 배열에 저장
        for idx, li in enumerate(li_elements):
            try:
                a_element = li.find_element(By.TAG_NAME, "a")
                link_text = a_element.text
                link_url = a_element.get_attribute('href')
                category_links.append({"text": link_text, "url": link_url})
            except NoSuchElementException:
                continue
    except NoSuchElementException as e:
        print(f"Error occurred while retrieving category links: {e}")

    return category_links


def get_prd_img_urls(driver):
    prd_img_urls = []
    prd_lists = driver.find_elements(By.CLASS_NAME, "prdList")

    # prdList 내의 prdImg 요소들에서 이미지 URL을 가져와 리스트에 추가
    for prd_list in prd_lists:
        prd_imgs = prd_list.find_elements(By.CLASS_NAME, "prdImg")
        for prd_img in prd_imgs:
            try:
                a_element = prd_img.find_element(By.TAG_NAME, "a")
                prd_img_urls.append(a_element.get_attribute('href'))
            except NoSuchElementException:
                continue

    return prd_img_urls


# 테스트 코드
def navigate_pages_test(driver):
    all_img_urls = []
    prd_img_urls = get_prd_img_urls(driver)
    all_img_urls.extend(prd_img_urls)
    return all_img_urls


def navigate_pages(driver):
    all_img_urls = []
    current_page = 1

    while True:
        print(f"Scraping page {current_page}")
        prd_img_urls = get_prd_img_urls(driver)
        all_img_urls.extend(prd_img_urls)

        try:
            # 페이지네이션 요소 찾기
            paging_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "xans-element-.xans-product.xans-product-normalpaging"))
            )
            pages = paging_element.find_elements(By.CSS_SELECTOR, "ol a")

            # 다음 페이지 찾기
            next_page = None
            for page in pages:
                if page.text == str(current_page + 1):
                    next_page = page
                    break

            if next_page:
                # 다음 페이지 클릭
                next_page.click()
                time.sleep(2)
                WebDriverWait(driver, 10).until(EC.staleness_of(paging_element))
                current_page += 1
            else:
                try:
                    next_button = paging_element.find_element(By.XPATH, 'ol/following-sibling::a')
                    previous_url = driver.current_url
                    next_button.click()
                    time.sleep(2)
                    WebDriverWait(driver, 10).until(EC.staleness_of(paging_element))

                    # URL이 변경되었는지 확인
                    if driver.current_url == previous_url:
                        print("Reached the last page.")
                        break

                    current_page += 1
                except NoSuchElementException:
                    print("No more pages.")
                    break

        except NoSuchElementException as e:
            print(f"Pagination element not found: {e}")
            break
        except StaleElementReferenceException as e:
            print(f"StaleElementReferenceException occurred: {e}. Retrying...")
            continue
        except WebDriverException as e:
            print(f"WebDriverException occurred: {e}")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    return all_img_urls

def wait_for_images_to_load(driver):
    # Wait for any image that does not contain 'data:image' in its src attribute
    time.sleep(2)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//img[not(starts-with(@src, 'data:image'))]"))
    )

def scrape_product_details(driver, url, category_text):
    retries = 3
    while retries > 0:
        try:
            driver.get(url)
            wait_for_images_to_load(driver)  # Wait for images to load


            product = {}
            product["카테고리"] = category_text

            base_url = driver.current_url

            try:
                img_area = driver.find_element(By.CLASS_NAME, "xans-element-.xans-product.xans-product-image.imgArea")
                img_tag = img_area.find_element(By.TAG_NAME, "img")
                img_src = img_tag.get_attribute('src')
                product["상품 이미지"] = urljoin(base_url, img_src)
            except NoSuchElementException:
                product["상품 이미지"] = None

            try:
                product_info = driver.find_element(By.CLASS_NAME, "product_info")
                tbody = product_info.find_element(By.TAG_NAME, "tbody")
                first_tr = tbody.find_element(By.TAG_NAME, "tr")
                product_name = first_tr.find_element(By.TAG_NAME, "td").text
                product["상품 리스트"] = product_name
            except NoSuchElementException:
                product["상품 리스트"] = None


            print(f"Scraped product details: {product}")

            return product

        except StaleElementReferenceException:
            print("StaleElementReferenceException occurred. Retrying...")
            retries -= 1
            time.sleep(2)

    print("Failed to scrape product details after several retries.")
    return {}
def main():
    driver = setup_driver()
    if driver is not None:
        base_url = "https://ba-on.com"

        # base_url = "https://addmore.co.kr/"

        driver.get(base_url)
        time.sleep(3)

        all_products = []

        try:
            # 카테고리 링크 가져오기
            category_links = get_category_links(driver)

            # 각 카테고리 링크를 순회하며 처리
            for index, category in enumerate(category_links):

                # 테스트 코드
                if index >= 3:
                    break

                try:
                    print(f"Scraping category: {category['text']}")
                    driver.get(category['url'])
                    time.sleep(3)

                    # 테스트 코드
                    img_urls = navigate_pages_test(driver)
                    
                    # img_urls = navigate_pages(driver)
                    print(f"Collected {len(img_urls)} image URLs from {category['text']}")

                    # 각 이미지 URL에서 제품 상세 정보 스크랩
                    for idx, img_url in enumerate(img_urls):

                        # 테스트 코드
                        if idx >= 3:
                            break

                        product = scrape_product_details(driver, img_url, category['text'])
                        all_products.append(product)

                except NoSuchElementException:
                    continue
                except StaleElementReferenceException as e:
                    print(f"StaleElementReferenceException occurred while processing categories: {e}. Retrying...")
                    time.sleep(2)
                    continue
                except UnexpectedAlertPresentException:
                    try:
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        print(f"Alert Text: {alert_text}")
                        alert.accept()
                    except NoAlertPresentException:
                        pass

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
