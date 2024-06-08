import time
import os
import requests
from bs4 import BeautifulSoup
from itertools import cycle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ffmpeg 경로 설정 (ffmpeg이 설치된 경우)
os.environ["PATH"] += os.pathsep + r'C:\ffmpeg\bin'  # ffmpeg 경로를 시스템 PATH에 추가

# 크롬 드라이버의 경로를 지정합니다.
chrome_driver_path = r'C:\chromedriver-win64\chromedriver.exe'
service = Service(chrome_driver_path)

test_ua = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

options = Options()
options.add_argument(f'--user-agent={test_ua}')
options.add_argument('--no-sandbox')
options.add_argument("--disable-extensions")
options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트 설정

def get_free_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    proxies = []
    for row in soup.find('table', {'class': 'table table-striped table-bordered'}).tbody.find_all('tr'):
        columns = row.find_all('td')
        ip_address = columns[0].text.strip()
        port = columns[1].text.strip()
        anonymity = columns[4].text.strip()
        if anonymity == 'anonymous':  # 익명성을 확인합니다
            proxies.append(f'{ip_address}:{port}')
    return proxies

def setup_driver(proxy):
    options.add_argument(f'--proxy-server={proxy}')
    return webdriver.Chrome(service=service, options=options)

def process_captcha(driver):
    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@title='reCAPTCHA']"))
    )
    checkbox = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'recaptcha-checkbox-border'))
    )
    checkbox.click()

    time.sleep(5)

    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    driver.switch_to.frame(iframes[4])
    audio_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'rc-button-audio'))
    )
    audio_button.click()

    print("음성 보안문자 버튼을 클릭했습니다.")
    driver.switch_to.default_content()
    time.sleep(5)

def main():
    proxies = get_free_proxies()
    proxy_pool = cycle(proxies)  # 프록시 리스트를 순환

    try:
        driver = setup_driver(next(proxy_pool))
        driver.get('https://loword.co.kr/keyword?engine=naver&query=%EB%AF%B8%EB%85%80%EC%99%80%20%EC%88%9C%EC%A0%95%EB%82%A8')

        process_captcha(driver)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()