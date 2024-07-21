import json
import pandas as pd
import math
import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

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



def main():

    driver = setup_driver()

    driver.get("https://www.instagram.com/")

    id = input("로그인이 완료되면 아이디를 입력하세요 : ")

    try:
        url = f"https://www.instagram.com/{id}"
        driver.get(url)
        time.sleep(5)
        follower_link = driver.find_element(By.XPATH, "//a[contains(text(), '팔로우')]")
        follower_link.click()

        time.sleep(2)
        # 대상 div 요소 찾기
        target_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6"))
        )

        # 대상 div 요소로 마우스 이동
        actions = ActionChains(driver)
        actions.move_to_element(target_div).perform()

        # 대상 div 요소 안에서 스크롤
        scroll_pause_time = 3  # 스크롤 후 대기 시간
        last_height = driver.execute_script("return arguments[0].scrollHeight", target_div)

        while True:
            # 대상 div 요소 끝까지 스크롤
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", target_div)

            # 새 데이터 로딩 대기
            time.sleep(scroll_pause_time)

            # 새로운 높이 계산
            new_height = driver.execute_script("return arguments[0].scrollHeight", target_div)

            # 새로운 데이터가 로드되지 않았으면 스크롤 종료
            if new_height == last_height:
                break

            last_height = new_height

        # 특정 클래스의 텍스트를 배열에 담기
        texts = []
        elements = driver.find_elements(By.CSS_SELECTOR, "._ap3a._aaco._aacw._aacx._aad7._aade")
        for element in elements:
            texts.append(element.text)

        # 결과 출력
        print(texts)

    except Exception as e:
        print("Element not found", e)

    time.sleep(2)
    driver.quit()

# 인스타
if __name__ == "__main__":
    main()

