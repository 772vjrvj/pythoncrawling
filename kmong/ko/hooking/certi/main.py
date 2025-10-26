# main_240601.py
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--proxy-server=http://127.0.0.1:8080')  # 프록시 설정 추가

    driver = uc.Chrome(
        options=options,
        driver_executable_path=ChromeDriverManager().install()
    )
    return driver

driver = setup_driver()
driver.get("https://gpm.golfzonpark.com/")

print("⏳ 예약 요청 감지 대기 중... Ctrl+C로 종료")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    driver.quit()
