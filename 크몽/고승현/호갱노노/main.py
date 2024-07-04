import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
import time



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
    details_mapping = [
        ["지역", "아파트명", "평수", "매매가", "전세가", "갭", "전세가율"],
        ["전고점", "전고점 대비", "세대수", "연식"]
    ]
    datas = []

    try:
                # maplist 요소들을 기다림
        maplist = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cluster')))
        
        for index, map in enumerate(maplist):
            try:
                loca = map.text.split('\n')[0]  # 지역
                map.click()  # map 클릭
                time.sleep(3)
                
                # real 요소들을 찾아서 클릭
                realList = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'diff-price')))
                
                for real in realList:
                    try:
                        real.click()
                        time.sleep(3)
                        
                        # 세부 정보 수집
                        area = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'areaSelector'))).text.strip()  # 평수
                        aptDetail = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'header-info'))).text.strip().split('\n')[0]  # 아파트명
                        price = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'price-group'))).text.strip().split('\n')[1]  # 매매가
                        card = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'card'))).text.strip()
                        age = card.split('\n')[1]  # 연식
                        cnt = card.split('\n')[0]  # 세대수
                        high = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
                        beforehigh = high[2].text.split('\n')[1]  # 전고점
                        
                        # 갭 = 매매가 - 전세가
                        time.sleep(3)
                        
                        datas.append([loca, aptDetail, area, price, "갭", "전세가율", beforehigh, "전고점대비", cnt, age])
                    
                    except StaleElementReferenceException as e:
                        print(f"StaleElementReferenceException 발생: {e}")
                        continue
            
            except StaleElementReferenceException as e:
                print(f"StaleElementReferenceException 발생: {e}")
                continue
        
    except Exception as e:
        maplist = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cluster')))
        print(f"에러 발생: {e}")

    finally:
        # 웹 드라이버 종료
        driver.quit()


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
        for kwd in ["서울특별시 동작구"]:
            url = f"https://hogangnono.com/region/11590/0"
            rec_idx_values = fetch_rec_idx_values(driver, url)
                
        # save_to_excel(job_details_list, 'job_details.xlsx')
    except Exception as e:
        print(f"Error in main process: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
