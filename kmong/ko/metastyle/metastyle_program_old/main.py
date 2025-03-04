import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def setup_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_total_count(driver, url):
    driver.get(url)
    time.sleep(3)
    count_element = driver.find_element(By.CSS_SELECTOR, "span.result_count")
    total_cnt = int(re.sub(r'[^0-9]', '', count_element.text)) if count_element else 0
    return total_cnt

def get_product_details(driver, product_url):
    driver.get(product_url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_details = {}

    product_details['product_title'] = soup.select_one("h1.product-title").get_text(strip=True) if soup.select_one("h1.product-title") else ""

    product_details['product_sub_title'] = soup.select_one("div.sub-product-title a").get_text(strip=True) if soup.select_one("div.sub-product-title a") else ""

    features_section = soup.find("p", string="FEATURES")
    product_details['product_features'] = [li.get_text(strip=True) for li in features_section.find_next("ul").find_all("li")] if features_section else []

    fabric_care_section = soup.find("p", string="FABRIC & CARE")
    product_details['product_fabric_care'] = [li.get_text(strip=True) for li in fabric_care_section.find_next("ul").find_all("li")] if fabric_care_section else []

    # 첫 번째 이미지 가져오기 (srcset에서 가장 큰 해상도 URL 추출)
    main_image_element = soup.select_one(".pdp-large-hero-image img")
    if main_image_element and "srcset" in main_image_element.attrs:
        product_details['product_img_1'] = main_image_element["srcset"].split(",")[0].split(" ")[0]
    else:
        product_details['product_img_1'] = main_image_element["src"] if main_image_element else ""

    # 대체 이미지 가져오기 (video 클래스 제외)
    product_details['product_img_2'] = ""
    product_details['product_img_3'] = ""
    product_details['product_img_4'] = ""

    image_elements = soup.select(".pdp-large-alt-images .large-alt-image:not(.video) img")
    for idx, img in enumerate(image_elements[:3]):
        product_details[f'product_img_{idx + 2}'] = img["src"]

    return product_details

def get_products_from_page(driver, url):
    driver.get(url)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_list = []
    product_elements = soup.select("#productsContainer > li")

    for product in product_elements:
        try:
            product_id = product.get("data-id", "")
            product_element_id = product.get("id", "")

            if not product_element_id or "scroll_id_" not in product_element_id:
                continue

            product_name_tag = product.select_one(".products-container-right .prod_nameBlock p")
            product_name = product_name_tag.get_text(strip=True) if product_name_tag else ""

            product_link_element = product.select_one(".prod_img_block > a")
            product_url = product_link_element["href"] if product_link_element else ""
            if product_url and not product_url.startswith("https://www.kohls.com"):
                product_url = "https://www.kohls.com" + product_url

            product_details = get_product_details(driver, product_url)

            product_data = {
                "product_id": product_id,
                "product_name": product_name,
                "product_url": product_url,
                **product_details
            }

            product_list.append(product_data)
            print(product_data)
            time.sleep(3)
            break
        except Exception as e:
            print(f"Error processing product: {e}")
            continue

    return product_list

def main():
    base_url = "https://www.kohls.com/catalog/womens-shirts-blouses-tops-clothing.jsp?CN=Gender:Womens+Product:Shirts%20%26%20Blouses+Category:Tops+Department:Clothing"

    driver = setup_driver()
    total_cnt = get_total_count(driver, base_url)
    total_pages = (total_cnt // 48) + (1 if total_cnt % 48 > 0 else 0)

    products = []
    for page in range(total_pages):
        ws_value = page * 48
        page_url = f"{base_url}&WS={ws_value}"
        print(f"Scraping page {page + 1} - {page_url}")

        page_products = get_products_from_page(driver, page_url)
        if not page_products:
            break

        products.extend(page_products)

    driver.quit()

    for product in products:
        print(product)
        time.sleep(3)

if __name__ == "__main__":
    main()
