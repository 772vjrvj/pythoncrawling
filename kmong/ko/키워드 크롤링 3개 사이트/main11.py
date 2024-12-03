from selenium_recaptcha_solver import RecaptchaSolver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os

# ffmpeg 경로 설정 (ffmpeg이 설치된 경우)
os.environ["PATH"] += os.pathsep + r'C:\ffmpeg\bin'  # ffmpeg 경로를 시스템 PATH에 추가



# 크롬 드라이버의 경로를 지정합니다.
chrome_driver_path = r'C:\chromedriver-win64'
service = Service(chrome_driver_path)

test_ua = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

options = Options()
options.add_argument("--headless")  # Remove this if you want to see the browser (Headless makes the chromedriver not have a GUI)
options.add_argument("--window-size=1920,1080")
options.add_argument(f'--user-agent={test_ua}')
options.add_argument('--no-sandbox')
options.add_argument("--disable-extensions")

# 드라이버를 초기화합니다.
try:
    test_driver = webdriver.Chrome(service=service, options=options)

    # RecaptchaSolver 초기화
    solver = RecaptchaSolver(driver=test_driver)

    # 웹 페이지를 엽니다.
    test_driver.get('https://www.google.com/recaptcha/api2/demo')

    # reCAPTCHA iframe을 찾습니다.
    recaptcha_iframe = test_driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

    # reCAPTCHA를 해결합니다.
    solver.click_recaptcha_v2(iframe=recaptcha_iframe)

    # 필요한 작업을 추가로 수행합니다.
    # 예를 들어, reCAPTCHA를 통과한 후의 요소를 찾습니다.
    # test_driver.find_element(By.ID, 'element_id')

finally:
    # 드라이버를 종료합니다.
    test_driver.quit()