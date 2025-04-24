import os
import time
from datetime import datetime
import schedule
import psutil
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


# 전역 변수
SELECT_URL = "https://주식회사비전.com/user/place/rest/select-currentrank"
UPDATE_URL = "https://주식회사비전.com/user/place/rest/update-currentrank"


# UPDATE_URL = "http://localhost/user/place/rest/update-currentrank"
# SELECT_URL = "http://localhost/user/place/rest/select-currentrank"


edge_driver = None
chrome_driver = None


def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _close_browser_processes():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if 'chrome' in name or 'msedge' in name or 'edge' in name:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def setup_chrome_driver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

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
        print(f'WebDriverException error {e}')
        return None


def setup_edge_driver():
    edge_options = EdgeOptions()
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--headless")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    edge_options.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=edge_options)
    driver.set_window_position(0, 0)
    driver.set_window_size(1000, 1000)
    return driver


def get_current_rank(type):
    try:
        params = {
            'type': type
        }
        response = requests.get(SELECT_URL, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"{get_current_time()} ✅ 응답 수신 성공")
        return data
    except requests.exceptions.RequestException as e:
        print(f"{get_current_time()} ⚠ 요청 실패: {e}")
    except ValueError as e:
        print(f"{get_current_time()} ⚠ JSON 파싱 실패: {e}")


def update_obj_list(obj_list):
    response = requests.put(UPDATE_URL, json=obj_list)
    print(f"HTTP 상태 코드: {response.status_code}")
    if response.status_code == 200:
        print("성공적으로 업데이트되었습니다.")
        print("응답 데이터:", response.text)
    else:
        print("업데이트 실패:", response.status_code)
        print("응답 데이터:", response.text)

# iframe 변경
def wait_for_iframe_and_switch(driver, timeout=60):
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

# 검색 키워드 입력
def search_keyword_on_map(driver, obj):
    try:
        chrome_driver.switch_to.default_content()

        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
        )
        search_input.click()
        search_input.clear()
        search_input.send_keys(Keys.CONTROL + "a")
        search_input.send_keys(Keys.DELETE)
        time.sleep(0.3)
        search_input.send_keys(obj.get("keyword"))
        time.sleep(0.5)
        search_input.send_keys(Keys.ENTER)
        time.sleep(2.5)
        return True
    except Exception as e:
        print(f"{get_current_time()} ⚠ 검색창 오류: {e}")
        return False


def scroll_slowly_to_bottom(driver, obj, driver_type="chrome"):
    try:
        driver.switch_to.default_content()
        if not wait_for_iframe_and_switch(driver):
            print(f"{get_current_time()} ❌ [{driver_type}] iframe 로딩 실패 - '{obj.get('businessName', '')}'")
            if driver_type == "chrome":
                global edge_driver
                if edge_driver is None:
                    edge_driver = setup_edge_driver()
                    edge_driver.get("https://map.naver.com")
                    time.sleep(2)
                if not search_keyword_on_map(edge_driver, obj):
                    return obj["currentRank"]
                return scroll_slowly_to_bottom(edge_driver, obj, driver_type="edge")
            else:
                return obj['currentRank']

        scrollable_div_selector = 'div#_pcmap_list_scroll_container'
        target_name = obj.get('businessName', '').strip()
        business_names = []
        page_num = 1

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
                        return 999
                except Exception:
                    pass
                return obj['currentRank']

            ActionChains(driver).move_to_element(scrollable_div).perform()
            time.sleep(1)

            result = real_time_rank(scrollable_div, business_names, target_name)
            if result:
                return result

            # 스크롤 가능한 컨테이너(scrollable_div)를 최하단까지 내리기 위한 반복문
            # scrollHeight: 전체 스크롤 영역의 높이
            # clientHeight: 현재 보이는 영역의 높이
            # scrollTop: 현재 스크롤 위치
            # scrollTop이 scrollHeight - clientHeight에 근접하면 스크롤이 끝까지 내려간 것으로 판단

            # 스크롤 끝까지 내리기
            while True:
                for _ in range(7):
                    driver.execute_script("arguments[0].scrollTop += 250;", scrollable_div)
                    time.sleep(0.2)
                time.sleep(1)
                current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                max_scroll_height = driver.execute_script(
                    "return arguments[0].scrollHeight - arguments[0].clientHeight;", scrollable_div
                )
                if current_scroll >= max_scroll_height - 5:
                    print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                    break

            result = real_time_rank(scrollable_div, business_names, target_name)
            if result:
                return result

            try:
                pages = driver.find_elements(By.CSS_SELECTOR, "div.zRM9F > a.mBN2s")
                current_page_index = -1
                for idx, page in enumerate(pages):
                    if 'qxokY' in page.get_attribute('class'):
                        current_page_index = idx
                        break
                if current_page_index + 1 < len(pages):
                    next_page_button = pages[current_page_index + 1]
                    driver.execute_script("arguments[0].click();", next_page_button)
                    time.sleep(2)
                    page_num += 1
                else:
                    break
            except:
                break
        return len(business_names) + 1
    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 스크롤 중 오류: {e}")
        return obj['currentRank']


def real_time_rank(scrollable_div, business_names, target_name):
    li_elements = scrollable_div.find_elements(By.CSS_SELECTOR, 'ul > li')
    for index, li in enumerate(li_elements, start=0):
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
                return business_names.index(target_name) + 1
        except:
            continue
    print(f"{get_current_time()} 📌 현재까지 누적된 사업장 수: {len(business_names)}")
    return None


def naver_cralwing(type):
    print(f"\n\n\n\n\n{get_current_time()} 🔍 유형: {type}")

    global edge_driver, chrome_driver
    # _close_browser_processes()
    # chrome_driver = set_chrome_driver_user()
    chrome_driver = setup_chrome_driver()
    chrome_driver.get("https://map.naver.com")
    time.sleep(2)

    obj_list = get_current_rank(type)
    print(f"{get_current_time()} 🔍 조회 데이터 수 수: {len(obj_list)}")
    for index, obj in enumerate(obj_list, start=1):
        if obj.get("crawlYn") == 'N':
            continue
        keyword = obj.get("keyword")
        businessName = obj.get("businessName")
        print(f'■ 현재 위치 {index}/{len(obj_list)}, 최초현재 순위 {obj["currentRank"]} ========================')
        print(f"{get_current_time()} 🔍 검색 키워드: {keyword}, 상호명: {businessName}")
        try:
            if not search_keyword_on_map(chrome_driver, obj):
                continue
            current_rank = scroll_slowly_to_bottom(chrome_driver, obj, driver_type="chrome")
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
            print(obj)
            print(f'■ 끝 현재 위치 {index}/{len(obj_list)}, 현재 순위 {obj["currentRank"]} ========================\n\n')
        except Exception as e:
            print(f"{get_current_time()} ⚠ [ERROR] 키워드 '{obj.get('keyword')}' 검색 중 오류 발생: {e}")

    update_obj_list(obj_list)
    chrome_driver.quit()
    if edge_driver:
        edge_driver.quit()


def naver_cralwing_all():
    naver_cralwing('one')
    time.sleep(60)
    naver_cralwing('last')
    time.sleep(60)
    naver_cralwing('none')


if __name__ == "__main__":
    print(f"{get_current_time()} 순위 보정 프로그램 정상 시작 완료!!!")
    schedule.every().day.at("04:00").do(naver_cralwing)

    fst = True
    while True:
        if fst:
            fst = False
            print(f"{get_current_time()} 순위 보정 프로그램 while 정상 시작 완료!!!")
        schedule.run_pending()
        time.sleep(1)

