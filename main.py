from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd

import time

def scroll_down(driver):
    """W3C Actions API를 사용하여 스와이프 제스처를 구현"""
    screen_size = driver.get_window_size()
    start_x = screen_size['width'] // 2
    start_y = screen_size['height'] * 5 // 6  # 화면 아래쪽 5/6 지점에서 시작
    end_y = screen_size['height'] // 6  # 화면 위쪽 1/6 지점에서 끝

    actions = ActionChains(driver)
    actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
    actions.w3c_actions.pointer_action.pointer_down()
    actions.w3c_actions.pointer_action.move_to_location(start_x, end_y)
    actions.w3c_actions.pointer_action.release()
    actions.perform()

    time.sleep(2)  # 스크롤 후 대기

def scroll_and_collect_buttons(driver, max_buttons=150):
    collected_buttons = set()
    scroll_attempts = 0

    while len(collected_buttons) < max_buttons:  # 최대 스크롤 시도 횟수 제한
        try:
            buttons = driver.find_elements(AppiumBy.ID, "com.instagram.android:id/image_button")
            for button in buttons:
                content_desc = button.get_attribute("content-desc")
                if content_desc not in collected_buttons:
                    collected_buttons.add(content_desc)

            print(f"현재 수집된 버튼 개수: {len(collected_buttons)}")
            scroll_down(driver)
            scroll_attempts += 1

        except StaleElementReferenceException:
            print("StaleElementReferenceException 발생, 요소를 다시 찾습니다.")
            scroll_down(driver)  # 스크롤 후 재탐색
            time.sleep(2)

        except Exception as e:
            print(f"스크롤 중 다른 오류 발생: {e}")
            break

    return list(collected_buttons)[:max_buttons]

def extract_usernames(collected_buttons):
    """'님의 사진' 앞에 있는 사용자 이름만 추출하는 함수"""
    usernames = []
    for content_desc in collected_buttons:
        if '님의 사진' in content_desc:
            username = content_desc.split('님의 사진')[0]
            usernames.append(username)
    return usernames


def save_usernames_to_excel(user_data, file_name="usernames.xlsx"):
    """사용자 이름과 해시태그 리스트를 엑셀 파일로 저장하거나 업데이트하는 함수"""
    try:
        # 기존 엑셀 파일을 읽어온다 (파일이 있을 경우)
        existing_data = pd.read_excel(file_name)
        df_existing = pd.DataFrame(existing_data)
    except FileNotFoundError:
        # 파일이 없을 경우 새로 만든다
        df_existing = pd.DataFrame(columns=["Usernames", "Hashtag"])

    # 새로운 데이터를 추가한다
    df_new = pd.DataFrame(user_data, columns=["Usernames", "Hashtag"])
    df_combined = pd.concat([df_existing, df_new], ignore_index=True).drop_duplicates()

    # 엑셀 파일에 저장
    df_combined.to_excel(file_name, index=False)
    print(f"엑셀 파일 '{file_name}'에 사용자 이름과 해시태그가 업데이트되었습니다.")


def main():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = "9"
    options.device_name = "emulator-5554"
    options.app_package = "com.instagram.android"
    options.app_activity = "com.instagram.mainactivity.InstagramMainActivity"
    options.no_reset = True
    options.adb_exec_timeout = 20000
    options.adb_executable = "C:\\Users\\772vj\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"

    driver = webdriver.Remote(command_executor='http://localhost:4723/wd/hub', options=options)

    hashtags = [
        "#kbeautyreview", "#kbeautyroutine", "#sensitiveskin",
        "#fordryskin", "#veganskincareproducts", "#acneroutine"
    ]
    user_data = set()  # 사용자 이름과 해시태그를 저장할 세트 (중복 제거를 위해)

    try:
        wait = WebDriverWait(driver, 30)

        for hashtag in hashtags:
            search_icon = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, '//android.widget.FrameLayout[@content-desc="검색 및 탐색하기"]/android.widget.ImageView')))
            search_icon.click()
            time.sleep(3)

            # 검색 창에 포커스를 주기 위해 검색 상자를 클릭
            search_box = wait.until(EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/action_bar_search_edit_text")))
            search_box.click()
            time.sleep(2)

            # 텍스트 입력 및 검색 실행
            search_box.clear()
            search_box.send_keys(hashtag)
            driver.tap([(search_box.location['x'] + 10, search_box.location['y'] + 10)])  # 포커스 맞춤
            time.sleep(1)

            # 검색 결과 클릭
            search_result = wait.until(EC.element_to_be_clickable((AppiumBy.ID, "com.instagram.android:id/row_hashtag_container")))
            search_result.click()
            time.sleep(2)

            # 스크롤하면서 버튼 수집
            collected_buttons = scroll_and_collect_buttons(driver, max_buttons=150)

            # 사용자 이름 추출 및 중복 제거
            usernames = extract_usernames(collected_buttons)
            for username in usernames:
                user_data.add((username, hashtag))

            # 사용자 이름과 해시태그를 엑셀에 저장 (한 번의 해시태그 작업이 끝날 때마다)
            save_usernames_to_excel(list(user_data), "usernames.xlsx")


    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
