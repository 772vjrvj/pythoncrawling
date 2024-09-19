from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import pyautogui
import time
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
from selenium.webdriver.common.action_chains import ActionChains


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


# 네이버 로그인
def naver_login():
    global global_cookies

    driver = setup_driver()
    driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

    logged_in = False
    max_wait_time = 300  # 최대 대기 시간 (초)
    start_time = time.time()

    while not logged_in:
        print('진행중...')
        time.sleep(1)
        elapsed_time = time.time() - start_time

        if elapsed_time > max_wait_time:
            messagebox.showwarning("경고", "로그인 실패: 300초 내에 로그인하지 않았습니다.")
            break

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

        if 'NID_AUT' in cookies and 'NID_SES' in cookies:
            logged_in = True
            global_cookies = cookies
            messagebox.showinfo("로그인 성공", "정상 로그인 되었습니다.")

            time.sleep(1)
            driver.get("https://blog.naver.com/772vjrvj?Redirect=Write&")

            try:
                time.sleep(5)  # 페이지 로드 시간 추가

                # iframe으로 전환
                iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'mainFrame'))  # iframe의 ID로 전환
                )
                driver.switch_to.frame(iframe)


                # time.sleep(2)
                # 이제 iframe 내에서 요소를 찾음
                # popup_button = WebDriverWait(driver, 10).until(
                #     EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-cancel'))
                # )
                # popup_button.click()


                time.sleep(2)
                # 이제 iframe 내에서 요소를 찾음
                close_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-help-panel-close-button'))
                )
                close_button.click()

                print('close_button')

                # 3초 후 텍스트 입력 (클래스 이름 'se-ff-nanumgothic se-fs32 __se-node' 내부에 텍스트 '1234' 입력)
                time.sleep(2)

                # 요소 찾기

                # 더 세밀하게 특정 요소를 클릭하고 텍스트 입력
                bb = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"제목")]'))
                )
                # 클릭 후 텍스트 삽입
                bb.click()
                actions = ActionChains(driver)
                actions.send_keys("입력할 텍스트").perform()


                time.sleep(2)
                # 이제 iframe 내에서 요소를 찾음
                image_upload_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-image-toolbar-button'))
                )
                image_upload_button.click()

                # 파일 업로드 처리
                time.sleep(2)
                upload_images(driver, 'D:\\GitHub\\pythoncrawling\\이미지\\400021727440')

            except Exception as e:
                print(f"에러 발생: {e}")

            time.sleep(200)
            driver.quit()  # 작업이 끝난 후 드라이버 종료


def upload_images(driver, folder_path):
    # Windows 파일 선택 창에서 경로를 입력하고 '열기' 버튼을 누름
    time.sleep(2)  # 파일 선택 창이 열릴 때까지 대기

    # 경로가 정확한지 확인
    if not os.path.exists(folder_path):
        messagebox.showerror("경로 오류", f"경로가 존재하지 않습니다: {folder_path}")
        return

    # 상단 경로 입력창에 포커스 맞추기 (탐색기 창에서 경로 입력)
    pyautogui.hotkey('alt', 'd')  # 상단 경로창 선택
    time.sleep(1)

    # 클립보드를 사용해 경로 입력
    pyperclip.copy(folder_path)  # 경로를 클립보드에 복사
    pyautogui.hotkey('ctrl', 'v')  # 클립보드에서 붙여넣기 (Ctrl + V)
    pyautogui.press('enter')  # 엔터키로 폴더 열기

    time.sleep(2)  # 폴더 열리는 시간 대기

    # 파일 목록에 포커스 맞추기 (탐색기 창에서 파일 선택으로 이동)
    pyautogui.press('tab')  # 경로창에서 파일 목록으로 이동하기 위해 탭 누르기
    pyautogui.press('tab')  # 두 번째 탭을 누르면 파일 목록에 포커스가 맞춰짐
    pyautogui.press('tab')  # 세 번째 탭을 누르면 포커스가 맞춰짐
    pyautogui.press('tab')  # 네 번째 탭을 누르면 포커스가 맞춰짐
    pyautogui.press('down')  # 파일 목록의 첫 번째 파일로 이동

    # 전체 파일 선택 (Ctrl + A)
    pyautogui.hotkey('ctrl', 'a')  # 모든 파일 선택
    time.sleep(1)

    # 파일 열기(확인) 버튼 클릭 (Windows 기준)
    pyautogui.press('enter')  # 열기 버튼을 눌러 파일 업로드

    time.sleep(3)

    # 스크롤을 맨 위로 올리기
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


    # 이제 iframe 내에서 요소를 찾음 (이미지 업로드 후 추가 작업)
    image_upload_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'se-image-type-label'))
    )

    print('test1')
    # JavaScript로 강제 클릭
    driver.execute_script("arguments[0].click();", image_upload_button)

    # 활성화된 요소 가져오기
    active_element = driver.switch_to.active_element

    # ActionChains로 클릭 후 텍스트 입력 시도
    actions = ActionChains(driver)
    actions.move_to_element(active_element).click().send_keys("여기에 입력할 텍스트").perform()
    print('test2')

    # # 더 세밀하게 특정 요소를 클릭하고 텍스트 입력
    # bb = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"본문에")]'))
    # )
    # # 클릭 후 텍스트 삽입
    # bb.click()
    # actions = ActionChains(driver)
    # actions.send_keys("입력할 텍스트").perform()




    # 3초 후 'publish_btn__m9KHH' 클래스 버튼 클릭
    time.sleep(3)
    publish_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'publish_btn__m9KHH'))
    )
    driver.execute_script("arguments[0].click();", publish_button)

    # 3초 후 'confirm_btn__WEaBq' 클래스 버튼 클릭
    time.sleep(3)
    confirm_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'confirm_btn__WEaBq'))
    )
    driver.execute_script("arguments[0].click();", confirm_button)




def main():
    naver_login()

if __name__ == "__main__":
    main()
