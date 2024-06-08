import time
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import subprocess

# ffmpeg 경로 설정 (ffmpeg이 설치된 경우)
os.environ["PATH"] += os.pathsep + r'C:\ffmpeg\bin'  # ffmpeg 경로를 시스템 PATH에 추가

# 크롬 드라이버의 경로를 지정합니다.
chrome_driver_path = r'C:\chromedriver-win64\chromedriver.exe'
service = Service(chrome_driver_path)

test_ua = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

chrome_browser = subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                                  r'--remote-debugging-port=9222 '
                                  r'--user-data-dir="C:\Temp\chrome"')



options = Options()
# options.add_argument("--headless")  # Remove this if you want to see the browser (Headless makes the chromedriver not have a GUI)
options.add_argument(f'--user-agent={test_ua}')
options.add_argument('--no-sandbox')
options.add_argument("--disable-extensions")

options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")



# 드라이버를 초기화합니다.
try:
    test_driver = webdriver.Chrome(service=service, options=options)

    # 웹 페이지를 엽니다.
    test_driver.get('https://loword.co.kr/keyword?engine=naver&query=%EB%AF%B8%EB%85%80%EC%99%80%20%EC%88%9C%EC%A0%95%EB%82%A8')

    # reCAPTCHA iframe을 찾고 체크박스를 클릭합니다.
    WebDriverWait(test_driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@title='reCAPTCHA']"))
    )
    checkbox = WebDriverWait(test_driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'recaptcha-checkbox-border'))
    )
    checkbox.click()

    time.sleep(5)

    # 최상위 컨텍스트로 돌아가기
    test_driver.switch_to.default_content()

    iframes = test_driver.find_elements(By.TAG_NAME, 'iframe')

    # 두 번째 iframe으로 전환
    test_driver.switch_to.frame(iframes[4])

    # recaptcha-audio-button 클래스를 가진 요소가 나타날 때까지 기다립니다
    audio_button = WebDriverWait(test_driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'rc-button-audio'))
    )

    # 클릭
    audio_button.click()

    print("음성 보안문자 버튼을 클릭했습니다.")

    # 원래의 컨텍스트로 돌아가기 위해 main frame으로 전환
    test_driver.switch_to.default_content()

    # 추가적인 작업을 수행하거나 페이지를 기다립니다.
    time.sleep(5)

finally:
    # 드라이버를 종료합니다.
    test_driver.quit()