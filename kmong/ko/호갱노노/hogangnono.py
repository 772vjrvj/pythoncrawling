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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
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
def extract_information(data, gu, latest_gap):
    try:
        area_info = data["area"]

        address = data["address"]
        region = gu
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
def process_data(driver, data_list, gu):
    filtered_data = filter_data_by_address(data_list, gu)
    extracted_data = []
    print(f"filtered_data len :  {len(filtered_data)}")
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
