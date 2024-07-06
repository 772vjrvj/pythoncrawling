import json
import pandas as pd
import math
import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, WebDriverException
from datetime import datetime

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

def extract_information(data, gu, latest_gap):
    try:
        area_info = data["area"]
        주소 = data["address"]
        지역 = gu
        아파트명 = data["name"]
        평수 = convert_to_pyeong(area_info["public_area"])
        전고점 = latest_gap.get("max_price", 0)
        매매가 = latest_gap.get("tradePrice", 0)
        전세가 = latest_gap.get("depositPrice", 0)
        갭 = latest_gap.get("gapPrice", 매매가 - 전세가)
        전세가율 = latest_gap.get("gapRate", round((전세가 / 매매가) * 100, 2) if 매매가 else 0)
        전고점대비 = f"{int((1 - (매매가 / 전고점)) * 100)}%" if 전고점 else "0%"
        세대수 = data["total_household"]
        연식 = data["diffYearText"][:4]

        return {
            "주소": 주소,
            "지역": 지역,
            "아파트명": 아파트명,
            "평수": 평수,
            "전고점": 전고점,
            "매매가": 매매가,
            "전세가": 전세가,
            "갭": 갭,
            "전세가율": 전세가율,
            "전고점대비": 전고점대비,
            "세대수": 세대수,
            "연식": 연식
        }
    except KeyError as e:
        print(f"KeyError while extracting information: {e}")
        return {}

def convert_to_pyeong(square_meter):
    try:
        return math.floor(square_meter / 3.3)
    except TypeError as e:
        print(f"TypeError in convert_to_pyeong: {e}")
        return 0

def filter_data_by_address(data_list, gu):
    try:
        return [data for data in data_list if f"서울특별시 {gu}" in data["address"]]
    except KeyError as e:
        print(f"KeyError in filter_data_by_address: {e}")
        return []

def fetch_max_price(driver, apt_id, data):
    area_info = data["area"]
    pyeong = convert_to_pyeong(area_info["public_area"])

    maxPriceUrl = f"https://hogangnono.com/apt/{apt_id}"
    driver.get(maxPriceUrl)

    area_no = 0
    try:
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "__ignore-close-portal-select"))).click()
        time.sleep(1)
        list_container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "list-container.scroll-content")))
        pyeong_elements = list_container.find_elements(By.CLASS_NAME, "py.two")

        if len(pyeong_elements) == 1:

            for i in range(101):  # range(101)은 0부터 100까지의 숫자를 생성합니다

                url = f"https://hogangnono.com/api/v2/apts/{apt_id}/monthly-reports/comparisons?areaNo={i}"
                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                response = requests.get(url, headers=headers)
                response_data = response.json()


                if response_data["status"] == "success":
                    max_price = response_data["data"]["summary"]["maxPrice"]

                    if max_price:
                        area_no = i
                        break

        else:
            # 동일한것을 클릭하면 url이 안바뀌므로 일단 다른것을 한개 클릭하고 시작해야 한다.
            for element in pyeong_elements:
                text = element.text
                number = int(''.join(filter(str.isdigit, text)))
                if number != pyeong:
                    parent_a_tag = element.find_element(By.XPATH, "./ancestor::a")
                    parent_a_tag.click()
                    time.sleep(2)
                    break

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "__ignore-close-portal-select"))).click()
            time.sleep(1)
            list_container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "list-container.scroll-content")))
            pyeong_elements = list_container.find_elements(By.CLASS_NAME, "py.two")

            area_no = 0

            for element in pyeong_elements:
                text = element.text
                number = int(''.join(filter(str.isdigit, text)))
                if number == pyeong:
                    parent_a_tag = element.find_element(By.XPATH, "./ancestor::a")
                    parent_a_tag.click()
                    time.sleep(2)
                    new_url = driver.current_url
                    area_no = new_url.split('/')[-1]
                    break

    except (NoSuchElementException, TimeoutException, ValueError) as e:
        print(f"Error fetching max price: {e}")
        area_no = 0

    url = f"https://hogangnono.com/api/v2/apts/{apt_id}/monthly-reports/comparisons?areaNo={area_no}"
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()




        latest_gap = {}
        if response_data["status"] == "success":
            max_price = response_data["data"]["summary"]["maxPrice"]
            latest_gap["max_price"] = max_price

            if "trade" in response_data["data"]["lists"]:
                trade_list = response_data["data"]["lists"]["trade"]
                if trade_list:
                    trade_last_value = trade_list[-1]
                    latest_gap["tradePrice"] = trade_last_value["averagePrice"]

            if "deposit" in response_data["data"]["lists"]:
                deposit_list = response_data["data"]["lists"]["deposit"]
                if deposit_list:
                    deposit_last_value = deposit_list[-1]
                    latest_gap["depositPrice"] = deposit_last_value["averagePrice"]

            if "gap" in response_data["data"]["lists"]:
                gap_list = response_data["data"]["lists"]["gap"]
                if gap_list:
                    latest_gap = gap_list[-1]
                    latest_gap["max_price"] = max_price

        return latest_gap
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error in fetch_max_price: {e}")
        return {}

def process_data(driver, data_list, gu):
    filtered_data = filter_data_by_address(data_list, gu)
    extracted_data = []
    for data in filtered_data:
        apt_id = data["id"]
        print(f"apt_id : {apt_id}")
        latest_gap = fetch_max_price(driver, apt_id, data)
        if latest_gap:
            extracted_info = extract_information(data, gu, latest_gap)
            print(f"extracted_info : {extracted_info}")
            extracted_data.append(extracted_info)
        time.sleep(random.uniform(2, 5))
    return extracted_data



def set_header(gu):


    headers = {
        ":authority": "hogangnono.com",
        ":method": "GET",
        ":path": "/api/apt/bounding?map=google&level=14&screenWidth=2282&screenHeight=952&apt&areaNo&startX=126.8292076&endX=127.0250732&startY=37.466991&endY=37.531817&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=83740",
        ":scheme": "https",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": "bat=B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w; _gcl_au=1.1.1396125265.1719933774; _fbp=fb.1.1719933774368.236361690114970150; _wp_uid=1-91bbdc913b84b6fa0d4707b4d05274c1-s1719933773.958925|windows_10|chrome-bb5ew7; _gid=GA1.2.954109146.1720198706; connect.sid=s%3AYzgxfx3AV-huAI6Oh_tSg23VjU2Ed1_Pxw.nzLerDk8KEomVPqHhlBp3dV2GRzOGyxYp3Yc7Mjd%2Fz8; client.cid=nzLerDk8KEomVPqHhlBp3dV2GRzOGyxYp3Yc7Mjd%2Fz8; _ga=GA1.2.1002612096.1719933775; cto_bundle=nDAjiV9PaVlvS2c0SzVzWUFLaXptZmdTQTZaVkdDdDh5UHJ2eG9XWU04VjZPQUdEVHR0aENoRXFvSVpCOWZzV3ZXQTRTYlptc21ZZXgzTFRqUmtJVlJkd0NFRUh1QzRxOW83MmEzajRJOTV6am1uQ1hWaUlYUDVzNzV2N2dldTljSFclMkJPektGa01selA5RWNoNUVIRVVGZjAwNEx2ZCUyQlo4bVZXJTJGeHNrRzRUbW9mSVVLbFkxTFAlMkZ4THNtVlprMEVBTyUyQjI2; _ga_P8RWS72S79=GS1.1.1720271266.6.1.1720283211.0.0.0",
        "Priority": "u=1, i",
        "Referer": "https://hogangnono.com/region/11590/0",
        "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Hogangnono-Api-Version": "1.9.18",
        "X-Hogangnono-App-Name": "hogangnono",
        "X-Hogangnono-At": "B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w",
        "X-Hogangnono-Ct": "1720283278496",
        "X-Hogangnono-Event-Duration": "529168",
        "X-Hogangnono-Event-Log": "d497fe5fb4a55f5311bbb3d19fcd0377d51396c5",
        "X-Hogangnono-Platform": "desktop",
        "X-Hogangnono-Release-Version": "1.9.18.16"
    }


def set_url(gu):

    url = ""
    if gu == "동작구":
        url = build_url(
            startX=126.8292076,  # 시작 X 좌표 (경도)
            endX=127.0250732,    # 끝 X 좌표 (경도)
            startY=37.466991,   # 시작 Y 좌표 (위도)
            endY=37.531817,     # 끝 Y 좌표 (위도)
            tradeType=0,         # 거래 유형 (예: 0은 매매)
            areaFrom=20,         # 면적 최소값 (평)
            areaTo=80,           # 면적 최대값 (평)
            priceFrom=0,         # 가격 최소값 (만원)
            priceTo=401000,      # 가격 최대값 (만원)
            gapPriceFrom=0,      # 갭 가격 최소값 (만원)
            gapPriceTo=47000,    # 갭 가격 최대값 (만원)
            gapPriceNeg=False,   # 갭 가격 음수 여부
            sinceFrom=0,         # 연식 최소값 (년)
            sinceTo=30,          # 연식 최대값 (년)
            floorAreaRatioFrom=0,        # 용적률 최소값
            floorAreaRatioTo=900,        # 용적률 최대값
            buildingCoverageRatioFrom=0, # 건폐율 최소값
            buildingCoverageRatioTo=100, # 건폐율 최대값
            rentalBusinessRatioFrom=0,   # 임대사업비율 최소값
            rentalBusinessRatioTo=100,   # 임대사업비율 최대값
            householdFrom=500,   # 세대수 최소값
            householdTo=5000,    # 세대수 최대값
            parking=0,           # 주차 수
            profitRatio=0,       # 수익률
            rentRateFrom=40,     # 전세가율 최소값
            rentRateTo=200       # 전세가율 최대값
        )



def build_url(startX, endX, startY, endY, tradeType,
              areaFrom, areaTo, priceFrom, priceTo, gapPriceFrom, gapPriceTo, gapPriceNeg, sinceFrom, sinceTo,
              floorAreaRatioFrom, floorAreaRatioTo, buildingCoverageRatioFrom, buildingCoverageRatioTo,
              rentalBusinessRatioFrom, rentalBusinessRatioTo, householdFrom, householdTo, parking, profitRatio,
              rentRateFrom, rentRateTo):
    base_url = "https://hogangnono.com/api/apt/bounding"
    url = (f"{base_url}?map=google&level=15&screenWidth=2399&screenHeight=943&apt"
           f"&areaNo&startX={startX}&endX={endX}&startY={startY}&endY={endY}&tradeType={tradeType}"
           f"&areaFrom={areaFrom}&areaTo={areaTo}&priceFrom={priceFrom}&priceTo={priceTo}&gapPriceFrom={gapPriceFrom}"
           f"&gapPriceTo={gapPriceTo}&gapPriceNeg={gapPriceNeg}&sinceFrom={sinceFrom}&sinceTo={sinceTo}"
           f"&floorAreaRatioFrom={floorAreaRatioFrom}&floorAreaRatioTo={floorAreaRatioTo}"
           f"&buildingCoverageRatioFrom={buildingCoverageRatioFrom}&buildingCoverageRatioTo={buildingCoverageRatioTo}"
           f"&rentalBusinessRatioFrom={rentalBusinessRatioFrom}&rentalBusinessRatioTo={rentalBusinessRatioTo}"
           f"&householdFrom={householdFrom}&householdTo={householdTo}&parking={parking}&profitRatio={profitRatio}"
           f"&rentRateFrom={rentRateFrom}&rentRateTo={rentRateTo}&aptType=-1&isIgnorePin=false"
           f"&auctionState=-1&reconstructionStep=0"
           f"&reconstructionStepFrom=1&reconstructionStepTo=10&r=23776")
    return url

def save_to_excel(data):
    try:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        df = pd.DataFrame(data)
        df.to_excel(f"hogangnono_{current_time}.xlsx", index=False)
    except Exception as e:
        print(f"Error saving to Excel: {e}")

def main():
    driver = setup_driver()
    if not driver:
        return

    try:
        with open('hogangnono.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    gu = "동작구"



    processed_data = process_data(driver, json_data["data"], gu)
    save_to_excel(processed_data)
    driver.quit()

if __name__ == "__main__":
    main()
