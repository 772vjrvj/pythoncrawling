import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Chrome 드라이버 경로 설정
driver_path = 'C:/chromedriver-win64/chromedriver.exe'
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-extensions')

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

try:
    # 테스트 페이지 열기
    driver.get('https://www.google.com/recaptcha/api2/demo')

    # reCAPTCHA 기본 iframe로 로드 후 전환
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@title="reCAPTCHA"]')))
    # reCAPTCHA 체크박스 클릭
    checkbox = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
    )
    checkbox.click()
    print("reCAPTCHA 체크박스를 클릭했습니다.")

    # 2분 후 만료될 reCAPTCHA iframe 로딩 및 전환
    # WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@title="reCAPTCHA&nbsp;보안문자 2분 후 만료"]')))
    # # 오디오 버튼 클릭
    # audio_button = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, '//button[@title="음성 보안문자 듣기"]'))
    # )
    # audio_button.click()
    print("오디오 보안문자 버튼을 클릭했습니다.")

    # 결과를 확인하기 위해 잠시 대기
    time.sleep(100)

finally:
    # 드라이버 종료
    driver.quit()