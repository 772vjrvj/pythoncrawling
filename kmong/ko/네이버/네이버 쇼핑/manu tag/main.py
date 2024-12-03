import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
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

def get_cookies_as_dict(driver):
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_dict

def fetch_initial_state():
    url = "https://msearch.shopping.naver.com/search/all?adQuery=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&origQuery=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&pagingIndex=2&pagingSize=40&productSet=checkout&query=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&sort=rel&viewType=list"

    # Selenium을 통해 쿠키를 수집
    driver = setup_driver()
    driver.get(url)

    # 쿠키 수집
    cookies = get_cookies_as_dict(driver)

    # 쿠키를 requests 라이브러리용으로 변환
    cookie_string = "; ".join([f"{name}={value}" for name, value in cookies.items()])

    print(f"cookie_string : {cookie_string}")

    # 수집한 쿠키를 사용해 requests로 동일 URL 요청
    headers = {
        "authority": "msearch.shopping.naver.com",
        "method": "GET",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": cookie_string,
        "logic": "PART",
        "priority": "u=1, i",
        "referer": "https://msearch.shopping.naver.com/search/all?adQuery=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&origQuery=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&pagingIndex=2&pagingSize=40&productSet=checkout&query=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&sort=rel&viewType=list",
        "sbth": "aa1d72598d6f5149f179eaea44c3490cbf9278d7b338cb7a4e29bc6fdf1cc0cf26387c1f81e15667d8d6b34b718e9b53",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-arch": "",
        "sec-ch-ua-bitness": "",
        "sec-ch-ua-form-factors": "",
        "sec-ch-ua-full-version-list": "",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "",
        "sec-ch-ua-platform": "Windows",
        "sec-ch-ua-platform-version": "",
        "sec-ch-ua-wow64": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    url = "https://msearch.shopping.naver.com/api/search/all?adQuery=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&origQuery=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&pagingIndex=2&pagingSize=40&productSet=checkout&query=%EB%B9%97%EC%9E%90%EB%A3%A8%EC%84%B8%ED%8A%B8&sort=rel&viewType=list"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # BeautifulSoup을 사용해 HTML을 파싱하고, JSON 데이터를 추출
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

        if script_tag:
            json_data = script_tag.string
            parsed_data = json.loads(json_data)
            initial_state = parsed_data.get('props', {}).get('pageProps', {}).get('initialState', {})

            # JSON 형태로 pretty-print
            print(json.dumps(initial_state, indent=4, ensure_ascii=False))
        else:
            print("script 태그를 찾을 수 없습니다.")
    else:
        print(f"Error: {response.status_code}")

    driver.quit()

if __name__ == "__main__":
    fetch_initial_state()
