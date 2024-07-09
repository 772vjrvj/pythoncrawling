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
                "제목": formatted_text,
                "url": href
            }
            data_list.append(data)
        except (NoSuchElementException, TimeoutException):
            print(f"Error processing href: {href}")
            continue

    return data_list


def click_title_links(driver, data_list):
    for data in data_list:
        try:

            driver.get(data["url"])
            time.sleep(2)

            # 아이프레임으로 전환
            WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))

            # 아이프레임 내부의 a 태그를 찾음
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "title__h2")))

            a_elem = driver.find_element(By.CLASS_NAME, "title__h2")
            href = a_elem.get_attribute('href')
            if href:
                driver.get(href)
                time.sleep(2)  # 페이지 로드 대기

                accept = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler")))
                accept.click()

                time.sleep(20)  # 페이지 로드 대기

            else:
                print(f"No href found for the specified a tag in {data['url']}")

            # 아이프레임에서 메인 컨텐츠로 돌아옴
            driver.switch_to.default_content()
        except (NoSuchElementException, TimeoutException):
            print(f"Could not find the specified a tag in {data['url']}")
            continue



def main():
    driver = setup_driver()
    if driver is not None:
        # url = "https://www.eltechkorea.com:444/knj/Sermon/Index"
        # driver.get(url)
        # time.sleep(2)
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "sm-contents-container-items-item")))
        #
        # links = get_links_from_page(driver)
        # all_hrefs = get_hrefs_from_links(driver, links)
        # data_list = extract_text_from_hrefs(driver, all_hrefs)
        #
        # print(f"Total hrefs: {len(all_hrefs)}")
        # # 수집된 데이터 출력
        # for data in data_list:
        #     print(data)

        data_list = [{'제목': '(가나안 여인을 만나주신 예수님) 마 15.26~28 1994.03.02 , 네 믿음이 크도다', 'url': 'https://www.eltechkorea.com:444/knj/Sermon/SermonView?params=10797'},
        {'제목': '(가나안 여인을 만나주신 예수님) 마 15.23~25 1994.02.23 , 도와 주소서', 'url': 'https://www.eltechkorea.com:444/knj/Sermon/SermonView?params=10796'},
        {'제목': '(가나안 여인을 만나주신 예수님) 마 15.21~22 1994.02.16 , 불쌍히 여기소서', 'url': 'https://www.eltechkorea.com:444/knj/Sermon/SermonView?params=10795'}
         ]

        click_title_links(driver, data_list)
        driver.quit()

if __name__ == "__main__":
    main()
