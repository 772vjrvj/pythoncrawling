import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


class Product:
    def __init__(self, image_url, name, price, category):
        self.image_url = image_url
        self.name = name
        self.price = price
        self.category = category

    def to_dict(self):
        return {
            "이미지URL": self.image_url,
            "품명": self.name,
            "가격": self.price,
            "카테고리": self.category
        }

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
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
    return driver

def extract_product_info(driver, url):
    driver.get(url)
    time.sleep(3)

    products = []

    # _1kp0Y6pSXs 클래스를 포함하는 요소를 찾기
    try:
        container = driver.find_element(By.CLASS_NAME, "_1kp0Y6pSXs")
        product_elements = container.find_elements(By.CLASS_NAME, "_3vb8-MtIrC")
        for product_element in product_elements:
            try:
                image_url = product_element.find_element(By.TAG_NAME, "img").get_attribute("src")
                name = product_element.find_element(By.CLASS_NAME, "_3tUCsjeUwv").text
                price = product_element.find_element(By.CLASS_NAME, "_2OV7zzQ3Rj").text
                category = "다른 구성"
                product = Product(image_url, name, price, category)
                products.append(product)
            except Exception as e:
                print(f"Error extracting product info: {e}")
    except Exception as e:
        print(f"Error finding _1kp0Y6pSXs container: {e}")

    # OdAoJ-HKEa 클래스를 포함하는 요소를 찾기
    try:
        containers_best_together = driver.find_elements(By.CLASS_NAME, "OdAoJ-HKEa")

        # 첫 번째 OdAoJ-HKEa 처리 (베스트 상품)
        best_product_elements = containers_best_together[0].find_elements(By.CLASS_NAME, "_1rY1-Sog8x")
        for product_element in best_product_elements:
            try:
                image_url = product_element.find_element(By.CLASS_NAME, "_25CKxIKjAk").get_attribute("src")
                name = product_element.find_element(By.CLASS_NAME, "_33pMQzgHDp").text
                price = product_element.find_element(By.CLASS_NAME, "_2CREpuMwk6").text
                category = "베스트 상품"
                product = Product(image_url, name, price, category)
                products.append(product)
            except Exception as e:
                print(f"Error extracting best product info: {e}")

        # 두 번째 OdAoJ-HKEa 처리 (함께 구매)
        together_product_elements = containers_best_together[1].find_elements(By.CLASS_NAME, "_1rY1-Sog8x")
        for product_element in together_product_elements:
            try:
                image_url = product_element.find_element(By.CLASS_NAME, "_25CKxIKjAk").get_attribute("src")
                name = product_element.find_element(By.CLASS_NAME, "_33pMQzgHDp").text
                price = product_element.find_element(By.CLASS_NAME, "_2CREpuMwk6").text
                category = "함께 구매"
                product = Product(image_url, name, price, category)
                products.append(product)
            except Exception as e:
                print(f"Error extracting together product info: {e}")
    except Exception as e:
        print(f"Error finding OdAoJ-HKEa containers: {e}")

    return products

def fetch_excel(products, filename):
    products_dict_list = [product.to_dict() for product in products]
    df = pd.DataFrame(products_dict_list)
    df.to_excel(filename, index=False)
    print(f"Products have been successfully saved to '{filename}'")


def main():
    url = "https://smartstore.naver.com/from_eat/products/5233032940"
    driver = setup_driver()
    products = extract_product_info(driver, url)
    driver.quit()

    # 엑셀 파일로 저장
    fetch_excel(products, "products_info.xlsx")

if __name__ == "__main__":
    main()