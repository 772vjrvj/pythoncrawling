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

# 추출 정보
def extract_information(data, latest_gap):
    try:
        area_info = data["area"]

        address = data["address"]
        region = data["gu"]
        apartment_name = data["name"]
        area = convert_to_pyeong(area_info["public_area"])
        highest_price = latest_gap.get("max_price", 0)
        sale_price = latest_gap.get("tradePrice", 0)
        deposit_price = latest_gap.get("depositPrice", 0)
        gap = latest_gap.get("gapPrice", sale_price - deposit_price)
        deposit_rate = latest_gap.get("gapRate", round((deposit_price / sale_price) * 100, 2) if sale_price else 0)
        compared_to_highest = f"{int((1 - (sale_price / highest_price)) * 100)}%" if highest_price else "0%"
        household_count = data["total_household"]
        year_built = data["diffYearText"][:4]

        return {
            "주소": address,
            "지역": region,
            "아파트명": apartment_name,
            "평수": area,
            "전고점": highest_price,
            "매매가": sale_price,
            "전세가": deposit_price,
            "갭": gap,
            "전세가율": deposit_rate,
            "전고점대비": compared_to_highest,
            "세대수": household_count,
            "연식": year_built
        }

    except KeyError as e:
        print(f"KeyError while extracting information: {e}")
        return {}

# 평수 계산
def convert_to_pyeong(square_meter):
    try:
        return math.floor(square_meter / 3.3)
    except TypeError as e:
        print(f"TypeError in convert_to_pyeong: {e}")
        return 0

# 해당 구가 포함된 것만 list에서 필터한다.
def filter_data_by_address(data_list, gu):
    try:
        return [data for data in data_list if f"서울특별시 {gu}" in data["address"]]
    except KeyError as e:
        print(f"KeyError in filter_data_by_address: {e}")
        return []

# 매매가, 전세가, 갭, 최대 거래가 가져오는 url header
def get_monthly_report_comparison_url_and_headers(apt_id, area_no):
    url = f"https://hogangnono.com/api/v2/apts/{apt_id}/monthly-reports/comparisons?areaNo={area_no}"
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    return url, headers

# 매매가, 전세가, 갭, 최대 거래가 가져오는 함수
def fetch_max_price(driver, apt_id, data):

    area_info = data["area"]
    pyeong = convert_to_pyeong(area_info["public_area"])
    maxPriceUrl = f"https://hogangnono.com/apt/{apt_id}"
    driver.get(maxPriceUrl)
    area_no = 0

    try:
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "__ignore-close-portal-select"))).click()
        time.sleep(2)
        list_container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "list-container.scroll-content")))
        pyeong_elements = list_container.find_elements(By.CLASS_NAME, "py.two")

        # 평당 가격보기 1개인 경우
        # 지역 번호를 알수 없으므로 0부터 100까지 넣어서 값이 존재하는 것으로 선택한다.
        if len(pyeong_elements) == 1:

            for i in range(101):  # range(101)은 0부터 100까지의 숫자를 생성합니다

                url, headers = get_monthly_report_comparison_url_and_headers(apt_id, i)

                response = requests.get(url, headers=headers)
                response_data = response.json()

                if response_data["status"] == "success":
                    max_price = response_data["data"]["summary"]["maxPrice"]

                    if max_price:
                        area_no = i
                        break

                time.sleep(random.uniform(2, 5))

        # 평당 가격보기 1개인 이상인 경우
        else:

            # 동일한것을 클릭하면 url이 안바뀌므로 일단 다른것을 한개 클릭하고 시작해야 한다.
            for element in pyeong_elements:
                text = element.text
                number = int(''.join(filter(str.isdigit, text)))
                if number != pyeong:
                    parent_a_tag = element.find_element(By.XPATH, "./ancestor::a")
                    parent_a_tag.click()
                    break

            # 평형 선택은 선택하면 무조건 창이 사라지므로 한번더 클릭
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "__ignore-close-portal-select"))).click()
            time.sleep(1)
            list_container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "list-container.scroll-content")))
            pyeong_elements = list_container.find_elements(By.CLASS_NAME, "py.two")

            area_no = 0
            # 다른평을 선택했으므로 내 평은 비활성화 되어있어서 클릭이 가능하다
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


    url, headers = get_monthly_report_comparison_url_and_headers(apt_id, area_no)

    latest_gap = {}
    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()


        if response_data["status"] == "success":
            max_price = response_data["data"]["summary"]["maxPrice"]
            latest_gap["max_price"] = max_price

            # 최근 매매가
            if "trade" in response_data["data"]["lists"]:
                trade_list = response_data["data"]["lists"]["trade"]
                if trade_list:
                    trade_last_value = trade_list[-1]
                    latest_gap["tradePrice"] = trade_last_value["averagePrice"]

            # 최근 전세가
            if "deposit" in response_data["data"]["lists"]:
                deposit_list = response_data["data"]["lists"]["deposit"]
                if deposit_list:
                    deposit_last_value = deposit_list[-1]
                    latest_gap["depositPrice"] = deposit_last_value["averagePrice"]

            # 최근 매매가 - 전세가 : gap
            if "gap" in response_data["data"]["lists"]:
                gap_list = response_data["data"]["lists"]["gap"]
                if gap_list:
                    latest_gap = gap_list[-1]
                    latest_gap["max_price"] = max_price

    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error in fetch_max_price: {e}")

    return latest_gap

# 메인함수
def process_data(driver, data_list):
    extracted_data = []
    for data in data_list:
        apt_id = data["id"]
        print(f"apt_id : {apt_id}")
        latest_gap = fetch_max_price(driver, apt_id, data)
        if latest_gap:
            extracted_info = extract_information(data, latest_gap)
            print(f"extracted_info : {extracted_info}")
            extracted_data.append(extracted_info)
        time.sleep(random.uniform(2, 5))
    return extracted_data


def save_to_excel(data):
    try:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        df = pd.DataFrame(data)
        df.to_excel(f"hogangnono_{current_time}.xlsx", index=False)
    except Exception as e:
        print(f"Error saving to Excel: {e}")

# 매번 새롭게 해더를 가져와야 한다.
def set_header(gu):

    headers = {}

    if gu == "동작구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720328559315',
            'X-Hogangnono-Event-Duration': '610300',
            'X-Hogangnono-Event-Log': 'd5634f2635a9bcc6c985630856ee07efe604f9d9',
        }

    elif gu == "성동구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720327868373',
            'X-Hogangnono-Event-Duration': '734220',
            'X-Hogangnono-Event-Log': '605f1e1b7a23fe7e74575fbc0b51db545c34010a',
        }

    elif gu == "마포구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720335085471',
            'X-Hogangnono-Event-Duration': '990782',
            'X-Hogangnono-Event-Log': '418374dd09a5402dafe12ca70aa594fa8a765c8d',
        }

    elif gu == "광진구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720335458843',
            'X-Hogangnono-Event-Duration': '266770',
            'X-Hogangnono-Event-Log': '919e2add5578f099e4469e67b87e9b5463ee52eb',
        }

    elif gu == "양천구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720336577775',
            'X-Hogangnono-Event-Duration': '612055',
            'X-Hogangnono-Event-Log': '0b9364e049482d30a4457ea6148f0927cbccad4a',
        }

    elif gu == "강동구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720336791238',
            'X-Hogangnono-Event-Duration': '654807',
            'X-Hogangnono-Event-Log': '90a93dfbcbf5974a859d7a7ec0296247d6bfe951',
        }

    elif gu == "영등포구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720336931216',
            'X-Hogangnono-Event-Duration': '753453',
            'X-Hogangnono-Event-Log': '3dd0d71569fffd448931d04fb11aaea9bbc7b33b',
        }

    elif gu == "종로구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720337140071',
            'X-Hogangnono-Event-Duration': '385288',
            'X-Hogangnono-Event-Log': '822e897b8890708968297db574237c58238fee26',
        }

    elif gu == "중구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720337267892',
            'X-Hogangnono-Event-Duration': '646970',
            'X-Hogangnono-Event-Log': '746cd26ce766bdd06e673966ead5197c817583e3',
        }

    elif gu == "동대문구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720337428677',
            'X-Hogangnono-Event-Duration': '789275',
            'X-Hogangnono-Event-Log': '1bd76cb36b5179f07c2680cc90436baa236a56fd',
        }

    elif gu == "서대문구":

        headers = {
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720337549894',
            'X-Hogangnono-Event-Duration': '261199',
            'X-Hogangnono-Event-Log': 'da7e7d919a9a5ddc59f862956b8fa262ce12dd6d',
        }

    return headers

# 매번 새롭게 url을 가져와야 한다.
def set_url(gu):
    url = ""
    if gu == "동작구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=13&screenWidth=1768&screenHeight=738&apt&areaNo&startX=126.7644054&endX=127.0679027&startY=37.4506053&endY=37.551111&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=49902"
    elif gu == "성동구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=1768&screenHeight=738&apt&areaNo&startX=126.9979397&endX=127.1496884&startY=37.5252099&endY=37.5754294&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=91616"
    elif gu == "마포구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=13&screenWidth=1768&screenHeight=738&apt&areaNo&startX=126.7961768&endX=127.0996741&startY=37.5116055&endY=37.612029&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=33030"
    elif gu == "광진구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=1768&screenHeight=738&apt&areaNo&startX=127.0446095&endX=127.1963582&startY=37.5228938&endY=37.5731148&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=45138"
    elif gu == "양천구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=1768&screenHeight=738&apt&areaNo&startX=126.811367&endX=126.9631157&startY=37.5015606&endY=37.551796&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=48758"
    elif gu == "강동구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=13&screenWidth=1768&screenHeight=738&apt&areaNo&startX=127.0536471&endX=127.3571444&startY=37.4949954&endY=37.5954413&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=27426"
    elif gu == "영등포구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=1768&screenHeight=738&apt&areaNo&startX=126.8615859&endX=127.0133346&startY=37.507374&endY=37.5576055&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=62126"
    elif gu == "종로구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=2840&screenHeight=1106&apt&areaNo&startX=126.9048914&endX=127.1486505&startY=37.5589955&endY=37.63421&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=50660"
    elif gu == "중구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=15&screenWidth=2840&screenHeight=1106&apt&areaNo&startX=126.9549871&endX=127.0768666&startY=37.5393461&endY=37.5769728&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=38942"
    elif gu == "동대문구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=2840&screenHeight=1106&apt&areaNo&startX=126.9846754&endX=127.2284346&startY=37.5424768&endY=37.617708&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=19700"
    elif gu == "서대문구":
        url = "https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=2840&screenHeight=1106&apt&areaNo&startX=126.8728561&endX=127.1166153&startY=37.5396939&endY=37.6149279&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=36330"
    return url

# json 데이터를 직접 가져와서 해야 하는 경우
# hogangnono.json 에 json을 넣고 실행한다.
def hogangnono_json():

    try:
        with open('hogangnono.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            return json_data["data"]
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return



def main():

    driver = setup_driver()

    main_data = hogangnono_json()

    gus = ["동작구", "성동구", "마포구", "광진구", "양천구", "강동구", "영등포구", "종로구", "중구", "동대문구", "서대문구"]
    # gus = ["동작구", "성동구"]

    combined_data = []

    try:

        for gu in gus:
            print(f"gu : {gu}")

            headers = set_header(gu)
            url = set_url(gu)

            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTP 에러가 발생하면 예외를 발생시킴

            response_data = response.json()

            # pretty_json = json.dumps(response_data, indent=4, ensure_ascii=False)
            # print(pretty_json)

            if response_data["status"] == "success":

                print(f"{gu} response_data len : {len(response_data['data'])}")

                data_list = response_data['data']
                filtered_data = filter_data_by_address(data_list, gu)

                print(f"{gu} filtered_data len : {len(filtered_data)}")

                for item in filtered_data:
                    item["gu"] = gu
                    # combined_data_dict[item["id"]] = item
                    combined_data.append(item)

            time.sleep(random.uniform(2, 5))

        print(f"len combined_data : {len(combined_data)}")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error: {json_err}")
    except Exception as err:
        print(f"An unexpected error occurred: {err}")


    processed_data = process_data(driver, combined_data)
    save_to_excel(processed_data)
    driver.quit()

if __name__ == "__main__":
    main()
