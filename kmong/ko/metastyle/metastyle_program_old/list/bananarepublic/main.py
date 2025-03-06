from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from webdriver_manager.chrome import ChromeDriverManager

# 🔹 Chrome WebDriver 설정
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


# 🔹 페이지 이동
def go_to_page(driver, page_id, base_url):
    url = f"{base_url}{page_id}"
    driver.get(url)
    time.sleep(3)  # 페이지 로딩 대기

# 🔹 <svg data-testid="large-grid-icon"> 클릭
def click_grid_icon(driver):
    try:
        grid_icon = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "svg[data-testid='large-grid-icon']"))
        )
        grid_icon.click()
        time.sleep(2)  # 클릭 후 대기
    except Exception:
        print("Grid icon not found or already selected.")

# 🔹 스크롤을 끝까지 내리기
def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 스크롤 후 대기
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# 🔹 제품 링크 추출
def extract_product_links(driver):
    product_links = []
    products = driver.find_elements(By.CLASS_NAME, "cat_product-image.sitewide-mvez9e")

    for product in products:
        try:
            link = product.find_element(By.TAG_NAME, "a").get_attribute("href")
            product_links.append(link)
        except Exception:
            continue

    return product_links

# 🔹 메인 실행 함수
def main():
    driver = setup_driver()
    base_url = "https://bananarepublic.gap.com/browse/women/new-arrivals?cid=48422&nav=meganav%3AWomen%3ADiscover%3ANew%20Arrivals#pageId="
    page_id = 0

    while True:
        go_to_page(driver, page_id, base_url)
        click_grid_icon(driver)
        scroll_to_bottom(driver)

        product_links = extract_product_links(driver)
        print(f"Page {page_id} Links:", product_links)

        # 다음 페이지로 이동
        page_id += 1

        # 데이터가 없으면 종료
        if len(product_links) == 0:
            print(f"Page {page_id} has no products. Stopping.")
            break

    driver.quit()

# 🔹 실행
if __name__ == "__main__":
    main()
