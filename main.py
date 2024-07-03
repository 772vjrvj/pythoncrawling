from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os
import pandas as pd

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
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

def fetch_product_info(driver, url):
    driver.get(url)
    time.sleep(30)  # 페이지가 완전히 로드되도록 대기

    product_info = {}

    try:
        product_info['상품명'] = driver.find_element(By.CLASS_NAME, "WBVL_7").text
    except Exception as e:
        product_info['상품명'] = None
        print(f"Error fetching 상품명: {e}")

    try:
        product_info['댓글'] = driver.find_element(By.CLASS_NAME, "F9RHbS").text
    except Exception as e:
        product_info['댓글'] = None
        print(f"Error fetching 댓글: {e}")

    try:
        product_info['판매'] = driver.find_element(By.CLASS_NAME, "AcmPRb").text
    except Exception as e:
        product_info['판매'] = None
        print(f"Error fetching 판매: {e}")

    try:
        product_info['대표이미지'] = driver.find_element(By.CSS_SELECTOR, "img.IMAW1w").get_attribute("src")
    except Exception as e:
        product_info['대표이미지'] = None
        print(f"Error fetching 대표이미지: {e}")

    try:
        product_info['설명'] = driver.find_element(By.CLASS_NAME, "QN2lPu").text
    except Exception as e:
        product_info['설명'] = None
        print(f"Error fetching 설명: {e}")

    return product_info

def main():
    urls = [
        "https://shopee.co.id/thermostat-termostat-Kia-Rio-SF-Carrens-88%C2%B0C-0K2C0-15-171-Ori-i.1009594725.18594798407",
        "https://shopee.co.id/thermostat-thermostart-termostat-kia-sportage-2-82%C2%B0C-25500-23010-i.1009594725.23859582857",
        "https://shopee.co.id/fuel-tank-unit-pelampung-bensin-minyak-kia-pride-Q0K24-060-960A-i.1009594725.21592567358",
        "https://shopee.co.id/actuator-idle-speed-servo-only-getz-verna-matrix-avage-35150-22600-i.1009594725.22447848339",
        "https://shopee.co.id/thermostat-termostat-atoz-1.1cc-visto-1.1cc-82%C2%B0C-25500-02550-i.1009594725.22185071297",
        "https://shopee.co.id/thermostat-termostat-picanto-atoz-1.0cc-visto-1.0cc-82%C2%B0C-25500-02500-i.1009594725.21494781438",
        "https://shopee.co.id/Tie-rod-tierod-kanan-kiri-1set-kia-all-new-rio-grand-avega-original-i.1009594725.21286663932"
    ]

    driver = setup_driver()

    product_info_list = []

    for url in urls:
        product_info = fetch_product_info(driver, url)
        product_info_list.append(product_info)

    driver.quit()

    # 엑셀 파일로 저장
    df = pd.DataFrame(product_info_list)
    df.to_excel("product_info.xlsx", index=False)
    print("엑셀 파일 저장 완료: product_info.xlsx")

if __name__ == "__main__":
    main()
