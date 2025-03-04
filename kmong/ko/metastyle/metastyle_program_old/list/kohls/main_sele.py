import requests
import json
from typing import List, Dict
import time

import os
import os
import ssl
import time

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver

from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime

ssl._create_default_https_context = ssl._create_unverified_context
import json
import os
import random
import re
import ssl
import time
from datetime import datetime

import pandas as pd
import psutil
import requests
from PyQt5.QtCore import QThread, pyqtSignal, QEventLoop
from PyQt5.QtWidgets import QMessageBox
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ssl._create_default_https_context = ssl._create_unverified_context


baseUrl = "https://www.kohls.com/catalog/womens-shirts-blouses-tops-clothing.jsp"

sess = requests.Session()



def _close_chrome_processes():
    """모든 Chrome 프로세스를 종료합니다."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()  # Chrome 프로세스를 종료
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def _setup_driver():
    try:
        _close_chrome_processes()

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
        # chrome_options.add_argument("--headless")  # Headless 모드 추가

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
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
                Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
            '''
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        return driver
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None





def fetch_products(page: int) -> Dict:

    # API 요청을 위한 URL 및 기본 파라미터



    headers = {
        "authority": "www.kohls.com",
        "method": "GET",
        "scheme": "https",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.kohls.com/catalog/womens-shirts-blouses-tops-clothing.jsp",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    # 요청 파라미터 템플릿
    payload = {
        "CN": "Gender:Womens Product:Shirts & Blouses Category:Tops Department:Clothing",
        "cc": "wms-TN3.0-S-shirtsblouses",
        "kls_sbp": "05864698454350754950882754362888169186",
        "spa": "1",
        "PPP": "48",
        "WS": 0,  # WS 값 변경
        "S": "1",
        "ajax": "true",
        "gNav": "false"
    }

    """
    특정 WS 값을 사용하여 요청을 보내고 데이터를 가져옴.
    :param ws_value: 변경할 WS 값 (0, 48, 96, ...)
    :return: JSON 데이터에서 'totalRecordsCount'와 'products' 리스트를 반환
    """
    payload["WS"] = page * 48

    response = sess.get(baseUrl, params=payload, headers=headers, timeout=10)

    if response.status_code == 200:
        data = response.json()
        return {
            "totalRecordsCount": data.get("totalRecordsCount", 0),
            "products": data.get("products", [])
        }
    else:
        print(f"Failed to fetch data for WS={page}. Status Code: {response.status_code}")
        return {"totalRecordsCount": 0, "products": []}


def main():

    # driver = _setup_driver()
    # driver.get(baseUrl)
    # cookies = driver.get_cookies()
    # for cookie in cookies:
    #     sess.cookies.set(cookie['name'], cookie['value'])
    # driver.quit()



    """
    메인 실행 함수
    - WS 값을 0, 48, 96씩 증가시키면서 데이터 가져오기
    - totalRecordsCount 저장
    - products 리스트 수집
    """
    all_products: List[Dict] = []
    total_records = 0

    for ws in range(0, 47):  # 1부터 47까지 반복
        result = fetch_products(ws)
        if ws == 0:
            total_records = result["totalRecordsCount"]
        all_products.extend(result["products"])
        time.sleep(2)

    print(f"Total Records Count: {total_records}")
    print(f"Total Products Collected: {len(all_products)}")

    # 결과 출력 (일부만 표시)
    for product in all_products[:5]:  # 처음 5개만 출력
        print(json.dumps(product, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
