from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import math
import csv
import os

def setup_driver():
    """
    Headless 모드로 실행하고, 화면을 꽉 차게 설정하는 Selenium 웹 드라이버 설정 함수
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 헤드리스 모드
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # 화면 꽉 차게 설정

    # 사용자 에이전트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 탐지 방지 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    return driver


def get_ctgrycd_values():
    """
    지정된 URL에서 class="title font-heading-2" 요소의 ctgrycd 속성 값과 텍스트를 추출하는 함수
    """
    url = "https://buykorea.org/ec/prd/category/selectAllCtgryList.do"
    driver = setup_driver()
    try:
        driver.get(url)

        # 해당 요소가 로드될 때까지 대기 (최대 10초)
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h2.title.font-heading-2"))
        )

        # ctgrycd 속성 값 및 텍스트 추출
        category_list = [
            {"ctgrycd": element.get_attribute("ctgrycd"), "ctgry_name": element.text}
            for element in elements if element.get_attribute("ctgrycd")
        ]
    except Exception as e:
        print(f"에러 발생: {e}")
        category_list = []
    finally:
        driver.quit()

    return category_list


def fetch_goods_list(ctgryCd, levelVal, upperCtgryCd="00", lastCtgryYn="N", rows=300):
    """
    주어진 카테고리 코드를 사용하여 모든 페이지의 goodsList를 수집하는 함수
    """
    url = "https://buykorea.org/ec/prd/ajax/selectCtgryGoodsList.do"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://buykorea.org",
        "referer": f"https://buykorea.org/ec/prd/category/selectGoodsList.do?ctgryCd={ctgryCd}&levelVal={levelVal}",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    # 첫 페이지 요청
    payload = {
        "ctgryCd": ctgryCd,
        "levelVal": levelVal,
        "upperCtgryCd": upperCtgryCd,
        "lastCtgryYn": lastCtgryYn,
        "rows": rows,
        "unitType": "horizon",
        "page": 1,
        "totalRows": 0,
        "array": "Newest",
        "priceMin": -1,
        "priceMax": -1
    }

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code != 200:
        print(f"요청 실패: {response.status_code}")
        return []

    data = response.json()
    if data.get("resultCd") != "0000":
        print(f"API 오류: {data.get('resultCd')}")
        return []

    total_rows = data["body"]["pageMap"]["totalRows"]
    last_page = math.ceil(total_rows / rows)  # 전체 페이지 계산
    goods_list = data["body"]["goodsList"]

    print(f"총 {total_rows}개의 데이터, {last_page} 페이지 수집 중...")

    # 나머지 페이지 요청
    for page in range(2, last_page + 1):
        time.sleep(1)
        payload["page"] = page
        print(f'page : {page} 시작')
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            page_data = response.json()
            # print(f'page : {page}, goodsList :{page_data["body"]["goodsList"]}')
            print(f'page : {page} 성공')
            goods_list.extend(page_data.get("body", {}).get("goodsList", []))
        else:
            print(f"{page} 페이지 요청 실패: {response.status_code}")

    return goods_list


def save_goods_list_to_csv(goods_list, filename="goods_list.csv"):
    """
    수집된 goods_list 데이터를 'ctgrycd' 폴더에 저장하는 함수
    """
    if not goods_list:
        print("저장할 데이터가 없습니다.")
        return

    save_path = os.path.join(os.getcwd(), "ctgrycd")  # 'ctgrycd' 폴더 경로 설정
    os.makedirs(save_path, exist_ok=True)  # 폴더 없으면 생성

    file_path = os.path.join(save_path, filename)  # 파일 저장 경로 설정

    keys = goods_list[0].keys()  # CSV 헤더 생성
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(goods_list)

    print(f"{file_path} 파일로 저장 완료.")



if __name__ == "__main__":
    # ctgrycd_list = get_ctgrycd_values()
    # print(ctgrycd_list)

    ctgrycd_list = [
        # {'ctgrycd': '001000000000', 'ctgry_name': 'Life & Health'},
        # {'ctgrycd': '002000000000', 'ctgry_name': 'Furniture & Home Decor'},
        {'ctgrycd': '003000000000', 'ctgry_name': 'Beauty'},
        # {'ctgrycd': '004000000000', 'ctgry_name': 'Sports, Toys & Hobbies'},
        # {'ctgrycd': '005000000000', 'ctgry_name': 'Fashion'},
        # {'ctgrycd': '006000000000', 'ctgry_name': 'Food, Beverage & Agriculture'},
        # {'ctgrycd': '008000000000', 'ctgry_name': 'ICT'},
        # {'ctgrycd': '009000000000', 'ctgry_name': 'Home Appliances, Electrical & Electronic Components'},
        # {'ctgrycd': '010000000000', 'ctgry_name': 'Construction Equipment & Material'},
        # {'ctgrycd': '011000000000', 'ctgry_name': 'Machinery & Heavy Equipment'},
        # {'ctgrycd': '012000000000', 'ctgry_name': 'Basic Material'},
        # {'ctgrycd': '013000000000', 'ctgry_name': 'Others'},
        # {'ctgrycd': '014000000000', 'ctgry_name': 'Medical Equipment'},
        # {'ctgrycd': '015000000000', 'ctgry_name': 'Automotive Parts'},
        # {'ctgrycd': '016000000000', 'ctgry_name': 'Plant, Power & Equipment'},
        # {'ctgrycd': '017000000000', 'ctgry_name': 'Medicine & Medical Supplies'},
        # {'ctgrycd': '018000000000', 'ctgry_name': 'Marine Equipment'},
        # {'ctgrycd': '019000000000', 'ctgry_name': 'Aerospace Parts'},
        # {'ctgrycd': '020000000000', 'ctgry_name': 'Service'}
    ]

    for category in ctgrycd_list:
        ctgrycd = category["ctgrycd"]
        goods_data = fetch_goods_list(ctgrycd, 1)
        save_goods_list_to_csv(goods_data, filename=f"{ctgrycd}.csv")


