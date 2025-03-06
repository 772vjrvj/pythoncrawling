from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import time

driver = None

def setup_driver():
    """Selenium WebDriver 설정 및 반환"""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # 최신 headless 모드 사용
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0")

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_mango():
    global driver
    """Mango 웹사이트에서 상품 URL 리스트 추출"""
    driver = setup_driver()
    driver.get("https://shop.mango.com/us/en/c/women/new-now_56b5c5ed")
    time.sleep(5)

    try:
        # Sticky_viewItem__7OMDF 클래스를 가진 요소 찾기 (3개 중 3번째 요소 클릭)
        view_items = driver.find_elements(By.CLASS_NAME, "Sticky_viewItem__7OMDF")
        if len(view_items) >= 3:
            view_items[2].click()
            time.sleep(3)

        # 스크롤을 끝까지 내리기
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 상품 링크 수집
        product_links = []
        grid_container = driver.find_element(By.CLASS_NAME, "Grid_grid__fLhp5.Grid_overview___rpEH")
        items = grid_container.find_elements(By.TAG_NAME, "li")

        for item in items:
            a_tag = item.find_element(By.TAG_NAME, "a")
            href = a_tag.get_attribute("href")
            if href:
                product_links.append(href)

        print("총 수집된 상품 링크 개수:", len(product_links))
        return product_links

    except Exception as e:
        print("에러 발생:", e)
        driver.quit()
        return []


def scrape_product_details(url):
    global driver
    """개별 상품 페이지 크롤링 (Selenium만 사용)"""
    driver.get(url)
    time.sleep(5)  # 페이지 로딩 대기

    product_data = {
        "product_category": None,
        "product_name": None,
        "description": None,
        "composition": [],
    }

    try:
        # product_category 가져오기
        try:
            category_element = driver.find_element(By.CLASS_NAME, "texts_uppercaseS__xdp_M.ProductDetail_tags__Eaooa.Tags_tags__knw43")
            product_data["product_category"] = category_element.text.strip()
        except Exception:
            pass

        # product_name 가져오기
        try:
            name_element = driver.find_element(By.CLASS_NAME, "ProductDetail_title___WrC_.texts_titleL__HgQ5x")
            product_data["product_name"] = name_element.text.strip()
        except Exception:
            pass

        # description 가져오기
        try:
            description_element = driver.find_element(By.ID, "truncate-text")
            paragraphs = description_element.find_elements(By.TAG_NAME, "p")
            product_data["description"] = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
        except Exception:
            pass

        # 이미지 리스트 가져오기
        try:
            image_grid = driver.find_element(By.CLASS_NAME, "ImageGrid_imageGrid__0lrrn")
            img_elements = image_grid.find_elements(By.TAG_NAME, "li")

            for idx, li in enumerate(img_elements[:4]):  # 최대 5개 이미지 수집
                try:
                    img_tag = li.find_element(By.TAG_NAME, "img")
                    srcset = img_tag.get_attribute("srcset")

                    if srcset:
                        first_img_url = srcset.split(",")[0].split(" ")[0]  # srcset에서 첫 번째 이미지 URL 가져오기
                        product_data[f"img_{idx+1}"] = first_img_url
                except Exception:
                    pass
        except Exception:
            pass

        # Composition 클릭
        try:
            comp_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ProductDetail_properties__UStvB.ButtonContentLink_default__oqROh.ButtonContentLink_medium__vKMM6"))
            )
            comp_button.click()
            time.sleep(3)

            # Composition 리스트 수집
            comp_list = driver.find_elements(By.CLASS_NAME, "Composition_list__9lORd")
            for comp in comp_list:
                product_data["composition"].extend([li.text.strip() for li in comp.find_elements(By.TAG_NAME, "li")])

        except Exception:
            pass

    finally:
        driver.quit()

    return product_data


def main():
    # 상품 리스트 가져오기
    product_links = scrape_mango()
    print(product_links)

    # 개별 상품 상세 정보 크롤링
    # product_details_list = ["https://shop.mango.com/us/en/p/women/jackets/leather/suede-leather-jacket_87054804?c=09&l=06", "https://shop.mango.com/us/en/p/women/sweaters-and-cardigans/sweaters/openwork-knitted-polo-neck-sweater_87065767?c=08"]
    product_details_list = []
    for idx, url in enumerate(product_links[:3]):  # 테스트를 위해 상위 3개만 실행
        print(f"크롤링 중: {idx+1}/{len(product_links)} -> {url}")
        details = scrape_product_details(url)
        print(details)
        product_details_list.append(details)

    # 최종 결과 출력
    for product in product_details_list:
        print("\n==============================")
        print(f"카테고리: {product['product_category']}")
        print(f"상품명: {product['product_name']}")
        print(f"설명: {product['description']}")
        print(f"이미지: {product['images']}")
        print(f"구성 요소: {product['composition']}")

if __name__ == "__main__":
    main()
