from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os
import pandas as pd

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
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

def click_close_button(driver):
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.txt-blue"))  # 팝업 창 닫기 버튼의 CSS 셀렉터
        )
        driver.execute_script("arguments[0].click();", close_button)
    except Exception as e:
        print(f"Error: {e}")


def load_storage(driver, storage_file):
    if os.path.exists(storage_file + "_local_storage.json"):
        with open(storage_file + "_local_storage.json", "r") as file:
            local_storage = json.load(file)
            for key, value in local_storage.items():
                driver.execute_script(f"window.localStorage.setItem(arguments[0], arguments[1]);", key, value)
        driver.refresh()
        time.sleep(3)  # localStorage 적용 후 페이지가 로드되도록 대기
        return True
    else:
        print(f"Warning: {storage_file}_local_storage.json not found.")
        return False


def login(driver, id, pw):
    try:
        id_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "idModel"))
        )
        id_field.send_keys(id)

        pw_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pwModel"))
        )
        pw_field.send_keys(pw)

        keep_logged_in = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "logged"))
        )
        driver.execute_script("arguments[0].click();", keep_logged_in)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-login"))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(15)  # 로그인 후 대기

        # 로그인 후 localStorage 저장
        save_storage(driver, "storage_data")
    except Exception as e:
        print(f"Error: {e}")

def save_storage(driver, file_name):
    # localStorage 저장
    local_storage = driver.execute_script("return window.localStorage;")
    with open(file_name + "_local_storage.json", "w") as file:
        json.dump(local_storage, file)

def check_and_use_local_storage(driver):
    kip_device_id = driver.execute_script("return window.localStorage.getItem('kipDeviceId_772VJRVJ');")
    login_info_keep = driver.execute_script("return window.localStorage.getItem('loginInfoKeep');")
    kip_sgn_val = driver.execute_script("return window.localStorage.getItem('kipSgnVal');")

    if kip_device_id and login_info_keep == "true" and kip_sgn_val:
        print("localStorage found, attempting to use it for login...")
        driver.refresh()
        time.sleep(3)  # localStorage 적용 후 페이지가 로드되도록 대기
        return True
    else:
        print("localStorage data not found or incomplete, proceeding with new login...")
        return False



def click_company_tab(driver):
    try:
        time.sleep(2)
        # 명시적 대기를 사용하여 ul.nav 요소가 존재할 때까지 기다립니다.
        nav_ul = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.nav"))
        )
        # span 요소 중 텍스트가 '기업'을 포함하는 요소를 찾습니다.
        company_li = nav_ul.find_element(By.XPATH, ".//li/a/span[text()='기업']")
        # 요소가 가시 영역에 들어오도록 스크롤합니다.
        driver.execute_script("arguments[0].scrollIntoView();", company_li)
        # 클릭합니다.
        company_li.click()
    except Exception as e:
        print(f"Error: {e}")




def perform_search(driver, search_term):
    try:
        time.sleep(3)
        # "검색어"라는 title을 가진 입력 필드 찾기
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[title='검색어']"))
        )
        # 입력 필드 내용 초기화 (JavaScript 사용)
        driver.execute_script("arguments[0].value = '';", search_input)
        # 검색어 입력
        search_input.send_keys(search_term)

        # "검색하기"라는 title을 가진 버튼 찾기
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='검색하기']"))
        )
        search_button.click()
    except Exception as e:
        print(f"Error: {e}")




def click_general_pages(driver, address_info_list):
    try:
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".result-txt-wrap"))
        )

        for index, result in enumerate(results):
            try:
                info_obj = {"회사": "", "대표자":""}
                button = result.find_element(By.CSS_SELECTOR, ".btn.result-layer-open")
                button_text = button.text
                info_obj["회사"] = button_text

                # 명시적 대기를 사용하여 ul.search-info-list 요소가 로드될 때까지 기다림
                search_info_list = result.find_element(By.CSS_SELECTOR, "ul.search-info-list")

                # 첫 번째 li 요소 내의 class가 list-info인 요소 찾기
                list_info = search_info_list.find_element(By.CSS_SELECTOR, "li:first-child .list-info")
                # 요소의 텍스트 추출
                list_info_text = list_info.text
                info_obj["대표자"] = list_info_text
                address_info_list.append(info_obj)

            except Exception as e:
                print(f"Error in inner loop: {e}")
                return address_info_list
    except Exception as e:
        print(f"Error: {e}")
        return address_info_list
    print(f"address_info_list : {address_info_list}")
    return address_info_list


def click_general_pages_search(driver, address_info):
    try:
        time.sleep(3)

        # 명시적 대기를 사용하여 모든 btn__list 클래스 요소가 로드될 때까지 기다림
        btn_lists = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".btn__list"))
        )

        if btn_lists:
            # 첫 번째 btn__list 클래스 요소 선택
            btn_list = btn_lists[0]

            # 첫 번째 btn__list 클래스 안의 모든 li 요소 찾기
            li_elements = btn_list.find_elements(By.CSS_SELECTOR, "li")

            if len(li_elements) >= 2:
                second_li = li_elements[1]  # 두 번째 li 요소 선택
                # 두 번째 li 요소의 a 태그 찾기
                link = second_li.find_element(By.CSS_SELECTOR, "a")

                # JavaScript를 사용하여 요소 클릭
                driver.execute_script("arguments[0].click();", link)
                time.sleep(1)  # 클릭 후 대기 (필요에 따라 조정)
            else:
                print("Not enough li elements found in the first btn__list.")


            # 첫 번째 block-area 클래스 요소 내의 txt 클래스 요소의 텍스트 추출
            block_area = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".block-area .txt"))
            )
            address1 = block_area.text

            # 객체에 주소1 저장
            address_info["도로명 주소"] = address1
            print(f"도로명 주소: {address1}")

            # 페이지 스크롤을 1/5 정도 내리기
            time.sleep(2)

            # right__arrow icon20 클래스 요소의 부모 버튼 클릭
            right_arrow = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".right__arrow.icon20"))
            )
            parent_button = right_arrow.find_element(By.XPATH, "./ancestor::button")
            time.sleep(2)
            driver.execute_script("arguments[0].click();", parent_button)
            time.sleep(3)

            # address-txt 클래스 요소의 텍스트 추출
            address_txt = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".address-txt"))
            )
            address2 = address_txt.text

            # 객체에 주소2 저장
            address_info["주소"] = address2
            print(f"주소: {address2}")

    except Exception as e:
        print(f"Error: {e}")



def click_paging_items(driver, address_info_list):

    while True:
        try:
            # 명시적 대기를 사용하여 paging 클래스 요소가 로드될 때까지 기다림
            paging_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".paging"))
            )
            # paging 클래스 안의 모든 li 요소 찾기
            li_elements = paging_element.find_elements(By.CSS_SELECTOR, "li")

            for index, li in enumerate(li_elements):
                try:
                    # li 안의 button 요소 찾기0
                    button = li.find_element(By.CSS_SELECTOR, "button.num")
                    # 요소를 스크롤하여 가시화
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)  # 스크롤 후 대기 (필요에 따라 조정)

                    # JavaScript를 사용하여 요소 클릭
                    driver.execute_script("arguments[0].click();", button)
                    print(f"li num {button.text}")
                    time.sleep(2)  # 클릭 후 대기 (필요에 따라 조정)

                    # "일반 페이지로 이동하기" 클릭 및 주소 추출
                    click_general_pages(driver, address_info_list)

                    if index == 1:
                        return

                    # 마지막 li 요소인 경우
                    if index == len(li_elements) - 1:
                        try:

                            # next 버튼 클릭
                            next_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, ".next"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", next_button)
                            time.sleep(2)  # 클릭 후 대기 (필요에 따라 조정)
                            print(f"li last click")
                            break  # while 루프를 계속 돌기 위해 break 사용
                        except Exception as e:
                            print("Next button not found. Exiting loop.")
                            return  # next 버튼을 찾지 못하면 종료
                except Exception as e:
                    print(f"Error clicking li element: {e}")
        except Exception as e:
            print(f"Error: {e}")
            return  # paging 요소를 찾지 못하면 종료


def main():
    driver = setup_driver()
    driver.get("https://www.cretop.com")
    time.sleep(3)  # 페이지가 완전히 로드되도록 대기

    id = "sfac1025"
    pw = "sfac1025!!"

    if not load_storage(driver, "storage_data"):
        # localStorage 데이터가 없거나 불완전하면 로그인 수행
        click_close_button(driver)  # 팝업 닫기
        login(driver, id, pw)

    # "기업" 탭 클릭
    click_company_tab(driver)



    # 검색 수행
    search_term = "건설"
    perform_search(driver, search_term)

    time.sleep(3)


    address_defail_info_list = []

    # 주소 정보 리스트 초기화
    address_info_list = []
    click_paging_items(driver, address_info_list)

    for address_info in address_info_list:
        print(f"회사명 {address_info["회사"]}")
        time.sleep(2)
        driver.refresh()
        perform_search(driver, address_info["회사"])

        click_general_pages_search(driver, address_info)

        print(f"address_info : {address_info}")
        address_defail_info_list.append(address_info)


    print(f"address_defail_info_list ; {address_defail_info_list}")
    print(f"len address_defail_info_list ; {len(address_defail_info_list)}")


    # 엑셀 파일로 저장
    df = pd.DataFrame(address_defail_info_list)
    df.to_excel("address_info.xlsx", index=False)
    print("엑셀 파일 저장 완료: address_info.xlsx")

    driver.quit()

if __name__ == "__main__":
    main()