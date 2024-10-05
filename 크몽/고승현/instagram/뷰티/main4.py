import pandas as pd
import re
import time

import pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver


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

def save_to_excel(results, output_file='instagram_search_results.xlsx'):
    # 기존 엑셀 파일이 있으면 그 내용을 불러와서 이어서 저장
    try:
        df_existing = pd.read_excel(output_file)
        df_results = pd.DataFrame(results)
        df_combined = pd.concat([df_existing, df_results], ignore_index=True)
    except FileNotFoundError:
        # 기존 파일이 없으면 바로 새로운 데이터 저장
        df_combined = pd.DataFrame(results)

    df_combined.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")

def remove_non_bmp_characters(text):
    # BMP 범위 내의 문자(알파벳, 숫자, 공백 포함)만 남기고 나머지는 제거
    cleaned_text = ''.join(c for c in text if ord(c) <= 0xFFFF)

    # 이모지 및 특수 문자를 제거하고 알파벳, 숫자, 공백만 남김
    # cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned_text)

    return cleaned_text


def main():
    driver = setup_driver()

    if not driver:
        return

    driver.get("https://www.instagram.com/")
    id = input("로그인이 완료되면 아이디를 입력하세요 : ")

    # 아이디로 프로필 페이지로 이동
    try:
        url = f"https://www.instagram.com/{id}"
        driver.get(url)
        time.sleep(5)
    except Exception as e:
        print(f"Failed to load user profile: {e}")
        driver.quit()
        return

    results = []  # 상위 리스트 생성
    output_file = 'instagram_search_results.xlsx'  # 엑셀 파일 경로

    # 엑셀 파일에서 데이터 읽어들이기
    input_file = 'instagram_hashtag.xlsx'
    df = pd.read_excel(input_file)

    # Usernames와 Hashtag 데이터를 리스트로 추출
    usernames = df['Usernames'].tolist()
    hashtags = df['Hashtag'].tolist()

    # 각 keyword에 대해 검색 처리
    for i, keyword in enumerate(usernames):
        cleaned_keyword = remove_non_bmp_characters(keyword)  # 이모지와 같은 BMP 밖의 문자 제거
        print(f"Searching for keyword: {cleaned_keyword}===============")

        # PolarisNavigationIcons 클래스명을 가진 두 번째 div 안의 a 태그 클릭
        try:
            navigation_icons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//*[contains(@class, 'x1iyjqo2') and contains(@class, 'xh8yej3')]")
                )
            )
            second_div = navigation_icons[0].find_element(By.XPATH, "./div[2]")
            pressable_link = second_div.find_element(By.TAG_NAME, "a")
            pressable_link.click()
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error finding the second navigation icon or 'a' tag: {e}")
            continue

        # 검색 input 필드에 keyword 입력
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='입력 검색']"))
            )
            search_input.clear()
            search_input.send_keys(cleaned_keyword)
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error finding search input: {e}")
            continue

        # div 내부의 모든 a 태그의 href 속성 추출
        try:
            time.sleep(2)
            div_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(@class, 'x9f619') and contains(@class, 'x78zum5') and contains(@class, 'xdt5ytf') and contains(@class, 'x1iyjqo2') and contains(@class, 'x6ikm8r') and contains(@class, 'x1odjw0f') and contains(@class, 'xh8yej3') and contains(@class, 'xocp1fn')]")
                )
            )
            time.sleep(2)
            a_tags = WebDriverWait(div_element, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            hrefs = [a.get_attribute("href") for a in a_tags]
            print(hrefs)
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error finding a tags: {e}")
            continue

        # href 배열의 각 값으로 새로운 페이지를 열기 (상위 10개의 href만 처리)
        for href in hrefs[:10]:
            driver.get(href)
            print(f"Opened {href}")
            time.sleep(3)  # 페이지가 로드될 시간을 주기 (필요에 따라 조정 가능)

            # element_to_click가 없을 경우 예외 처리 추가
            try:
                element_to_click = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, 'x1lliihq') and contains(@class, 'x1plvlek') and contains(@class, 'xryxfnj') and contains(@class, 'x1n2onr6') and contains(@class, 'x1ff1cvt') and contains(@class, 'xatrb82') and contains(@class, 'x193iq5w') and contains(@class, 'xeuugli') and contains(@class, 'x1fj9vlw') and contains(@class, 'x13faqbe') and contains(@class, 'x1vvkbs') and contains(@class, 'x1s928wv') and contains(@class, 'xhkezso') and contains(@class, 'x1gmr53x') and contains(@class, 'x1cpjm7i') and contains(@class, 'x1fgarty') and contains(@class, 'x1943h6x') and contains(@class, 'x1i0vuye') and contains(@class, 'xvs91rp') and contains(@class, 'xo1l8bm') and contains(@class, 'x1roi4f4') and contains(@class, 'x1yc453h') and contains(@class, 'x10wh9bi') and contains(@class, 'x1wdrske') and contains(@class, 'x8viiok') and contains(@class, 'x18hxmgj')]")
                    )
                )
                element_to_click.click()
            except (NoSuchElementException, TimeoutException):
                print("Element to click not found, continuing without clicking.")

            # user 텍스트 추출
            try:
                user = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, 'x1lliihq') and contains(@class, 'x193iq5w') and contains(@class, 'x6ikm8r') and contains(@class, 'x10wlt62') and contains(@class, 'xlyipyv') and contains(@class, 'xuxw1ft')]")
                    )
                ).text
            except (NoSuchElementException, TimeoutException):
                user = ""
                print("User not found.")

            # 두 번째 follower 텍스트 추출
            try:
                follower = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//*[contains(@class, 'xdj266r') and contains(@class, 'x11i5rnm') and contains(@class, 'xat24cr') and contains(@class, 'x1mh8g0r') and contains(@class, 'xexx8yu') and contains(@class, 'x4uap5') and contains(@class, 'x18d9i69') and contains(@class, 'xkhd6sd') and contains(@class, 'x1hl2dhg') and contains(@class, 'x16tdsg8') and contains(@class, 'x1vvkbs')]")
                    )
                )[1].text
            except (NoSuchElementException, TimeoutException, IndexError):
                follower = ""
                print("Follower not found.")

            # content 텍스트 추출
            try:
                content = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, '_ap3a') and contains(@class, '_aaco') and contains(@class, '_aacu') and contains(@class, '_aacx') and contains(@class, '_aad7') and contains(@class, '_aade')]")
                    )
                ).text
            except (NoSuchElementException, TimeoutException):
                content = ""
                print("Content not found.")

            # url 텍스트 추출
            try:
                url = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(@class, 'x1lliihq') and contains(@class, 'x1plvlek') and contains(@class, 'xryxfnj') and contains(@class, 'x1n2onr6') and contains(@class, 'x1ff1cvt') and contains(@class, 'xatrb82') and contains(@class, 'x193iq5w') and contains(@class, 'xeuugli') and contains(@class, 'x1fj9vlw') and contains(@class, 'x13faqbe') and contains(@class, 'x1vvkbs') and contains(@class, 'x1s928wv') and contains(@class, 'xhkezso') and contains(@class, 'x1gmr53x') and contains(@class, 'x1cpjm7i') and contains(@class, 'x1fgarty') and contains(@class, 'x1943h6x') and contains(@class, 'x1i0vuye') and contains(@class, 'xvs91rp') and contains(@class, 'x1s688f') and contains(@class, 'x7l2uk3') and contains(@class, 'x10wh9bi') and contains(@class, 'x1wdrske') and contains(@class, 'x8viiok') and contains(@class, 'x18hxmgj')]")
                    )
                ).text
            except (NoSuchElementException, TimeoutException):
                url = ""
                print("URL not found.")

            # 데이터 객체 생성
            data = {
                "user": user,
                "follower": follower,
                "content": f'{content}\n{url}',  # content와 url을 합쳐서 저장
                "search": keyword,
                "hashtag": hashtags[i]
            }

            # 객체 출력
            print(data)

            # 중복 확인 후 리스트에 추가 (객체 전체가 동일해야 추가되지 않음)
            if not any(d == data for d in results):
                results.append(data)
                print(f'results 갯수 {len(results)}')

        # 한 번의 검색이 끝날 때마다 저장
        save_to_excel(results, output_file)

    print("모든 검색이 완료되었습니다.")
    driver.quit()

# 인스타
if __name__ == "__main__":
    main()
