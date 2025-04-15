import os
import time
from datetime import datetime

import psutil
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# 현재 시간 반환 함수

# 전역 변수
# SELECT_URL = "https://주식회사비전.com/user/place/rest/select-currentrank"
# UPDATE_URL = "https://주식회사비전.com/user/place/rest/update-currentrank"

UPDATE_URL = "http://localhost/user/place/rest/update-currentrank"
SELECT_URL = "http://localhost/user/place/rest/select-currentrank"


# 드라이버 설정
def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # 서버 실행 시 필요

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    driver.set_window_position(0, 0)
    driver.set_window_size(1000, 1000)
    return driver

    # 크롬 끄기


def _close_chrome_processes():
    """모든 Chrome 프로세스를 종료합니다."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()  # Chrome 프로세스를 종료O
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def set_chrome_driver_user():
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
        print(f'WebDriverException error {e}')
        return None


def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def update_obj_list(obj_list):
    response = requests.put(UPDATE_URL, json=obj_list)

    # 상태 코드 출력
    print(f"HTTP 상태 코드: {response.status_code}")

    if response.status_code == 200:
        try:
            json_data = response.text
            print("성공적으로 업데이트되었습니다.")
            print("응답 데이터:", json_data)
        except requests.exceptions.JSONDecodeError:
            print("JSON 파싱 오류: 응답 데이터가 JSON 형식이 아닙니다.")
            print("응답 데이터 (원본):", response.text)
    else:
        print("업데이트 실패:", response.status_code)
        print("응답 데이터:", response.text)


def get_current_rank():
    try:
        response = requests.get(SELECT_URL)
        response.raise_for_status()  # 에러 코드면 예외 발생
        data = response.json()
        print(f"{get_current_time()} ✅ 응답 수신 성공")
        return data

    except requests.exceptions.RequestException as e:
        print(f"{get_current_time()} ⚠ 요청 실패: {e}")
    except ValueError as e:
        print(f"{get_current_time()} ⚠ JSON 파싱 실패: {e}")


def wait_for_iframe_and_switch(driver, timeout=60):
    """iframe과 내부 요소가 모두 로드될 때까지 기다림"""
    for i in range(timeout):
        try:
            iframe = driver.find_element(By.ID, "searchIframe")
            driver.switch_to.frame(iframe)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#_pcmap_list_scroll_container'))
            )
            return True
        except:
            time.sleep(1)
    return False


def scroll_slowly_to_bottom(driver, obj):
    try:
        driver.switch_to.default_content()

        if not wait_for_iframe_and_switch(driver):
            print(f"{get_current_time()} ❌ iframe 로딩 실패 - '{obj.get('businessName', '')}'")
            driver.switch_to.default_content()  # ✅ 다음 키워드를 위해 초기화
            return obj['currentRank']

        scrollable_div_selector = 'div#_pcmap_list_scroll_container'
        target_name = obj.get('businessName', '').strip()
        business_names = []

        page_num = 1  # <-- 초기값 설정

        while True:
            try:
                scrollable_div = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_div_selector))
                )
            except TimeoutException:
                try:
                    no_result_div = driver.find_element(By.CLASS_NAME, "FYvSc")
                    if no_result_div.text == "조건에 맞는 업체가 없습니다.":
                        print("조건에 맞는 업체가 없습니다.")
                        print(f"{get_current_time()} ✅ '{target_name}'의 위치: 999 번째")
                except Exception:
                    pass
                return 999

            ActionChains(driver).move_to_element(scrollable_div).perform()
            time.sleep(1)

            prev_height = -1
            no_change_count = 0

            # 페이지에 맞는 순위 계산
            result = real_time_rank(driver, scrollable_div, business_names, target_name, page_num)
            if result:
                print(f"{get_current_time()} 📌 현재까지 누적된 사업장 수: {len(business_names)}")
                return result  # 찾았으면 바로 종료

            # 스크롤 끝까지 내리기
            while True:
                # 한 번에 끝까지 스크롤
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_div)
                time.sleep(0.3)  # 약간의 대기 시간 (렌더링 여유)

                # 스크롤이 더 이상 내려가지 않는 경우 종료
                current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                max_scroll_height = driver.execute_script(
                    "return arguments[0].scrollHeight - arguments[0].clientHeight;", scrollable_div
                )
                if current_scroll >= max_scroll_height - 5:
                    print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                    break

            result = real_time_rank(driver, scrollable_div, business_names, target_name, page_num)
            if result:
                print(f"{get_current_time()} 📌 현재까지 누적된 사업장 목록: {len(business_names)}")
                return result  # 찾았으면 종료


            print(f"{get_current_time()} 📌 현재까지 누적된 사업장 목록: {len(business_names)}")

            # 다음 페이지로 이동 가능한지 체크
            try:
                pages = driver.find_elements(By.CSS_SELECTOR, "div.zRM9F > a.mBN2s")
                current_page_index = -1

                for idx, page in enumerate(pages):
                    classes = page.get_attribute('class')
                    if 'qxokY' in classes:
                        current_page_index = idx
                        break

                if current_page_index == -1:
                    print(f"{get_current_time()} ⚠ 현재 페이지를 찾을 수 없습니다.")
                    break

                if current_page_index + 1 < len(pages):
                    next_page_button = pages[current_page_index + 1]
                    driver.execute_script("arguments[0].click();", next_page_button)
                    print(f"{get_current_time()} 📄 다음 페이지 ({current_page_index + 2})로 이동합니다.")
                    time.sleep(2)
                    page_num += 1  # ✅ 페이지 수 증가
                else:
                    next_group_button = driver.find_element(By.CSS_SELECTOR,
                                                            "div.zRM9F > a.eUTV2[aria-disabled='false']:last-child")
                    driver.execute_script("arguments[0].click();", next_group_button)
                    print(f"{get_current_time()} 📄 다음 페이지 그룹으로 이동합니다.")
                    time.sleep(2)
                    page_num += 1  # ✅ 그룹 이동 후에도 증가

            except Exception:
                print(f"{get_current_time()} ⛔️ 다음 페이지가 없습니다")
                break

        # 마지막까지 못 찾은 경우
        last_position = len(business_names) + 1  # 꼴등 처리
        print(f"{get_current_time()} ⚠ '{target_name}'을(를) 찾지 못했습니다. 꼴등 처리 위치: {last_position}")
        driver.switch_to.default_content()
        return last_position

    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 스크롤 중 오류: {e}")
        return obj['currentRank']


def real_time_rank(driver, scrollable_div, business_names, target_name, page):
    li_elements = scrollable_div.find_elements(By.CSS_SELECTOR, 'ul > li')

    # 페이지당 70개씩 가정
    start_num = len(business_names) - ((page - 1) * 70)

    for index, li in enumerate(li_elements[start_num:], start=start_num):
        try:
            ad_elements = li.find_elements(By.CSS_SELECTOR, 'span.place_blind')
            if any(ad.text.strip() == '광고' for ad in ad_elements):
                continue

            # 'span.TYaxT', 'span.YwYLL', 'span.t3s7S', 'span.CMy2_', 'span.O_Uah'
            try:
                bluelink_div = li.find_element(By.CLASS_NAME, 'place_bluelink')
                span_elements = bluelink_div.find_elements(By.TAG_NAME, 'span')
                name_element = span_elements[0] if span_elements else None
            except:
                name_element = None

            if name_element:
                business_name = name_element.text.strip()
                if business_name and business_name not in business_names:
                    business_names.append(business_name)

            if target_name in business_names:
                matched_index = business_names.index(target_name)
                print(f"{get_current_time()} ✅ '{target_name}'의 위치: {matched_index + 1}번째")
                driver.switch_to.default_content()
                return matched_index + 1

        except Exception as e:
            print(f"⚠️ 요소 처리 중 오류 발생: {e}")
            continue
    return None


def naver_cralwing():
    chrome_driver = setup_chrome_driver()
    chrome_driver.get("https://map.naver.com")
    try:

        time.sleep(2)  # 페이지 로딩 대기

        # 2. 현재 순위 가져오기
        obj_list = get_current_rank()

        print(f'obj_list len : {len(obj_list)}')

        for index, obj in enumerate(obj_list, start=1):
            print(f'■ 현재 위치 {index}/{len(obj_list)}, 최초현재 순위 {obj['currentRank']} ========================')
            if obj.get("crawlYn") == 'N':
                continue

            keyword = obj.get("keyword")
            businessName = obj.get("businessName")
            print(f"{get_current_time()} 🔍 검색 키워드: {keyword}, 상호명: {businessName}")

            # 3. 검색창 찾기 및 키워드 입력
            try:

                chrome_driver.switch_to.default_content()

                search_input = WebDriverWait(chrome_driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
                )

                # 확실한 초기화 방법: clear() 후 backspace/delete 키 반복 전송
                search_input.click()
                search_input.clear()

                # 기존 내용을 완벽히 지우기 위한 확실한 조작 추가
                search_input.send_keys(Keys.CONTROL + "a")  # Ctrl + A 전체 선택
                search_input.send_keys(Keys.DELETE)  # Delete 키 눌러서 삭제
                time.sleep(0.3)

                search_input.send_keys(keyword)
                time.sleep(0.5)

                # 4. 검색 버튼 클릭
                # Enter 키를 눌러 검색 실행
                search_input.send_keys(Keys.ENTER)

                time.sleep(3)  # 검색 결과 대기 (필요 시 더 조절)

                current_rank = scroll_slowly_to_bottom(chrome_driver, obj)
                #obj['currentRank'] = current_rank
                obj['recentRank'] = obj['currentRank']
                obj['rankChkDt'] = get_current_time()

                if obj['correctYn'] == 'N':
                    # 보정이 안된 데이터인데 현재 순위가 다르면 보정
                    if int(obj.get("currentRank")) != int(current_rank):
                        obj['correctYn'] = 'Y'
                        obj['highestRank'] = current_rank
                        obj['initialRank'] = current_rank
                        obj['highestDt'] = get_current_time()
                        print(f'보정됨')
                else:
                    if int(obj.get("highestRank")) >= int(current_rank):
                        obj['highestRank'] = current_rank
                        obj['highestDt'] = get_current_time()

                obj['currentRank'] =current_rank
                print(obj)
                print(f'■ 끝 현재 위치 {index}/{len(obj_list)}, 현재 순위 {obj['currentRank']} ========================\n\n')

            except Exception as e:
                print(f"{get_current_time()} ⚠ [ERROR] 키워드 '{keyword}' 검색 중 오류 발생: {e}")

        update_obj_list(obj_list)
        chrome_driver.quit()

    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 크롤링 중 오류 발생: {e}")


# 실행 (메인 루프)
if __name__ == "__main__":

    naver_cralwing()
    print(f"{get_current_time()} 순위 보정 프로그램 정상 시작 완료!!!")

    # 매일 04:00에 test() 실행
    # schedule.every().day.at("04:00").do(naver_cralwing)

    # 1초마다 실행시간이 도래 했는지 확인
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
