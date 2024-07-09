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
# 크롬 브라우저에  chrome://version를 입력해서 정보를 가져온다.
# 구글 로그인은 보안이 까다로우므로 실제 브라우저로 해야한다.
# 이 경우 다른 크롬 창은 띄우지 말고 작업해야 한다.
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
        links = [elem.get_attribute('href') for elem in elements]
        return links
    except NoSuchElementException:
        print("Element not found!")
        return []


def get_hrefs_from_links(driver, links):
    all_hrefs = []
    for index, link in enumerate(links):
        print(f"link : {link}")
        if index == 1:  # Example limit for demonstration
            break
        try:
            driver.get(link)
            time.sleep(2)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "ol")))

            ol_elements = driver.find_elements(By.CSS_SELECTOR, "ol li a")
            hrefs = [elem.get_attribute('href') for elem in ol_elements]
            all_hrefs.extend(hrefs)
        except (NoSuchElementException, TimeoutException):
            print(f"Error processing link: {link}")
            continue

    return all_hrefs


def format_title(title):
    match = re.match(r'\[(.*?)\]\n(.*?)\n(.*?) / .*? / (.*?)년 (.*?) (.*?)일', title)
    if match:
        new_title = f"({match.group(1)}) {match.group(3).replace(':', '.')} {match.group(4)}.{match.group(5)}.{match.group(6)} , {match.group(2)}"
        return new_title
    else:
        return title


def extract_final_part(title):
    return title.split(",")[-1].strip()



def extract_text_from_hrefs(driver, hrefs):
    data_list = []
    for href in hrefs:
        try:
            driver.get(href)
            time.sleep(2)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[style='margin-top: 20px; line-height: 2.4rem;']")))

            div_elem = driver.find_element(By.CSS_SELECTOR, "div[style='margin-top: 20px; line-height: 2.4rem;']")
            text = div_elem.text
            formatted_text = format_title(text)

            data = {
                "원제": text,
                "제목": formatted_text,
                "url": href
            }
            print(f"제목 : {formatted_text}")
            data_list.append(data)
        except (NoSuchElementException, TimeoutException):
            print(f"Error processing href: {href}")
            continue

    return data_list


def wait_for_download(download_dir, target_text, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        for file_name in os.listdir(download_dir):
            if file_name.endswith('.crdownload'):
                continue
            if file_name.endswith('.mp3') and target_text in file_name:
                return file_name
        time.sleep(1)
    return None



def click_title_links(driver, data_list):
    download_dir = os.path.abspath("downloads")
    complete_dir = os.path.join(download_dir, "complete")
    if not os.path.exists(complete_dir):
        os.makedirs(complete_dir)

    for index, data in enumerate(data_list):
        print(f"index : {index}, title : {data['제목']}")
        try:
            driver.get(data["url"])
            time.sleep(2)

            WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "title__h2")))

            a_elem = driver.find_element(By.CLASS_NAME, "title__h2")
            href = a_elem.get_attribute('href')
            if href:
                driver.get(href)
                time.sleep(3)
                sc_button_more = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="More"]')))
                sc_button_more.click()

                time.sleep(1)
                download_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Download this track"]')
                download_button.click()

                target_text = extract_final_part(data['제목'])

                downloaded_file_name = wait_for_download(download_dir, target_text, timeout=60)
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

        links = get_links_from_page(driver)
        all_hrefs = get_hrefs_from_links(driver, links)
        data_list = extract_text_from_hrefs(driver, all_hrefs)

        print(f"Total hrefs: {len(all_hrefs)}")

        # 엑셀로 data_list 저장
        save_data_list_to_excel(data_list)

        # 엑셀 파일에서 data_list 불러오기
        data_list = pd.read_excel("data_list.xlsx").to_dict(orient='records')

        click_title_links(driver, data_list)
        driver.quit()


def get_data_list():
    return [
        {'제목': '(가나안 여인을 만나주신 예수님) 마 15.26~28 1994.03.02 , 네 믿음이 크도다', 'url': 'https://www.eltechkorea.com:444/knj/Sermon/SermonView?params=10797'},
        {'제목': '(가나안 여인을 만나주신 예수님) 마 15.23~25 1994.02.23 , 도와 주소서', 'url': 'https://www.eltechkorea.com:444/knj/Sermon/SermonView?params=10796'},
        {'제목': '(가나안 여인을 만나주신 예수님) 마 15.21~22 1994.02.16 , 불쌍히 여기소서', 'url': 'https://www.eltechkorea.com:444/knj/Sermon/SermonView?params=10795'}
    ]




if __name__ == "__main__":
    main()



