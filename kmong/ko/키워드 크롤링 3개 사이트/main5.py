import os
import sys
import time
from pydub import AudioSegment
from selenium_recaptcha_solver import RecaptchaSolver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ffmpeg 및 ffprobe 경로 설정
ffmpeg_path = 'C:/ffmpeg-2024-06-06-git-d55f5cba7b-full_build/bin/ffmpeg.exe'
ffprobe_path = 'C:/ffmpeg-2024-06-06-git-d55f5cba7b-full_build/bin/ffprobe.exe'

os.environ['FFMPEG_BINARY'] = ffmpeg_path
os.environ['FFPROBE_BINARY'] = ffprobe_path

# 시스템 정보 출력
print('Python %s on %s' % (sys.version, sys.platform))

# chromedriver 경로 지정
driver_path = 'C:/chromedriver-win64/chromedriver.exe'  # 실제 경로로 업데이트하세요

test_ua = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

options = Options()
options.add_argument(f'--user-agent={test_ua}')
options.add_argument('--no-sandbox')
options.add_argument("--disable-extensions")

# chromedriver 서비스 설정
service = Service(driver_path)

# WebDriver 초기화
test_driver = webdriver.Chrome(service=service, options=options)

solver = RecaptchaSolver(driver=test_driver)

# 테스트 페이지 열기
test_driver.get('https://www.google.com/recaptcha/api2/demo')

# reCAPTCHA iframe 찾기
recaptcha_iframe = test_driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

# reCAPTCHA v2 클릭
solver.click_recaptcha_v2(iframe=recaptcha_iframe)

# 필요한 작업을 기다립니다.
time.sleep(5)

# 드라이버 종료
test_driver.quit()

# 예시 오디오 파일 로드
