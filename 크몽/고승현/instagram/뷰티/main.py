from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def scroll_and_collect_buttons(driver, max_buttons=20):
    collected_buttons = set()
    scroll_attempts = 0

    while len(collected_buttons) < max_buttons:
        try:
            buttons = driver.find_elements(AppiumBy.ID, "com.instagram.android:id/image_button")
            for button in buttons:
                content_desc = button.get_attribute("content-desc")
                if content_desc not in collected_buttons:
                    collected_buttons.add(content_desc)

            print(f"현재 수집된 버튼 개수: {len(collected_buttons)}")
            scroll_down(driver)
            scroll_attempts += 1

        except Exception as e:
            print(f"스크롤 중 오류 발생: {e}")
            break

    return list(collected_buttons)[:max_buttons]

def click_buttons(driver, buttons):
    for index, content_desc in enumerate(buttons):
        try:
            print(f"버튼 {index+1} 클릭 중...")
            button = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().description("{content_desc}")')
            button.click()
            time.sleep(2)

        except Exception as e:
            print(f"버튼 {index+1} 클릭 중 오류 발생: {e}")

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

    try:
        wait = WebDriverWait(driver, 30)

        search_icon = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, '//android.widget.FrameLayout[@content-desc="검색 및 탐색하기"]/android.widget.ImageView')))
        search_icon.click()
        time.sleep(2)

        search_box = wait.until(EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/action_bar_search_edit_text")))
        search_box.send_keys("#kbeautyreview")
        time.sleep(2)

        # 엔터 키를 물리적으로 눌러 검색 실행
        # 검색 박스의 좌표를 클릭하여 엔터 입력
        driver.tap([(search_box.location['x'] + 10, search_box.location['y'] + 10)])  # 포커스 맞춤
        time.sleep(1)
        # 검색 결과 클릭 (지정된 XPath 사용)
        # 요소가 보일 때까지 기다립니다.
        search_result = wait.until(EC.element_to_be_clickable((AppiumBy.ID, "com.instagram.android:id/row_hashtag_container")))
        search_result.click()  # 클릭합니다.

        collected_buttons = scroll_and_collect_buttons(driver, max_buttons=20)
        print(f"최종 수집된 버튼 개수: {len(collected_buttons)}")

        click_buttons(driver, collected_buttons)

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
