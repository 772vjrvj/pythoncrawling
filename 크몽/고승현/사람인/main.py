import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import random

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

def fetch_rec_idx_values(driver, url):
    driver.get(url)

    time.sleep(2)
    # 요소가 로드될 때까지 대기
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'recruit_container'))
    )

    # class가 'recruit_container list_link recruit'인 요소들 찾기
    elements = driver.find_elements(By.CLASS_NAME, 'recruit_container')

    # data-rec_idx 값 추출
    rec_idx_values = [element.get_attribute('data-rec_idx') for element in elements if 'list_link recruit' in element.get_attribute('class')]

    return rec_idx_values

def fetch_job_details(driver, rec_idx):
    url = f"https://m.saramin.co.kr/job-search/view?rec_idx={rec_idx}"
    driver.get(url)

    time.sleep(random.uniform(3, 5))

    # 회사 이름과 제목 추출
    company_name = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'corp_name'))
    ).text.strip()

    subject = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'subject'))
    ).text.strip()

    # 요소가 로드될 때까지 대기
    first_wrap_info_job = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'wrap_info_job'))
    )

    job_info = {
        "회사이름": company_name,
        "제목": subject
    }
    dt_elements = first_wrap_info_job.find_elements(By.TAG_NAME, 'dt')
    dd_elements = first_wrap_info_job.find_elements(By.TAG_NAME, 'dd')

    for dt, dd in zip(dt_elements, dd_elements):
        key = dt.text.strip()
        value = dd.text.strip()
        if key in ["마감일", "급여", "지역", "직급/직책", "근무요일", "근무일시", "필수사항", "우대사항"]:
            job_info[key] = value

    job_info["아이디"] = rec_idx
    job_info["URL"] = url

    return job_info

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

def main():
    url = "https://m.saramin.co.kr/search?searchType=search&searchword=%ED%8C%80%EC%9E%A5&cat_mcls=2&exp_cd=2&company_type=scale001%2Cscale002%2Cscale003&is_detail_search=y&list_type=unified&page=1"
    driver = setup_driver()

    try:
        rec_idx_values = fetch_rec_idx_values(driver, url)
        job_details_list = []

        for index, rec_idx in enumerate(rec_idx_values):
            if index >= 30:
                break
            try:
                job_details = fetch_job_details(driver, rec_idx)
                job_details_list.append(job_details)
            except Exception as e:
                print(f"Error fetching details for rec_idx {rec_idx}: {e}")

        # Print job details list
        print(job_details_list)

        # Save to Excel
        save_to_excel(job_details_list, 'job_details.xlsx')

    except Exception as e:
        print(f"Error fetching rec_idx values: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
