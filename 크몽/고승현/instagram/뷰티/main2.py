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

    if not driver:
        return

    driver.get("https://www.instagram.com/")
    id = input("로그인이 완료되면 아이디를 입력하세요 : ")

    try:
        url = f"https://www.instagram.com/{id}"
        driver.get(url)
        time.sleep(5)

        # PolarisNavigationIcons 클래스명을 가진 두 번째 div 안의 a 태그 클릭
        try:
            # XPath를 contains로 수정하여 각 클래스를 포함한 div 요소 찾기
            navigation_icons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//*[contains(@class, 'x1iyjqo2') and contains(@class, 'xh8yej3')]")
                )
            )
            # navigation_icons 안의 div 요소들 찾기
            second_div = navigation_icons[0].find_element(By.XPATH, "./div[2]")
            pressable_link = second_div.find_element(By.TAG_NAME, "a")
            pressable_link.click()

            # 검색 input 필드에 'SKINSIDER' 입력
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='입력 검색']"))
            )
            search_input.clear()  # 기존 입력 값이 있을 경우 삭제
            search_input.send_keys("SKINSIDER")

            # 클래스 이름을 가진 div 내부에서 a 태그들을 찾음
            time.sleep(2)
            div_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(@class, 'x9f619') and contains(@class, 'x78zum5') and contains(@class, 'xdt5ytf') and contains(@class, 'x1iyjqo2') and contains(@class, 'x6ikm8r') and contains(@class, 'x1odjw0f') and contains(@class, 'xh8yej3') and contains(@class, 'xocp1fn')]")
                )
            )

            # div 안에 있는 모든 a 태그의 href 속성 추출
            # a 태그들이 로드될 때까지 기다림
            time.sleep(2)
            a_tags = WebDriverWait(div_element, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            hrefs = [a.get_attribute("href") for a in a_tags]
            # href 배열 출력
            print(hrefs)

            # href 배열의 각 값으로 새로운 페이지를 열기
            for href in hrefs:
                driver.get(href)
                print(f"Opened {href}")

                time.sleep(3)  # 페이지가 로드될 시간을 주기 (필요에 따라 조정 가능)

                # user 텍스트 추출
                # user 텍스트 추출 (여러 클래스 이름을 포함하는 요소)
                user = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, 'x1lliihq') and contains(@class, 'x193iq5w') and contains(@class, 'x6ikm8r') and contains(@class, 'x10wlt62') and contains(@class, 'xlyipyv') and contains(@class, 'xuxw1ft')]")
                    )
                ).text

                # 두 번째 follower 텍스트 추출
                follower = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//*[contains(@class, 'xdj266r') and contains(@class, 'x11i5rnm') and contains(@class, 'xat24cr') and contains(@class, 'x1mh8g0r') and contains(@class, 'xexx8yu') and contains(@class, 'x4uap5') and contains(@class, 'x18d9i69') and contains(@class, 'xkhd6sd') and contains(@class, 'x1hl2dhg') and contains(@class, 'x16tdsg8') and contains(@class, 'x1vvkbs')]")
                    )
                )[1].text  # 두 번째 요소 선택

                # content 텍스트 추출
                content = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, '_ap3a') and contains(@class, '_aaco') and contains(@class, '_aacu') and contains(@class, '_aacx') and contains(@class, '_aad7') and contains(@class, '_aade')]")
                    )
                ).text

                # url 텍스트 추출
                url = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, 'x1lliihq') and contains(@class, 'x1plvlek') and contains(@class, 'xryxfnj') and contains(@class, 'x1n2onr6') and contains(@class, 'x1ff1cvt') and contains(@class, 'xatrb82') and contains(@class, 'x193iq5w') and contains(@class, 'xeuugli') and contains(@class, 'x1fj9vlw') and contains(@class, 'x13faqbe') and contains(@class, 'x1vvkbs') and contains(@class, 'x1s928wv') and contains(@class, 'xhkezso') and contains(@class, 'x1gmr53x') and contains(@class, 'x1cpjm7i') and contains(@class, 'x1fgarty') and contains(@class, 'x1943h6x') and contains(@class, 'x1i0vuye') and contains(@class, 'xvs91rp') and contains(@class, 'x1s688f') and contains(@class, 'x7l2uk3') and contains(@class, 'x10wh9bi') and contains(@class, 'x1wdrske') and contains(@class, 'x8viiok') and contains(@class, 'x18hxmgj')]")
                    )
                ).text
                # 데이터 객체 생성
                data = {
                    "user": user,
                    "follower": follower,
                    "content": content,
                    "url": url
                }

                # 객체 출력
                print(data)


        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error finding the second navigation icon or 'a' tag: {e}")

    except Exception as e:
        print("Element not found", e)

    time.sleep(2)
    driver.quit()

# 인스타
if __name__ == "__main__":
    main()
