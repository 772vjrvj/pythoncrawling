import json
import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, WebDriverException
from datetime import datetime

# 드라이버 세팅
def set_header(gu):

    headers = {}

    if gu == "동작구":

        headers = {
            # 'Accept': 'application/json',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',
            # 'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            # 'X-Hogangnono-Api-Version': '1.9.18',
            # 'X-Hogangnono-App-Name': 'hogangnono',
            'X-Hogangnono-At': 'B-ZPpvSjl0d1-SOnxH9wm3zZxgrrTXdhBk5w',
            'X-Hogangnono-Ct': '1720328559315',
            'X-Hogangnono-Event-Duration': '610300',
            'X-Hogangnono-Event-Log': 'd5634f2635a9bcc6c985630856ee07efe604f9d9',
            # 'X-Hogangnono-Platform': 'desktop',
            # 'X-Hogangnono-Release-Version': '1.9.18.16'
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


    return headers


def set_url(gu):

    url = ""
    if gu == "동작구":
        url = build_url(
            level=13,
            startX=126.7644054,  # 시작 X 좌표 (경도)  ********** 필수값 **********
            endX=127.0679027,    # 끝 X 좌표 (경도)   ********** 필수값 **********
            startY=37.4506053,   # 시작 Y 좌표 (위도) ********** 필수값 **********
            endY=37.551111,     # 끝 Y 좌표 (위도)   ********** 필수값 **********

            screenWidth=1768,
            screenHeight=738,

            tradeType=0,         # 거래 유형 (예: 0은 매매)
            areaFrom=20,         # 면적 최소값 (평)
            areaTo=80,           # 면적 최대값 (평)
            priceFrom=0,         # 가격 최소값 (만원)
            priceTo=401000,      # 가격 최대값 (만원)
            gapPriceFrom=0,      # 갭 가격 최소값 (만원)
            gapPriceTo=47000,    # 갭 가격 최대값 (만원)
            gapPriceNeg="false",   # 갭 가격 음수 여부
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
            rentRateTo=200,       # 전세가율 최대값
            r=49902
        )
    elif gu == "성동구":

        url = build_url(
            level=14,
            startX=126.9979397,  # 시작 X 좌표 (경도) ********** 필수값 **********
            endX=127.1496884,    # 끝 X 좌표 (경도)   ********** 필수값 **********
            startY=37.5252099,   # 시작 Y 좌표 (위도) ********** 필수값 **********
            endY=37.5754294,     # 끝 Y 좌표 (위도)   ********** 필수값 **********

            screenWidth=1768,
            screenHeight=738,

            tradeType=0,         # 거래 유형 (예: 0은 매매)
            areaFrom=20,         # 면적 최소값 (평)
            areaTo=80,           # 면적 최대값 (평)
            priceFrom=0,         # 가격 최소값 (만원)
            priceTo=401000,      # 가격 최대값 (만원)
            gapPriceFrom=0,      # 갭 가격 최소값 (만원)
            gapPriceTo=47000,    # 갭 가격 최대값 (만원)
            gapPriceNeg="false",   # 갭 가격 음수 여부
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
            rentRateTo=200,      # 전세가율 최대값
            r=91616
        )

    elif gu == "마포구":
        url = build_url(
            level=13,
            startX=126.7961768,  # 시작 X 좌표 (경도) ********** 필수값 **********
            endX=127.0996741,    # 끝 X 좌표 (경도)   ********** 필수값 **********
            startY=37.5116055,   # 시작 Y 좌표 (위도) ********** 필수값 **********
            endY=37.612029,     # 끝 Y 좌표 (위도)   ********** 필수값 **********

            screenWidth=1768,
            screenHeight=738,

            tradeType=0,         # 거래 유형 (예: 0은 매매)
            areaFrom=20,         # 면적 최소값 (평)
            areaTo=80,           # 면적 최대값 (평)
            priceFrom=0,         # 가격 최소값 (만원)
            priceTo=401000,      # 가격 최대값 (만원)
            gapPriceFrom=0,      # 갭 가격 최소값 (만원)
            gapPriceTo=47000,    # 갭 가격 최대값 (만원)
            gapPriceNeg="false",   # 갭 가격 음수 여부
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
            rentRateTo=200,      # 전세가율 최대값
            r=33030
        )

    elif gu == "광진구":
        url = build_url(
            level=14,
            startX=127.0446095,  # 시작 X 좌표 (경도) ********** 필수값 **********
            endX=127.1963582,    # 끝 X 좌표 (경도)   ********** 필수값 **********
            startY=37.5228938,   # 시작 Y 좌표 (위도) ********** 필수값 **********
            endY=37.5731148,     # 끝 Y 좌표 (위도)   ********** 필수값 **********

            screenWidth=1768,
            screenHeight=738,

            tradeType=0,         # 거래 유형 (예: 0은 매매)
            areaFrom=20,         # 면적 최소값 (평)
            areaTo=80,           # 면적 최대값 (평)
            priceFrom=0,         # 가격 최소값 (만원)
            priceTo=401000,      # 가격 최대값 (만원)
            gapPriceFrom=0,      # 갭 가격 최소값 (만원)
            gapPriceTo=47000,    # 갭 가격 최대값 (만원)
            gapPriceNeg="false",   # 갭 가격 음수 여부
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
            rentRateTo=200,      # 전세가율 최대값
            r=45138
        )



    return url


def build_url(level, screenWidth, screenHeight, startX, endX, startY, endY, tradeType,
              areaFrom, areaTo, priceFrom, priceTo, gapPriceFrom, gapPriceTo, gapPriceNeg, sinceFrom, sinceTo,
              floorAreaRatioFrom, floorAreaRatioTo, buildingCoverageRatioFrom, buildingCoverageRatioTo,
              rentalBusinessRatioFrom, rentalBusinessRatioTo, householdFrom, householdTo, parking, profitRatio,
              rentRateFrom, rentRateTo, r):
    base_url = "https://hogangnono.com/api/apt/bounding"
    url = (f"{base_url}?map=google&level={level}&screenWidth={screenWidth}&screenHeight={screenHeight}&apt"
           f"&areaNo&startX={startX}&endX={endX}&startY={startY}&endY={endY}&tradeType={tradeType}"
           f"&areaFrom={areaFrom}&areaTo={areaTo}&priceFrom={priceFrom}&priceTo={priceTo}&gapPriceFrom={gapPriceFrom}"
           f"&gapPriceTo={gapPriceTo}&gapPriceNeg={gapPriceNeg}&sinceFrom={sinceFrom}&sinceTo={sinceTo}"
           f"&floorAreaRatioFrom={floorAreaRatioFrom}&floorAreaRatioTo={floorAreaRatioTo}"
           f"&buildingCoverageRatioFrom={buildingCoverageRatioFrom}&buildingCoverageRatioTo={buildingCoverageRatioTo}"
           f"&rentalBusinessRatioFrom={rentalBusinessRatioFrom}&rentalBusinessRatioTo={rentalBusinessRatioTo}"
           f"&householdFrom={householdFrom}&householdTo={householdTo}&parking={parking}&profitRatio={profitRatio}"
           f"&rentRateFrom={rentRateFrom}&rentRateTo={rentRateTo}&aptType=-1&isIgnorePin=false"
           f"&auctionState=-1&reconstructionStep=0"
           f"&reconstructionStepFrom=1&reconstructionStepTo=10&r={r}")
    return url




def main():
    gu = "광진구"

    try:
        headers = set_header(gu)
        url = set_url(gu)
        print(url)
        print("https://hogangnono.com/api/apt/bounding?map=google&level=14&screenWidth=1768&screenHeight=738&apt&areaNo&startX=127.0446095&endX=127.1963582&startY=37.5228938&endY=37.5731148&tradeType=0&areaFrom=20&areaTo=80&priceFrom=0&priceTo=401000&gapPriceFrom=0&gapPriceTo=47000&gapPriceNeg=false&sinceFrom=0&sinceTo=30&floorAreaRatioFrom=0&floorAreaRatioTo=900&buildingCoverageRatioFrom=0&buildingCoverageRatioTo=100&rentalBusinessRatioFrom=0&rentalBusinessRatioTo=100&householdFrom=500&householdTo=5000&parking=0&profitRatio=0&rentRateFrom=40&rentRateTo=200&aptType=-1&isIgnorePin=false&auctionState=-1&reconstructionStep=0&reconstructionStepFrom=1&reconstructionStepTo=10&r=45138")

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 에러가 발생하면 예외를 발생시킴

        response_data = response.json()

        pretty_json = json.dumps(response_data, indent=4, ensure_ascii=False)
        print(pretty_json)

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



if __name__ == "__main__":
    main()
