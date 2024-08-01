import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")  # Use incognito mode

    # Set user-agent to mimic a regular browser
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Bypass the detection of automated software
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    return driver

def get_search_results(driver, q):
    url = f"https://www.teamblind.com/kr/search/{q}"
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    urls = set()

    while True:
        try:
            articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'article-list-pre')))
            for article in articles:
                a_tag = article.find_element(By.CLASS_NAME, 'tit').find_element(By.TAG_NAME, 'a')
                if a_tag:
                    full_url = a_tag.get_attribute('href')
                    urls.add(full_url)
                    print(f" URL: {full_url}")

            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(3)  # 페이지가 로드되는 시간을 기다림
            new_articles = driver.find_elements(By.CLASS_NAME, 'article-list-pre')
            if len(new_articles) == len(articles):
                break  # 더 이상 새로운 글이 없으면 종료
        except Exception as e:
            print(f"Error fetching search results: {e}")
            break

    return list(urls)

def get_post_details(driver, url, index):
    print(f"[{index}] Fetching details from {url}")
    driver.get(url)
    obj = {}
    try:
        obj['사이트'] = "블라인드"
        obj['URL'] = url
        obj['제목'] = driver.find_element(By.CSS_SELECTOR, '.article-view-head h2').text.strip()
        obj['원문'] = driver.find_element(By.ID, 'contentArea').text.strip()
        obj['날짜'] = driver.find_element(By.CLASS_NAME, 'date').get_attribute('textContent').strip().replace('작성일', '').strip()

    except Exception as e:
        print(f"Error parsing post details from {url}: {e}")
        return None

    print(f"[{index}] obj: {obj}")
    return obj

def save_to_excel(data, file_name='teamblind_results.xlsx'):
    try:
        if os.path.exists(file_name):
            existing_df = pd.read_excel(file_name)
            combined_df = pd.concat([existing_df, pd.DataFrame(data)], ignore_index=True)
        else:
            combined_df = pd.DataFrame(data)

        with pd.ExcelWriter(file_name, engine='openpyxl', mode='w') as writer:
            combined_df.to_excel(writer, index=False)
        print(f"Data successfully saved to {file_name}")

    except Exception as e:
        print(f"Error saving to Excel: {e}")

def main(q):
    driver = setup_driver()
    all_results = []
    post_index = 1
    search_results = get_search_results(driver, q)
    for url in search_results:
        time.sleep(random.uniform(1, 2))  # 1~2초 사이의 랜덤 간격
        post_details = get_post_details(driver, url, post_index)
        if post_details:
            all_results.append(post_details)
            post_index += 1
            if len(all_results) >= 100:
                save_to_excel(all_results)
                all_results = []

    if all_results:
        save_to_excel(all_results)

    driver.quit()

if __name__ == "__main__":
    query = "사이버대학"  # 원하는 검색어로 바꿔주세요
    main(query)
