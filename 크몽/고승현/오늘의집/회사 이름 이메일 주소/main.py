import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

def fetch_search_results(kwd, page):
    url = f"https://ohou.se/productions/feed.json?v=7&type=store&query={kwd}&page={page}&per=20"
    headers = {
        'authority': 'ohou.se',
        'method': 'GET',
        'path': f'/productions/feed.json?v=7&type=store&query={kwd}&page={page}&per=20',
        'scheme': 'https',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'If-None-Match': 'W/"45a142fe1a5df378810859e6665519dc"',
        'Priority': 'u=0, i',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }

    # 세션 생성
    session = requests.Session()

    # Retry 설정
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # UTF-8로 인코딩된 헤더 설정
    headers = {k: str(v).encode('utf-8') for k, v in headers.items()}

    try:
        response = session.get(url, headers=headers, timeout=10)  # 타임아웃 설정
        response.raise_for_status()  # 요청이 성공하지 못하면 예외를 발생시킵니다
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except requests.exceptions.ConnectionError as err:
        print(f"Error connecting: {err}")
    except requests.exceptions.Timeout as err:
        print(f"Timeout error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")

def parse_results(results):
    ids = []
    items = results.get('productions', [])
    for item in items:
        id_value = item.get('id')
        if id_value:
            ids.append(id_value)
    return ids

def click_fourth_tab(driver, product_id):
    time.sleep(2)  # 각 요청 사이에 잠시 대기
    url = f"https://ohou.se/productions/{product_id}/selling"
    driver.get(url)
    print(f"product_id : {product_id}")
    print(f"url : {url}")

    seller_info = {"상호": "", "e-mail": ""}

    try:
        # class "production-selling-navigation__list"를 찾아서 4번째 li 태그 클릭
        nav_list = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'production-selling-navigation__list'))
        )
        li_elements = nav_list.find_elements(By.TAG_NAME, 'li')
        if len(li_elements) >= 4:
            li_elements[3].click()
        else:
            print("li 태그가 4개 이상 존재하지 않습니다.")
            return seller_info

        time.sleep(3)  # 네비게이션 후 페이지 로딩 시간 추가

        # 모든 테이블 찾기
        tables = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'production-selling-table'))
        )

        print(f"len(tables): {len(tables)}")

        if len(tables) >= 4:
            table = tables[3]  # 네 번째 테이블 선택

            # th의 text가 "상호"인 것의 td text 찾기
            th_elements = table.find_elements(By.TAG_NAME, 'th')
            for th in th_elements:
                if '상호' in th.text:
                    td = th.find_element(By.XPATH, './following-sibling::td')
                    seller_info['상호'] = td.text
                    break

            # th의 text가 'E-mail'를 포함하는 것의 td text 찾기
            for th in th_elements:
                if 'E-mail' in th.text:
                    td = th.find_element(By.XPATH, './following-sibling::td')
                    seller_info['e-mail'] = td.text
                    break
        else:
            print("production-selling-table 테이블이 4개 이상 존재하지 않습니다.")
            return seller_info

    except Exception as e:
        print(f"An error occurred for product ID: {product_id}: {e}")

    return seller_info

if __name__ == "__main__":
    # 예제 검색어와 첫 페이지 번호
    kwd = input("Enter keyword: ")
    company = '오늘의집'
    initial_page = 1

    print("오늘의 집 시작...")

    # 첫 페이지에서 totalPage 값을 가져옵니다.
    totalPageJson = fetch_search_results(kwd, initial_page)
    print(f"totalPageJson : {totalPageJson}")
    totalPage = int(totalPageJson['total_count'])
    print(f"totalPage : {totalPage}")

    print("페이지 수집...")

    all_ids = set()

    # 모든 페이지에 대해 for 문을 돌면서 id 값을 수집합니다.
    for page in range(1, 1 + 1):
        results = fetch_search_results(kwd, page)
        ids = parse_results(results)
        all_ids.update(ids)  # set을 사용하여 중복을 자동으로 제거합니다.

    print(f"all_ids : {all_ids}")

    # Selenium WebDriver 설정
    driver = setup_driver()

    all_ids = ['2155528', '2041865', '1926924']

    all_seller_info = []
    print("크롤링 시작...")
    for product_id in all_ids:
        seller_info = click_fourth_tab(driver, product_id)
        seller_info["키워드"] = kwd
        seller_info["플랫폼"] = company

        print(f"seller_info : {seller_info}")

        all_seller_info.append(seller_info)

    # Define the columns
    columns = ['키워드', '상호', 'e-mail', '플랫폼']

    # Create a DataFrame
    df = pd.DataFrame(all_seller_info, columns=columns)

    # Save the DataFrame to an Excel file
    df.to_excel('seller_info.xlsx', index=False)
