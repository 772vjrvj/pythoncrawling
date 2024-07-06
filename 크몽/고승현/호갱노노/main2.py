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
import requests
from bs4 import BeautifulSoup
import json
from math import radians, degrees, cos, sin, asin, sqrt



def setup_driver():
    # Set up Chrome options
    chrome_options = Options()

    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--start-maximized")
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


def calculate_bounding_box(lng_str, lat_str, distance_km):
    """
    Calculate the bounding box for a given distance (in km) around a point (lng_str, lat_str).

    Parameters:
    lng_str (str): Longitude as a string
    lat_str (str): Latitude as a string
    distance_km (float): Distance in kilometers

    Returns:
    tuple: (startX, endX, startY, endY) - boundaries of the bounding box
    """
    try:
        # Convert string inputs to float
        lng = float(lng_str)
        lat = float(lat_str)
    except ValueError as e:
        raise ValueError("Invalid input: lng_str and lat_str must be convertible to float.") from e

    # Radius of Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat_rad = radians(lat)
    lng_rad = radians(lng)

    # Angular distance in radians
    distance_rad = distance_km / R

    # Latitude boundaries
    min_lat_rad = lat_rad - distance_rad
    max_lat_rad = lat_rad + distance_rad

    # Longitude boundaries (considering the shrinking of longitude degree at different latitudes)
    min_lng_rad = lng_rad - distance_rad / cos(lat_rad)
    max_lng_rad = lng_rad + distance_rad / cos(lat_rad)

    # Convert boundaries from radians to degrees
    min_lat = degrees(min_lat_rad)
    max_lat = degrees(max_lat_rad)
    min_lng = degrees(min_lng_rad)
    max_lng = degrees(max_lng_rad)

    return min_lng, max_lng, min_lat, max_lat



def fetch_rec_idx_values(driver, url):
    driver.get(url)

    url = "https://hogangnono.com/api/apt/bounding?map=google&level=13&screenWidth=1098&screenHeight=953&apt&areaNo&startX=126.8452579&endX=127.0337421&startY=37.447539&endY=37.5773046&tradeType=0&areaFrom=0&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=151000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=0&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=0&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=27594"

    details_mapping = [
        ["지역", "아파트명", "평수", "매매가", "전세가", "갭", "전세가율"],
        ["전고점", "전고점 대비", "세대수", "연식"]
    ]
    datas = []

    # try:
    time.sleep(2)

    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': 'bat=B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w; _gcl_au=1.1.1396125265.1719933774; _fbp=fb.1.1719933774368.236361690114970150; _wp_uid=1-91bbdc913b84b6fa0d4707b4d05274c1-s1719933773.958925|windows_10|chrome-bb5ew7; _gid=GA1.2.954109146.1720198706; connect.sid=s%3AZVXULkglG6idlQ0Xvh9x0PBv156sSB4myg.1PyJrwOIkmLdoNAUkam%2FYoDwTCu1uUaqyHNJvUFXRfw; client.cid=1PyJrwOIkmLdoNAUkam%2FYoDwTCu1uUaqyHNJvUFXRfw; _gat_UA-216121571-2=1; _ga=GA1.2.1002612096.1719933775; _ga_P8RWS72S79=GS1.1.1720243978.5.1.1720244624.0.0.0; cto_bundle=OnqxWV9PaVlvS2c0SzVzWUFLaXptZmdTQTZlVERVNU1jRG5GVTBJck4lMkZlWUNKSEVMbnp0dlVka3o1dzl0dmhKVzh5ZHp2YUwzU2NpSGQ5diUyRmRwVUtHZWdPJTJGaW4xRElZalIyeUFWVkJkNjJTMlR4b051TjhiNWc1THEzUDYyVUxtMGl4QWFvQiUyRkl5anhDYWhTJTJGbWZSSnFlZXZxUFN5VVZrTzNrVGduVlFpTlhpejNac0ZlbSUyRnBDZjVhTEY2TU53V0lscmc',
        'Priority': 'u=1, i',
        'Referer': 'https://hogangnono.com/region/11590/0',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'X-Hogangnono-Api-Version': '1.9.18',
        'X-Hogangnono-App-Name': 'hogangnono',
        'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
        'X-Hogangnono-Ct': '1720244625701',
        'X-Hogangnono-Event-Duration': '234815',
        'X-Hogangnono-Event-Log': 'f6d2106c1d3da3e60142afb94ae7a92445b21f8b',
        'X-Hogangnono-Platform': 'desktop',
        'X-Hogangnono-Release-Version': '1.9.18.16'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html_content = response.text
        data = json.loads(html_content)

        # JSON 데이터 출력
        # print(json.dumps(data, indent=4, ensure_ascii=False))

        # "서울특별시 동작구"인 항목만 필터링합니다.
        filtered_data = [item for item in data['data'] if "서울특별시 동작구" in item['content']['name']]

        # 결과를 출력합니다.
        print(json.dumps(filtered_data, indent=4, ensure_ascii=False))


        # startX = 126.9668879
        # endX = 126.9904485
        # startY = 37.4749499
        # endY = 37.491177



        startX = "126.9786682"
        endX = "126.9786682"
        startY = "37.4830639"
        endY = "37.4830639"


        startX = "126.9786682"
        endX = "126.9796682"  # startX보다 약간 큰 값으로 설정
        startY = "37.4830639"
        endY = "37.4840639"  # startY보다 약간 큰 값으로 설정




        # URL 및 파라미터 설정
        lng = "126.9786682"
        startX = "126.9668879"
        endX = "126.9904485"

        lat = "37.4830639"
        startY = "37.4749499"
        endY = "37.491177"




        # startX, endX, startY, endY = calculate_bounding_box(lng, lat, 2)

        #
        # url = f"https://hogangnono.com/api/apt/bounding?map=google&level=16&screenWidth=1098&screenHeight=953&apt&areaNo&startX={startX}&endX={endX}&startY={startY}&endY={endY}&tradeType=0&areaFrom=0&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=151000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=0&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=0&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=62188"
        #
        # url = f"https://hogangnono.com/api/apt/bounding?map=google&level=16&screenWidth=1104&screenHeight=953&apt&areaNo&startX=126.9678106&endX=126.9914999&startY=37.4752735&endY=37.4915005&tradeType=0&areaFrom=0&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=151000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=0&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=0&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=55498"
        #
        #
        #
        # # 헤더 설정
        # headers = {
        #     'Accept': 'application/json',
        #     'Accept-Encoding': 'gzip, deflate, br, zstd',
        #     'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        #     'Cookie': 'bat=B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w; _gcl_au=1.1.1396125265.1719933774; _fbp=fb.1.1719933774368.236361690114970150; _wp_uid=1-91bbdc913b84b6fa0d4707b4d05274c1-s1719933773.958925|windows_10|chrome-bb5ew7; _gid=GA1.2.954109146.1720198706; connect.sid=s%3AZVXULkglG6idlQ0Xvh9x0PBv156sSB4myg.1PyJrwOIkmLdoNAUkam%2FYoDwTCu1uUaqyHNJvUFXRfw; client.cid=1PyJrwOIkmLdoNAUkam%2FYoDwTCu1uUaqyHNJvUFXRfw; _ga=GA1.2.1002612096.1719933775; _ga_P8RWS72S79=GS1.1.1720243978.5.1.1720247622.0.0.0; cto_bundle=LeVYtF9PaVlvS2c0SzVzWUFLaXptZmdTQTZSQ1AxVEFtYmtFMUJqNEZYUCUyQlJzNVl1WmZOdlN6V1RTZkphQkdyRnZOd1VINU9MV2J3d25Eb0dxMENnd0JDc0FtZnU3eXA2RU5KcFg1emNOUDYlMkJQT1k4MTVsamd3SllhT1dYMHN4YzQ4VXJKNTlhMnNlSUpuR2c4JTJCQjhnaTN4ekFTOEc1akNsbWRORkVOa3M2cHdIYnhkZDlvc3hQWmRkQ1lDN0NsWFJnclc',
        #     'Priority': 'u=1, i',
        #     'Referer': 'https://hogangnono.com/region/11590/0',
        #     'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        #     'Sec-Ch-Ua-Mobile': '?0',
        #     'Sec-Ch-Ua-Platform': '"Windows"',
        #     'Sec-Fetch-Dest': 'empty',
        #     'Sec-Fetch-Mode': 'cors',
        #     'Sec-Fetch-Site': 'same-origin',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        #     'X-Hogangnono-Api-Version': '1.9.18',
        #     'X-Hogangnono-App-Name': 'hogangnono',
        #     'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
        #     'X-Hogangnono-Ct': '1720247635760',
        #     'X-Hogangnono-Event-Duration': '284763',
        #     'X-Hogangnono-Event-Log': 'd7dcb29f1b5dcdb76a71bff054da83370aa5b1c0',
        #     'X-Hogangnono-Platform': 'desktop',
        #     'X-Hogangnono-Release-Version': '1.9.18.16'
        # }
        #


        url = "https://hogangnono.com/api/v2/items/local?regionCode=11590107&offset=10&limit=10"

        headers = {
            'authority': 'hogangnono.com',
            'method': 'GET',
            'path': '/api/v2/items/local?regionCode=11590107&offset=10&limit=10',
            'scheme': 'https',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Priority': 'u=1, i',
            'Referer': 'https://hogangnono.com/local-item/11590107',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'X-Hogangnono-Api-Version': '1.9.18',
            'X-Hogangnono-App-Name': 'hogangnono',
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            # 'X-Hogangnono-Ct': '1720253931258',
            # 'X-Hogangnono-Event-Duration': '68049',
            # 'X-Hogangnono-Event-Log': 'd6daddae5638c13661633205169b2fd504ba6f32',
            'X-Hogangnono-Platform': 'desktop',
            'X-Hogangnono-Release-Version': '1.9.18.16'
        }



        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # print(f"Response JSON: {response.json()}")

            res = response.json()
            print(f"len : {len(res['data'])}")


        else:
            print(f"Failed to fetch data: {response.status_code}")



    #     soup = BeautifulSoup(html_content, 'html.parser')
    #
    #     # 필요한 데이터를 추출
    #     # 예시로, '서울특별시 동작구' 지역 정보를 추출
    #     region_info = soup.find('script', {'id': '__HGNN_DATA__'})
    #
    #     if region_info:
    #         import json
    #         data = json.loads(region_info.string)
    #         region_data = data['queryState']['queries'][0]['state']['data']
    #
    #         print("지역명:", region_data['name'])
    #         print("위도:", region_data['lat'])
    #         print("경도:", region_data['lng'])
    #
    #         # 추가적으로 필요한 데이터를 추출하여 사용할 수 있습니다.
    #     else:
    #         print("필요한 데이터를 찾을 수 없습니다.")
    # else:
    #     print(f"Failed to fetch data: {response.status_code}")






        # maplist 요소들을 기다림
        # maplist = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cluster')))
        #
        # print(f"maplist : {len(maplist)}")
        #
        # for index, map in enumerate(maplist):
        #     try:
        #         loca = map.text.split('\n')[0]  # 지역
        #         map.click()  # map 클릭
        #         time.sleep(3)
        #
        #         # real 요소들을 찾아서 클릭
        #         realList = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'diff-price')))
        #
        #         for real in realList:
        #             try:
        #                 real.click()
        #                 time.sleep(3)
        #
        #                 # 세부 정보 수집
        #                 area = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'areaSelector'))).text.strip()  # 평수
        #                 aptDetail = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'header-info'))).text.strip().split('\n')[0]  # 아파트명
        #                 price = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'price-group'))).text.strip().split('\n')[1]  # 매매가
        #                 card = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'card'))).text.strip()
        #                 age = card.split('\n')[1]  # 연식
        #                 cnt = card.split('\n')[0]  # 세대수
        #                 high = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
        #                 beforehigh = high[2].text.split('\n')[1]  # 전고점
        #
        #                 # 갭 = 매매가 - 전세가
        #                 time.sleep(3)
        #
        #                 datas.append([loca, aptDetail, area, price, "갭", "전세가율", beforehigh, "전고점대비", cnt, age])
        #
        #             except StaleElementReferenceException as e:
        #                 print(f"StaleElementReferenceException 발생: {e}")
        #                 continue
        #
        #     except StaleElementReferenceException as e:
        #         print(f"StaleElementReferenceException 발생: {e}")
        #         continue

    # except Exception as e:
    #     maplist = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cluster')))
    #     print(f"에러 발생: {e}")
    #
    # finally:
    #     # 웹 드라이버 종료
    #     driver.quit()


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
