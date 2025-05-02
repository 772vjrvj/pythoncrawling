import os
import time
from datetime import datetime
import schedule
import psutil
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import ReadTimeoutError
from webdriver_manager.chrome import ChromeDriverManager
import copy

# 전역 변수
SELECT_URL = "https://주식회사비전.com/user/place/rest/select-currentrank"
UPDATE_URL = "https://주식회사비전.com/user/place/rest/update-currentrank"

# UPDATE_URL = "http://localhost/user/place/rest/update-currentrank"
# SELECT_URL = "http://localhost/user/place/rest/select-currentrank"

fail_list = []
success_list = []
eq_cnt = 0
df_cnt = 0

RESTART_INTERVAL = 50

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _close_browser_processes():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if 'chrome' in name:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def setup_chrome_driver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")  # ✅ 최신 모드
    chrome_options.add_argument("--window-size=1920,1080")  # ✅ 넉넉한 뷰포트
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    driver.set_window_position(0, 0)
    driver.set_window_size(1000, 1000)
    return driver


def set_chrome_driver_user():
    try:
        _close_browser_processes()

        chrome_options = ChromeOptions()
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

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

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
        print(f'{get_current_time()} ❌ WebDriverException error {e}')
        return None

def get_current_rank(param_type):
    try:
        params = {
            'type': param_type
        }
        response = requests.get(SELECT_URL, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"{get_current_time()} ✅ 응답 수신 성공 데이터: {data}")
        return data
    except Exception:
        print(f"{get_current_time()} ❌ 요청 실패")


def update_obj_list(obj_list):
    response = requests.put(UPDATE_URL, json=obj_list)
    print(f"HTTP 상태 코드: {response.status_code}")
    if response.status_code == 200:
        print("성공적으로 업데이트되었습니다.")
        print(f"HTTP 상태 결과: {response.text}")
    else:
        print("업데이트 실패:", response.status_code)

# iframe 변경
def wait_for_iframe_and_switch(driver, timeout=5):
    for i in range(timeout):
        try:
            iframe = driver.find_element(By.ID, "searchIframe")
            driver.switch_to.frame(iframe)
            return True
        except Exception:
            print(f"{get_current_time()} ❌ iframe 변경 에러 발생 (재시도 {i+1}/5)")
            time.sleep(1)
    return False

# 검색 키워드 입력
def search_keyword_on_map(driver, obj):
    global fail_list
    try:
        input_search_keyword(driver, obj.get("keyword"))
        return True
    except Exception as e:
        print(f"{get_current_time()} ⚠ 검색창 오류 (1차): {e}")

        try:
            print(f"{get_current_time()} 🔁 검색창 재시도: 페이지 새로고침")
            driver.get("https://map.naver.com")
            time.sleep(2)
            input_search_keyword(driver, obj.get("keyword"))
            print(f"{get_current_time()} ✅ 재시도 성공")
            return True
        except Exception as e2:
            fail_list.append(obj)
            print(f"{get_current_time()} ❌ 재시도 실패: {e2}")
            return False

def input_search_keyword(driver, keyword):
    driver.switch_to.default_content()
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
    )
    search_input.click()
    search_input.clear()
    search_input.send_keys(Keys.CONTROL + "a")
    search_input.send_keys(Keys.DELETE)
    time.sleep(0.3)
    search_input.send_keys(keyword)
    time.sleep(0.5)
    search_input.send_keys(Keys.ENTER)
    time.sleep(2.5)


def scroll_slowly_to_bottom(driver, obj):
    global fail_list
    try:
        driver.switch_to.default_content()
    except Exception as e:
        print(f"{get_current_time()} ❌ default_content 전환 실패: {e}")
        return None

    if not wait_for_iframe_and_switch(driver):
        print(f"{get_current_time()} ❌ iframe 로딩 실패 - '{obj.get('businessName', '')}'")
        return None

    scrollable_div_selector = 'div#_pcmap_list_scroll_container'
    target_name = obj.get('businessName', '').strip()
    business_names = []
    page_num = 1

    scrollable_div = ''
    while True:
        try:
            scrollable_div = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_div_selector))
            )
        except TimeoutException:
            print(f"{get_current_time()} ❌ 타임아웃 에러.")
            try:
                no_result_div = driver.find_element(By.CLASS_NAME, "FYvSc")
                if no_result_div.text == "조건에 맞는 업체가 없습니다.":
                    print("조건에 맞는 업체가 없습니다.")
                    print(f"{get_current_time()} ❌ '{target_name}'의 위치: 999 번째")
                    return 999
            except Exception:
                print(f"{get_current_time()} ❌ '{target_name}'의 위치: 999 번째 에러")
                return None

        try:
            ActionChains(driver).move_to_element(scrollable_div).perform()
        except Exception as e:
            print(f"{get_current_time()} ❌ move_to_element 에러: {e}")
            return None

        time.sleep(1)

        result = real_time_rank(scrollable_div, business_names, target_name)
        if not result:
            print(f"{get_current_time()} ❌ 순위조회 실패")
            return None
        elif result == -1:
            pass
        else:
            return result


        # 스크롤 가능한 컨테이너(scrollable_div)를 최하단까지 내리기 위한 반복문
        # scrollHeight: 전체 스크롤 영역의 높이
        # clientHeight: 현재 보이는 영역의 높이
        # scrollTop: 현재 스크롤 위치
        # scrollTop이 scrollHeight - clientHeight에 근접하면 스크롤이 끝까지 내려간 것으로 판단

        # 스크롤 끝까지 내리기
        try:
            while True:
                for _ in range(7):
                    try:
                        driver.execute_script("arguments[0].scrollTop += 250;", scrollable_div)
                    except Exception:
                        print(f"{get_current_time()} ❌ 스크롤 증가 중 에러")
                    time.sleep(0.2)
                time.sleep(1)

                try:
                    current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                    max_scroll_height = driver.execute_script(
                        "return arguments[0].scrollHeight - arguments[0].clientHeight;", scrollable_div
                    )
                except Exception:
                    print(f"{get_current_time()} ❌ 스크롤 상태 확인 중 에러")
                    return None

                if current_scroll >= max_scroll_height - 5:
                    print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                    break

        except Exception as e:
            print(f"{get_current_time()} ❌ 전체 스크롤 처리 중 예외 발생: {e}")
            return None

        result = real_time_rank(scrollable_div, business_names, target_name)
        if not result:
            print(f"{get_current_time()} ❌ 순위조회 실패")
            return None
        elif result == -1:
            pass
        else:
            return result


        try:
            pages = driver.find_elements(By.CSS_SELECTOR, "div.zRM9F > a.mBN2s")
        except Exception:
            print(f"{get_current_time()} ❌ 페이지 리스트 로딩 실패")
            return None

        current_page_index = -1
        for idx, page in enumerate(pages):
            try:
                if 'qxokY' in page.get_attribute('class'):
                    current_page_index = idx
                    break
            except Exception:
                print(f"{get_current_time()}❌ 페이지 클래스 확인 실패 (index {idx})")
                return None

        if current_page_index + 1 < len(pages):
            try:
                next_page_button = pages[current_page_index + 1]
                driver.execute_script("arguments[0].click();", next_page_button)
                time.sleep(2)
                page_num += 1
            except Exception:
                print(f"{get_current_time()} ❌ 다음 페이지 클릭 실패")
                return None
        else:
            print(f"{get_current_time()} ✅ 마지막 페이지에 도달했습니다.")
            break

    return len(business_names) + 1


def real_time_rank(scrollable_div, business_names, target_name):
    try:
        li_elements = scrollable_div.find_elements(By.CSS_SELECTOR, 'ul > li')
    except (NoSuchElementException, StaleElementReferenceException):
        print(f"{get_current_time()} ❌ ⚠ li 요소 탐색 실패")
        return None
    except Exception:
        print(f"{get_current_time()} ❌ 예기치 못한 에러 발생")
        return None

    for index, li in enumerate(li_elements, start=0):
        try:
            ad_elements = li.find_elements(By.CSS_SELECTOR, 'span.place_blind')
            if any(ad.text.strip() == '광고' for ad in ad_elements):
                continue
            # 'span.TYaxT', 'span.YwYLL', 'span.t3s7S', 'span.CMy2_', 'span.O_Uah'
            bluelink_div = li.find_element(By.CLASS_NAME, 'place_bluelink')
            span_elements = bluelink_div.find_elements(By.TAG_NAME, 'span')
            name_element = span_elements[0] if span_elements else None

            if name_element:
                business_name = name_element.text.strip()
                if business_name and business_name not in business_names:
                    business_names.append(business_name)
            if target_name in business_names:
                return business_names.index(target_name) + 1
        except:
            print(f"{get_current_time()} ❌ real_time_rank 에러")
            continue
    return -1


def naver_cralwing(obj_list):
    global fail_list, eq_cnt, df_cnt

    # _close_browser_processes()
    # driver = set_chrome_driver_user()
    driver = setup_chrome_driver()
    driver.get("https://map.naver.com")
    time.sleep(2)

    for index, obj in enumerate(obj_list, start=1):
        if index % RESTART_INTERVAL == 0:
            driver.quit()
            driver = setup_chrome_driver()
            driver.get("https://map.naver.com")
            print(f'{get_current_time()} ■ 드라이버 리셋 ========================')
            time.sleep(2)

        if obj.get("crawlYn") == 'N':
            continue

        print(f'{get_current_time()} ■ 현재 위치 {index}/{len(obj_list)}, 최초현재 순위 {obj["currentRank"]} ========================')
        print(f"{get_current_time()} 🔍 검색 키워드: {obj.get('keyword')}, 상호명: {obj.get('businessName')}")
        if not search_keyword_on_map(driver, obj):
            continue

        current_rank = scroll_slowly_to_bottom(driver, obj)

        if not current_rank:
            obj['crawlSuccessYn'] = 'N'
            fail_list.append(obj)
            continue

        rs = int(obj.get("currentRank")) == int(current_rank)
        if rs:
            rs_text = '같음'
            eq_cnt = eq_cnt + 1
        else:
            rs_text = '다름'
            df_cnt = df_cnt + 1

        obj['recentRank'] = obj['currentRank']
        obj['rankChkDt'] = get_current_time()
        if obj['correctYn'] == 'N' and int(obj.get("currentRank")) != int(current_rank):
            obj['correctYn'] = 'Y'
            obj['highestRank'] = obj['initialRank'] = current_rank
            obj['highestDt'] = get_current_time()
        elif int(obj.get("highestRank")) > int(current_rank):
            obj['highestRank'] = current_rank
            obj['highestDt'] = get_current_time()
        obj['currentRank'] = current_rank
        obj['crawlSuccessYn'] = 'Y'
        print(obj)

        print(f'{get_current_time()} ■ 끝 현재 위치 : {index}/{len(obj_list)}, 현재 순위 : {obj["currentRank"]}, 차이 : {rs_text}========================\n\n')
        success_list.append(obj)

    print(f"{get_current_time()} 작업완료(처음 수): {len(obj_list)}")
    print(f"{get_current_time()} 작업완료(성공 수): {len(success_list)}")
    print(f"{get_current_time()} 작업완료(같은 수): {eq_cnt}")
    print(f"{get_current_time()} 작업완료(다른 수): {df_cnt}")
    print(f"{get_current_time()} 작업완료(실패 수): {len(fail_list)}")
    update_obj_list(success_list)
    driver.quit()


def naver_cralwing_all():
    global fail_list, success_list, eq_cnt, df_cnt

    print(f"{get_current_time()} 1위 시작")
    obj_list = get_current_rank('one')
    naver_cralwing(obj_list)
    copy_fail_list = copy.deepcopy(fail_list)
    fail_list = []
    success_list = []
    eq_cnt = 0
    df_cnt = 0
    naver_cralwing(copy_fail_list)
    time.sleep(60)
    print(f"{get_current_time()} 1위 끝")

    print(f"{get_current_time()} 301위 시작")
    obj_list = get_current_rank('last')
    naver_cralwing(obj_list)
    copy_fail_list = copy.deepcopy(fail_list)
    fail_list = []
    success_list = []
    eq_cnt = 0
    df_cnt = 0
    naver_cralwing(copy_fail_list)
    time.sleep(60)
    print(f"{get_current_time()} 301위 끝")

    print(f"{get_current_time()} 999위 시작")
    obj_list = get_current_rank('none')
    naver_cralwing(obj_list)
    copy_fail_list = copy.deepcopy(fail_list)
    fail_list = []
    success_list = []
    eq_cnt = 0
    df_cnt = 0
    naver_cralwing(copy_fail_list)
    time.sleep(60)
    print(f"{get_current_time()} 999위 끝")

if __name__ == "__main__":

    print(f"{get_current_time()} 순위 보정 프로그램 정상 시작 완료!!!")
    schedule.every().day.at("03:30").do(naver_cralwing_all)

    fst = True
    while True:
        if fst:
            naver_cralwing_all()
            fst = False
            print(f"{get_current_time()} 순위 보정 프로그램 while 정상 시작 완료!!!")
        schedule.run_pending()
        time.sleep(1)

