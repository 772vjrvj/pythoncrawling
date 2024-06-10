from datetime import datetime
import time
import pytz

import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# 전역 변수로 드라이버 선언
driver = None
main_start_time = ""
main_end_time = ""
main_total_time = ""

start_time = ""
end_time = ""
total_time = ""

def init_driver():
    global driver
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")  # Headless 모드에서 브라우저 크기 설정

    # 추가적인 헤드리스 모드 안정화 옵션
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def close_driver():
    global driver
    if driver:
        driver.quit()

def get_marker_ids(place, category):
    global driver
    # URL 구성
    print(f"URL 구성: https://map.naver.com/v5/search/{place}%20{category}")
    url = f"https://map.naver.com/v5/search/{place}%20{category}"

    # URL로 이동
    print(f"URL로 이동: {url}")
    driver.get(url)

    all_ids = []

    try:
        # 첫 페이지에서 id 가져오기
        print("첫 페이지에서 id 가져오기")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id^="salt-search-marker-"]')))
        elements = driver.find_elements(By.CSS_SELECTOR, '[id^="salt-search-marker-"]')
        all_ids.extend([re.search(r'salt-search-marker-(\d+)', element.get_attribute('id')).group(1) for element in elements])
        print(f"첫 페이지에서 가져온 ID len: {len(all_ids)}")

        # iframe으로 전환
        print("iframe으로 전환")
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe")))

        # 페이지 넘김 버튼 가져오기
        print("페이지 넘김 버튼 가져오기")
        page_buttons = driver.find_elements(By.CSS_SELECTOR, 'a.mBN2s')
        num_pages = len(page_buttons)
        print(f"페이지 수: {num_pages}")

        for i in range(1, num_pages):  # 첫 번째 버튼은 이미 클릭된 상태이므로 1부터 시작
            try:
                # 각 페이지 버튼을 클릭
                print(f"각 페이지 버튼을 클릭 {i}")
                page_buttons[i].click()

                time.sleep(3)

                # 최상위 컨텍스트로 전환
                print(f"최상위 컨텍스트로 전환 {i}")
                driver.switch_to.default_content()

                # 새로운 페이지가 로드될 때까지 대기
                print(f"새로운 페이지가 로드될 때까지 대기 {i}")
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id^="salt-search-marker-"]')))

                # 새로운 페이지에서 id 가져오기
                print(f"새로운 페이지에서 id 가져오기 {i}")
                elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[id^="salt-search-marker-"]')))
                all_ids.extend([re.search(r'salt-search-marker-(\d+)', element.get_attribute('id')).group(1) for element in elements])
                print(f"{i} 페이지에서 가져온 ID len: {len(all_ids)}")

                # 다시 iframe으로 전환
                print(f"다시 iframe으로 전환 {i}")
                WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe")))

                # 페이지 넘김 버튼을 다시 가져오기
                print(f"페이지 넘김 버튼을 다시 가져오기 {i}")
                page_buttons = driver.find_elements(By.CSS_SELECTOR, 'a.mBN2s')
                print(f"페이지 끝 {i}")
            except NoSuchElementException:
                print(f"No elements found on page {i+1}")
                break
            except TimeoutException:
                print(f"Timed out waiting for page {i+1} to load")
                break
            except StaleElementReferenceException:
                print("Stale element reference exception caught. Retrying...")
                break

        return all_ids

    except Exception as e:
        print(f"Error during marker ID retrieval: {e}")
        return all_ids

def get_marker_details(marker_id, category):
    global driver
    url = f"https://m.place.naver.com/place/{marker_id}/home?entry=pll"

    details = {
        "구분번호": marker_id,
        "상호명": "",
        "카테고리": category,
        "시": "",
        "구": "",
        "주소": "",
        "전화번호": "",
        "인스타": "",
        "홈페이지": "",
        "블로그": "",
        "카카오": "",
        "페이스북": "",
        "유튜브": "",
        "네이버 플레이스": url
    }

    try:
        driver.get(url)
        time.sleep(1.2)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.GHAhO')))
        details["상호명"] = driver.find_element(By.CSS_SELECTOR, 'span.GHAhO').text
        juso = driver.find_element(By.CSS_SELECTOR, 'span.LDgIH').text
        details["주소"] = juso
        # 띄어쓰기로 주소를 자르기
        split_juso = juso.split()

        if split_juso[0] == '경기':
            details["시"] = split_juso[1]
            details["구"] = split_juso[2]
        else:
            details["시"] = split_juso[0]
            details["구"] = split_juso[1]

        details["전화번호"] = driver.find_element(By.CSS_SELECTOR, 'span.xlx7Q').text

        spans = driver.find_elements(By.CSS_SELECTOR, 'span.jO09N, span.S8peq')

        for span in spans:
            link = span.find_element(By.TAG_NAME, 'a')
            href = link.get_attribute('href')
            if 'instagram' in href:
                details["인스타"] = href
            elif 'blog' in href:
                details["블로그"] = href
            elif 'facebook' in href:
                details["페이스북"] = href
            elif 'kakao' in href:
                details["카카오"] = href
            elif 'youtube' in href:
                details["유튜브"] = href
            elif 'cafe' in href:
                details["카페"] = href
            elif '.naver.' not in href and href:
                details["홈페이지"] = href

        # 인스타, 블로그, 홈페이지 중 하나라도 없으면 details를 추가하지 않음
        if not details["인스타"] and not details["블로그"] and not details["홈페이지"]:
            print(f"Skipping marker ID: {marker_id} as it lacks Instagram, Blog, and Homepage")
            return None

        print(f"details {details}")
    except NoSuchElementException:
        print(f"Element not found for marker ID: {marker_id}")
    except TimeoutException:
        print(f"Timed out waiting for details of marker ID: {marker_id}")

    return details

def get_current_time():
    # 한국 시간대 정의
    korea_tz = pytz.timezone('Asia/Seoul')

    # 현재 시간을 UTC 기준으로 가져오기
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # 한국 시간으로 변환
    now_korea = now_utc.astimezone(korea_tz)

    # 시간을 "yyyy-mm-dd hh:mm:ss" 형식으로 포맷팅
    formatted_time_korea = now_korea.strftime('%Y-%m-%d %H:%M:%S')
    print(formatted_time_korea)

def main():
    init_driver()
    cities = "서울"
    places = [
        {"city": "서울", "gu": "강남구"}, {"city": "서울", "gu": "서초구"},
        {"city": "서울", "gu": "송파구"}, {"city": "서울", "gu": "강북구"},
        {"city": "서울", "gu": "용산구"}, {"city": "서울", "gu": "강동구"},
        {"city": "서울", "gu": "마포구"}, {"city": "서울", "gu": "중랑구"},
        {"city": "서울", "gu": "은평구"}, {"city": "서울", "gu": "관악구"},
        {"city": "서울", "gu": "금천구"}, {"city": "서울", "gu": "구로구"},
        {"city": "서울", "gu": "광진구"}, {"city": "서울", "gu": "노원구"},
        {"city": "서울", "gu": "도봉구"}, {"city": "서울", "gu": "동대문구"},
        {"city": "서울", "gu": "동작구"}, {"city": "서울", "gu": "서대문구"},
        {"city": "서울", "gu": "성동구"}, {"city": "서울", "gu": "성북구"},
        {"city": "서울", "gu": "양천구"}, {"city": "서울", "gu": "영등포구"},
        {"city": "서울", "gu": "종로구"}, {"city": "서울", "gu": "중구"},
        {"city": "용인시", "gu": "처인구"}, {"city": "용인시", "gu": "기흥구"},
        {"city": "용인시", "gu": "수지구"}, {"city": "수원시", "gu": "장안구"},
        {"city": "수원시", "gu": "권선구"}, {"city": "수원시", "gu": "팔달구"},
        {"city": "수원시", "gu": "영통구"}, {"city": "성남시", "gu": "수정구"},
        {"city": "성남시", "gu": "중원구"}, {"city": "성남시", "gu": "분당구"},
        {"city": "고양시", "gu": "덕양구"}, {"city": "고양시", "gu": "일산동구"},
        {"city": "고양시", "gu": "일산서구"}, {"city": "부천시", "gu": "원미구"},
        {"city": "부천시", "gu": "소사구"}, {"city": "부천시", "gu": "오정구"},
        {"city": "인천시", "gu": "중구"}, {"city": "인천시", "gu": "동구"},
        {"city": "인천시", "gu": "미추홀구"}, {"city": "인천시", "gu": "연수구"},
        {"city": "인천시", "gu": "남동구"}, {"city": "인천시", "gu": "부평구"},
        {"city": "인천시", "gu": "계양구"}, {"city": "인천시", "gu": "서구"},
        {"city": "인천시", "gu": "강화군"}, {"city": "인천시", "gu": "옹진군"}
    ]


    categories = ["발레"]
    all_details = []
    all_unique_marker_ids = set()

    for category in categories:
        category_unique_marker_ids = set()

        for pc in places:

            place = pc["gu"]

            if len(category_unique_marker_ids) >= 1800:
                break

            print(f"======================================")
            start_time = time.time()  # 시작 시간 기록
            get_current_time()

            print(f"Place: {place}, Category: {category}")
            marker_ids = get_marker_ids(place, category)

            unique_marker_ids = set(marker_ids)
            unique_marker_ids = unique_marker_ids - all_unique_marker_ids  # 전체에서 중복 제거
            unique_marker_ids = unique_marker_ids - category_unique_marker_ids  # 현재 카테고리에서 중복 제거
            category_unique_marker_ids.update(unique_marker_ids)

            print(f"Total unique marker IDs in {place} for {category}: {len(category_unique_marker_ids)}")

            end_time = time.time()  # 종료 시간 기록
            total_time = end_time - start_time  # 총 걸린 시간 계산
            print(f"아이디 수집 단위 걸린시간: {total_time} 초")

            total_time = end_time - main_start_time  # 총 걸린 시간 계산
            print(f"아이디 수집 현재까지 걸린시간: {total_time} 초")

            get_current_time()
            print(f"======================================")

            if len(category_unique_marker_ids) >= 1800:
                category_unique_marker_ids = set(list(category_unique_marker_ids)[:1800])  # 2000개로 제한

        all_unique_marker_ids.update(category_unique_marker_ids)

        print(f"======================================")
        start_time = time.time()  # 시작 시간 기록
        get_current_time()

        for index, marker_id in enumerate(category_unique_marker_ids):
            print(f"Index: {index}, Marker ID: {marker_id}")
            details = get_marker_details(marker_id, category)
            all_details.append(details)

        end_time = time.time()  # 종료 시간 기록
        total_time = end_time - start_time  # 총 걸린 시간 계산
        print(f"실제데이터 수집 단위 걸린시간: {total_time} 초")

        total_time = end_time - main_start_time  # 총 걸린 시간 계산
        print(f"실제데이터 수집 현재까지 걸린시간: {total_time} 초")

        get_current_time()
        print(f"======================================")



    df = pd.DataFrame(all_details)
    df.to_excel("marker_details.xlsx", index=False)

    print("Excel file has been created with the marker details.")

    close_driver()

if __name__ == "__main__":
    main_start_time = time.time()  # 시작 시간 기록
    get_current_time()

    main()

    main_end_time = time.time()  # 종료 시간 기록
    get_current_time()

    main_total_time = main_end_time - main_start_time  # 총 걸린 시간 계산
    print(f"전체 걸린시간: {main_total_time} 초")
