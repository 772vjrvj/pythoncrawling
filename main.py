import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import os
import pandas as pd

# 드라이버 세팅
def setup_driver():
    try:
        chrome_options = Options()
        user_data_dir = "C:\\Users\\772vj\\AppData\\Local\\Google\\Chrome\\User Data"
        profile = "Default"

        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"profile-directory={profile}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--start-maximized")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        download_dir = os.path.abspath("downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

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
            Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
        '''
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        return driver
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None


def get_links_from_page(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".sm-contents-container-items-item a")
        links = []
        print(f"[get_links_from_page start]=========================================")
        for index, elem in enumerate(elements):
            href = elem.get_attribute('href')
            print(f"index : {index + 1}, href : {href}")
            links.append(href)
        print(f"[get_links_from_page end]=========================================")
        return links
    except NoSuchElementException:
        print("Element not found!")
        return []


def get_hrefs_from_links(driver, links):
    all_hrefs = []
    print("[get_hrefs_from_links start]=========================================")
    total_idx = 0
    for index, link in enumerate(links):
        print(f"index : {index}, link : {link}")
        try:
            driver.get(link)
            time.sleep(2)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "ol")))

            ol_elements = driver.find_elements(By.CSS_SELECTOR, "ol li a")

            for idx, elem in enumerate(ol_elements):
                href = elem.get_attribute('href')
                total_idx += 1
                print(f"    inner index : {idx + 1}, link : {href}")
                print(f"    last total index : {total_idx}")
                all_hrefs.append(href)

        except (NoSuchElementException, TimeoutException):
            print(f"Error processing link: {link}")
            continue
    print("[get_hrefs_from_links end]=========================================")
    return all_hrefs

# 숫자 기호와 해당 숫자 간의 매핑
number_map = {
    '①': '(1)', '②': '(2)', '③': '(3)', '④': '(4)', '⑤': '(5)',
    '⑥': '(6)', '⑦': '(7)', '⑧': '(8)', '⑨': '(9)', '⑩': '(10)'
}

def replace_number_symbols(text):
    for symbol, number in number_map.items():
        text = text.replace(symbol, number)
    return text

def convert_date_format(text):
    return re.sub(r'(\d{4})년\s(\d{2})\s(\d{2})일', r'\1.\2.\3', text)

def extract_final_part(title):
    return title.split(",")[-1].strip()

def replace_brackets(text):
    return text.replace('[', '(').replace(']', ')')

def convert_verse_format(text):
    return re.sub(r'(\D+)\s(\d+):(\d+)', r'\1 \2.\3', text)

def extract_text_from_hrefs(driver, hrefs):
    data_list = []
    for index, href in enumerate(hrefs):
        print(f"extract_text_from_hrefs index : {index + 1}, href : {href}")
        try:
            driver.get(href)
            time.sleep(2)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[style='margin-top: 20px; line-height: 2.4rem;']")))

            div_elem = driver.find_element(By.CSS_SELECTOR, "div[style='margin-top: 20px; line-height: 2.4rem;']")
            span_list = div_elem.find_elements(By.TAG_NAME, "span")

            formatted_text = ""

            ### 마지막 span ###

            # 고전 15:22 / 김남준 목사 / 2011년 01 30일
            last_span = span_list[-1].text
            parts = last_span.split("/")

            # 고전 13:10 -> 고전 13.10
            bible = convert_verse_format(parts[0].strip())

            # 김남준 목사
            Pastor = parts[1].strip()

            # 2011년 01 30일 -> 2011.01.30
            date = convert_date_format(parts[2].strip())



            ### 마지막 전 span ###
            last_span_2 = span_list[-2].text

            # 기호 숫자 변경 ① -> (1) ...
            last_span_2_new = replace_number_symbols(last_span_2)


            if len(span_list) == 3:
                span_1 = replace_brackets(span_list[0].text)
                # [2017 장년교구 여름수련회][경륜이 있는 복음 (장년)]목양 받게 하심 빌 1:10 / 김남준 목사 / 2017년 08 14일"
                # (2017 장년교구 여름수련회)(경륜이 있는 복음 (장년)) 고전 13.10 2011.01.30 , 목양 받게 하심
                if bible:
                    formatted_text = f"{span_1} {bible} {date} , {last_span_2_new}"
                else:
                    formatted_text = f"{span_1} {date} , {last_span_2_new}"

            if len(span_list) == 4:
                span_1 = replace_brackets(span_list[0].text)
                span_2 = replace_brackets(span_list[1].text)
                if bible:
                    formatted_text = f"{span_1}{span_2} {bible} {date} , {last_span_2_new}"
                else:
                    formatted_text = f"{span_1}{span_2} {date} , {last_span_2_new}"

            data = {
                "원제": div_elem.text,
                "제목": formatted_text,
                "성경": parts[0],
                "목사": Pastor,
                "날짜": date,
                "url": href
            }
            print(f"    제목 : {formatted_text}")
            data_list.append(data)
        except (NoSuchElementException, TimeoutException):
            print(f"Error processing href: {href}")
            continue

    return data_list


def wait_for_download(download_dir, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        for file_name in os.listdir(download_dir):
            if file_name.endswith('.crdownload'):
                continue
            if file_name.endswith('.mp3'):
                return file_name
        time.sleep(1)
    return None


def click_title_links(driver, data_list):
    download_dir = os.path.abspath("downloads")
    complete_dir = os.path.join(download_dir, "complete")
    if not os.path.exists(complete_dir):
        os.makedirs(complete_dir)

    for index, data in enumerate(data_list):
        print(f"index : {index + 1}, title : {data['제목']}")
        try:
            driver.get(data["url"])
            time.sleep(2)

            # "음성설교" 텍스트가 포함된 버튼 찾기 (최대 10초 대기)
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '음성설교')]"))
            )
            # 버튼 클릭
            button.click()
            time.sleep(4)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe")))
            # 첫 번째 iframe 요소 찾기
            iframe = driver.find_element(By.XPATH, "//iframe")

            # 첫 번째 iframe으로 전환
            driver.switch_to.frame(iframe)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "title__h2")))

            a_elem = driver.find_element(By.CLASS_NAME, "title__h2")

            href = a_elem.get_attribute('href')

            print(f"href : {href}")

            if href:
                driver.get(href)
                time.sleep(3)
                sc_button_more = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="More"]')))
                sc_button_more.click()

                time.sleep(1)
                download_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Download this track"]')
                download_button.click()

                downloaded_file_name = wait_for_download(download_dir, timeout=60)
                if downloaded_file_name:
                    old_file_path = os.path.join(download_dir, downloaded_file_name)
                    new_file_path = os.path.join(download_dir, f"{data['제목']}.mp3")
                    os.rename(old_file_path, new_file_path)
                    final_path = os.path.join(complete_dir, f"{data['제목']}.mp3")
                    os.rename(new_file_path, final_path)
                    print(f"Download complete and file moved to {final_path}")
                else:
                    print("Download failed or timed out. ")

            else:
                print(f"No href found for the specified a tag in {data['url']}")

            driver.switch_to.default_content()

        except (NoSuchElementException, TimeoutException):
            print(f"Could not find the specified a tag in {data['url']}")
            continue


def save_data_list_to_excel(data_list, filename="data_list.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)


def main():
    driver = setup_driver()
    if driver is not None:
        url = "https://www.eltechkorea.com:444/knj/Sermon/Index"
        driver.get(url)
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "sm-contents-container-items-item")))

        # 전체 페이지 목록 리스트
        links = get_links_from_page(driver)
        print(f">>>>> Total links: {len(links)}")

        # 리스트 안에 새부 리스트 포함
        all_hrefs = get_hrefs_from_links(driver, links)
        print(f">>>>> Total all_hrefs: {len(all_hrefs)}")

        data_list = extract_text_from_hrefs(driver, all_hrefs)
        print(f">>>>> Total data_list: {len(data_list)}")

        # 엑셀로 data_list 저장
        save_data_list_to_excel(data_list)

        # 엑셀 파일에서 data_list 불러오기
        data_list = pd.read_excel("data_list.xlsx").to_dict(orient='records')

        # 음원 다운로드
        click_title_links(driver, data_list)
        driver.quit()


if __name__ == "__main__":
    main()
