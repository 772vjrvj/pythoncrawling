import os
import time

import pandas as pd
import psutil
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

from selenium import webdriver


def close_chrome_processes():
    """모든 Chrome 프로세스를 종료합니다."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def setup_driver():
    try:
        close_chrome_processes()
        chrome_options = Options()
        user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
        profile = "Default"

        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"profile-directory={profile}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        download_dir = os.path.abspath("downloads")
        os.makedirs(download_dir, exist_ok=True)
        chrome_options.add_experimental_option('prefs', {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        script = '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        '''
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        return driver
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None

def extract_data_from_elements(driver, collected_urls):
    """셀레니움을 활용하여 데이터 추출"""
    result = []

    try:
        # 부모 div 내의 모든 추가된 div 가져오기
        new_divs = driver.find_elements(By.CSS_SELECTOR, "div.xrvj5dj.xd0jker.x1evr45z")

        for new_div in new_divs:

            # 데이터 추출 객체 초기화
            obj = {
                "글본문": "",
                "좋아요": "",
                "url": "",
                "날짜": ""
            }

            try:
                # 각 div의 고유 URL로 중복 검사
                url_element = None
                full_url = ""

                try:
                    url_element = new_div.find_element(By.XPATH, ".//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1lku1pv x12rw4y6 xrkepyr x1citr7e x37wo2f']")
                    full_url = f"{url_element.get_attribute('href')}"
                    obj["url"] = full_url
                except NoSuchElementException:
                    obj["url"] = ""

                # 날짜 추출
                try:
                    date_element = url_element.find_element(By.TAG_NAME, "time")
                    obj["날짜"] = date_element.get_attribute("title")
                except NoSuchElementException:
                    obj["날짜"] = ""


                if full_url in collected_urls:
                    continue  # 이미 수집된 URL이면 무시

                collected_urls.add(full_url)  # 새로운 URL 추가

                # 글본문 추출
                try:
                    text_element = new_div.find_element(By.CSS_SELECTOR, "div.x1a6qonq.x6ikm8r.x10wlt62.xj0a0fe.x126k92a.x6prxxf.x7r5mf7")
                    obj["글본문"] = text_element.text.strip()
                except NoSuchElementException:
                    obj["글본문"] = ""

                # 좋아요 추출 (정확한 클래스 이름을 지정해야 함)
                try:
                    # svg 태그를 기준으로 aria-label="좋아요" 속성을 가진 태그 찾기
                    like_divs = new_div.find_elements(By.CSS_SELECTOR, "div.x6s0dn4.x78zum5.xl56j7k.xezivpi")

                    # svg 태그의 바로 옆 형제 span 태그를 찾기
                    like_count = like_divs[0].find_element(By.CSS_SELECTOR, "span.x17qophe.x10l6tqk.x13vifvy")

                    # 좋아요 수 가져오기
                    obj["좋아요"] = like_count.text.strip()

                except NoSuchElementException:
                    obj["좋아요"] = "0"


                print(f'날짜 : {obj["날짜"]}')
                print(f'url : {obj["url"]}')
                print(f'글본문 : {obj["글본문"]}')
                print(f'좋아요 : {obj["좋아요"]}')
                result.append(obj)
                print(f'===============================')

            except Exception as e:
                print(f"오류 발생 (각 new_div 처리 중): {e}")

    except NoSuchElementException:
        print("필요한 요소를 찾을 수 없습니다. 부모 div가 존재하지 않음.")

    except Exception as e:
        print(f"오류 발생 (전체 처리 중): {e}")

    return result


def scroll_and_collect_data(driver, url, wait_time=3, target_data_count=None):
    driver.get(url)
    time.sleep(wait_time)  # 페이지 로딩 대기

    collected_data = []
    collected_urls = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 새 데이터 추출
        new_data = extract_data_from_elements(driver, collected_urls)
        collected_data.extend(new_data)

        # 데이터 개수 기준으로 종료
        if target_data_count and len(collected_data) >= target_data_count:
            print(f"목표 데이터 개수 {target_data_count}에 도달했습니다.")
            break

        # 스크롤 실행
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 스크롤 높이 변경 여부 확인
        for _ in range(5):  # 5초 동안 반복 체크
            time.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height > last_height:
                last_height = new_height
                break
        else:
            print("더 이상 스크롤할 수 없습니다.")
            break

        # 로드 대기
        time.sleep(wait_time)

    return collected_data


def save_to_excel(data, output_file):
    """데이터를 엑셀 파일로 저장"""
    try:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"데이터가 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"엑셀 저장 중 오류 발생: {e}")

def main():
    url = "https://www.threads.net/@lecor.creator?igshid=NTc4MTIwNjQ2YQ%3D%3D"
    output_file = "extracted_data.xlsx"

    driver = setup_driver()
    if driver is None:
        print("드라이버 설정 실패")
        return

    try:
        collected_data = scroll_and_collect_data(driver, url)
        if collected_data:
            save_to_excel(collected_data, output_file)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
