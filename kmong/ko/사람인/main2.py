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
    try:
        driver.get(url)
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'recruit_container')))
        elements = driver.find_elements(By.CLASS_NAME, 'recruit_container')
        rec_idx_values = [element.get_attribute('data-rec_idx') for element in elements if 'list_link recruit' in element.get_attribute('class')]
        return rec_idx_values
    except Exception as e:
        print(f"Error fetching rec_idx values from {url}: {e}")
        return []

def fetch_job_details(driver, rec_idx):
    job_info = {"회사이름": "", "제목": "", "마감일": "", "급여": "", "지역": "", "직급/직책": "", "근무요일": "", "근무일시": "",
                "필수사항": "", "우대사항": "", "접수방법": "", "접수양식": "", "담당자": "", "전화": "", "휴대폰": "", "사전인터뷰": "",
                "지원금/보험": "", "급여제도": "", "교육/생활": "", "선물": "", "전형절차": "", "제출서류": "",
                "대표자명": "", "기업형태": "", "업종": "", "사원수": "", "설립입": "", "매출액": "", "홈페이지": "", "주소": "",

                "아이디": rec_idx, "URL": f"https://m.saramin.co.kr/job-search/view?rec_idx={rec_idx}"}

    try:
        driver.get(job_info["URL"])
        time.sleep(random.uniform(3, 5))

        company_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'corp_name'))).text.strip()
        subject = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'subject'))).text.strip()

        job_info["회사이름"] = company_name
        job_info["제목"] = subject

        wrap_info_jobs = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'wrap_info_job')))
        details_mapping = [
            ["마감일", "급여", "지역", "직급/직책", "근무요일", "근무일시", "필수사항", "우대사항"],
            ["접수방법", "접수양식", "담당자", "전화", "휴대폰", "사전인터뷰"],
            ["전형절차", "제출서류"],
            ["지원금/보험", "급여제도", "교육/생활", "선물"]
        ]

        for wrap_info_job, details_keys in zip(wrap_info_jobs, details_mapping):
            dt_elements = wrap_info_job.find_elements(By.TAG_NAME, 'dt')
            dd_elements = wrap_info_job.find_elements(By.TAG_NAME, 'dd')
            for dt, dd in zip(dt_elements, dd_elements):
                key = dt.text.strip()
                value = dd.text.strip()
                if key in details_keys:
                    job_info[key] = value


        wrap_corp_info = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'wrap_corp_info')))
        corp_dt_elements = wrap_corp_info.find_elements(By.TAG_NAME, 'dt')
        corp_dd_elements = wrap_corp_info.find_elements(By.TAG_NAME, 'dd')
        corp_details_mapping = ["대표자명", "기업형태", "업종", "사원수", "설립일", "매출액", "홈페이지", "주소"]

        for dt, dd in zip(corp_dt_elements, corp_dd_elements):
            key = dt.text.strip()
            value = dd.text.strip()
            if key in corp_details_mapping:
                job_info[key] = value





    except Exception as e:
        print(f"Error fetching job details for rec_idx {rec_idx}: {e}")

    return job_info

def save_to_excel(data, filename):
    try:
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
    except Exception as e:
        print(f"Error saving to Excel file {filename}: {e}")

def main():
    driver = setup_driver()
    job_details_list = []
    try:
        for kwd in ["팀장"]:
            for page in [1]:
                url = f"https://m.saramin.co.kr/search?searchType=search&searchword={kwd}&cat_mcls=2&exp_cd=2&company_type=scale001%2Cscale002%2Cscale003&is_detail_search=y&list_type=unified&page={page}"
                rec_idx_values = fetch_rec_idx_values(driver, url)
                for index, rec_idx in enumerate(rec_idx_values):
                    if rec_idx >= 2:
                        break
                    job_details = fetch_job_details(driver, rec_idx)
                    job_details_list.append(job_details)
        save_to_excel(job_details_list, 'job_details.xlsx')
    except Exception as e:
        print(f"Error in main process: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
