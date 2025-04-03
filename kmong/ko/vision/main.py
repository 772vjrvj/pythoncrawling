import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import schedule
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from datetime import datetime


# 현재 시간 반환 함수

# 전역 변수
SELECT_URL = "https://주식회사비전.com/user/place/rest/select-currentrank"
UPDATE_URL = "https://주식회사비전.com/user/place/rest/update-currentrank"

# UPDATE_URL = "http://localhost/user/place/rest/update-currentrank"
# SELECT_URL = "http://localhost/user/place/rest/select-currentrank"


# 드라이버 설정
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # 서버 실행 시 필요

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
        params = {
            'type': 'currentRank'
        }
        response = requests.get(SELECT_URL, params=params)

        print(f"📡 상태 코드: {response.status_code}")
        print(f"📄 응답 본문:\n{response.text}")

        response.raise_for_status()  # 에러 코드면 예외 발생

        data = response.json()
        print(f"{get_current_time()} ✅ 응답 수신 성공")
        return data

    except requests.exceptions.RequestException as e:
        print(f"{get_current_time()} ⚠ 요청 실패: {e}")
    except ValueError as e:
        print(f"{get_current_time()} ⚠ JSON 파싱 실패: {e}")



def scroll_slowly_to_bottom(driver, obj):
    try:
        driver.switch_to.default_content()

        # 최초 iframe 진입 (한 번만!)
        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe"))
        )

        scrollable_div_selector = 'div#_pcmap_list_scroll_container'
        target_name = obj.get('businessName', '').strip()
        business_names = []

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
                except Exception:
                    pass
                return 999

            ActionChains(driver).move_to_element(scrollable_div).perform()
            time.sleep(1)

            prev_height = -1
            no_change_count = 0

            # 스크롤 끝까지 내리기
            while True:
                for _ in range(7):
                    driver.execute_script("arguments[0].scrollTop += 150;", scrollable_div)
                    time.sleep(0.3)

                time.sleep(1)

                current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                max_scroll_height = driver.execute_script(
                    "return arguments[0].scrollHeight - arguments[0].clientHeight;", scrollable_div
                )
                if current_scroll >= max_scroll_height:
                    print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                    break

                # if current_scroll >= max_scroll_height:
                #     if prev_height == max_scroll_height:
                #         no_change_count += 1
                #     else:
                #         no_change_count = 0
                #
                #     if no_change_count >= 3:
                #         print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                #         break
                #
                #     prev_height = max_scroll_height
                # else:
                #     prev_height = max_scroll_height

            # 현재 페이지에서 사업장 이름 추출
            li_elements = scrollable_div.find_elements(By.CSS_SELECTOR, 'ul > li')
            for li in li_elements:
                try:
                    # 광고 요소는 건너뛰기
                    ad_elements = li.find_elements(By.CSS_SELECTOR, 'span.place_blind')
                    if any(ad.text.strip() == '광고' for ad in ad_elements):
                        continue  # 광고면 건너뛰기

                    # 세 가지 클래스 중 먼저 발견되는 것으로 이름 가져오기
                    name_element = None
                    for cls in ['span.TYaxT', 'span.YwYLL', 'span.t3s7S', 'span.CMy2_']:
                        try:
                            name_element = li.find_element(By.CSS_SELECTOR, cls)
                            if name_element:
                                break
                        except:
                            continue

                    if name_element:
                        business_name = name_element.text.strip()
                        if business_name and business_name not in business_names:
                            business_names.append(business_name)

                except Exception as e:
                    print(f"⚠️ 요소 처리 중 오류 발생: {e}")
                    continue

            print(f"{get_current_time()} 📌 현재까지 누적된 사업장 목록: {business_names}")

            # 타겟 이름이 있는지 확인
            if target_name in business_names:
                matched_index = business_names.index(target_name)
                print(f"{get_current_time()} ✅ '{target_name}'의 위치: {matched_index + 1}번째")
                driver.switch_to.default_content()
                return matched_index + 1

            # 다음 페이지로 이동 가능한지 체크
            try:
                # 현재 페이지 확인
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

                # 다음 페이지가 존재하는지 확인
                if current_page_index + 1 < len(pages):
                    next_page_button = pages[current_page_index + 1]
                    driver.execute_script("arguments[0].click();", next_page_button)
                    print(f"{get_current_time()} 📄 다음 페이지 ({current_page_index + 2})로 이동합니다.")
                    time.sleep(3)  # 페이지 로딩 대기
                else:
                    # 다음 페이지 그룹으로 이동 가능한지 체크 (마지막 '>' 버튼)
                    next_group_button = driver.find_element(By.CSS_SELECTOR,
                                                            "div.zRM9F > a.eUTV2[aria-disabled='false']:last-child")
                    driver.execute_script("arguments[0].click();", next_group_button)
                    print(f"{get_current_time()} 📄 다음 페이지 그룹으로 이동합니다.")
                    time.sleep(3)  # 페이지 로딩 대기

            except Exception:
                # 다음 페이지가 없으면 종료
                print(f"{get_current_time()} ⛔️ 다음 페이지가 없습니다")
                break

        # 마지막까지 못 찾은 경우
        last_position = len(business_names) + 1  # 꼴등 처리
        print(f"{get_current_time()} ⚠ '{target_name}'을(를) 찾지 못했습니다. 꼴등 처리 위치: {last_position}")
        driver.switch_to.default_content()
        return last_position

    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 스크롤 중 오류: {e}")



def naver_cralwing():
    driver = setup_driver()
    driver.get("https://map.naver.com")
    try:

        time.sleep(2)  # 페이지 로딩 대기

        # 2. 현재 순위 가져오기
        obj_list = get_current_rank()

        for obj in obj_list:

            if obj.get("crawlYn") == 'N':
                continue

            keyword = obj.get("keyword")
            print(f"{get_current_time()} 🔍 검색 키워드: {keyword}")

            # 3. 검색창 찾기 및 키워드 입력
            try:

                driver.switch_to.default_content()

                search_input = WebDriverWait(driver, 10).until(
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

                current_rank = scroll_slowly_to_bottom(driver, obj)
                obj['currentRank'] = current_rank
                obj['recentRank'] = current_rank
                obj['rankChkDt'] = get_current_time()

                if obj['correctYn'] == 'N':
                    # 보정이 안된 데이터인데 현재 순위가 다르면 보정
                    if int(obj.get("currentRank")) != int(current_rank):
                        obj['correctYn'] = 'Y'
                        obj['highestRank'] = current_rank
                        obj['initialRank'] = current_rank
                        obj['highestDt'] = get_current_time()
                else:
                    if int(obj.get("highestRank")) >= int(current_rank):
                        obj['highestRank'] = current_rank
                        obj['highestDt'] = get_current_time()

            except Exception as e:
                print(f"{get_current_time()} ⚠ [ERROR] 키워드 '{keyword}' 검색 중 오류 발생: {e}")

        update_obj_list(obj_list)

    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 크롤링 중 오류 발생: {e}")


# 실행 (메인 루프)
if __name__ == "__main__":

    naver_cralwing()
    print(f"{get_current_time()} 순위 보정 프로그램 정상 시작 완료!!!")

    # 매일 04:00에 test() 실행
    schedule.every().day.at("04:16").do(naver_cralwing)

    # 1초마다 실행시간이 도래 했는지 확인
    while True:
        schedule.run_pending()
        time.sleep(1)
