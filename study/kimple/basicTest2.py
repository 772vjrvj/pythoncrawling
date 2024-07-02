import os

#최신 selenium을 다운 받고 시직한다.
os.system('pip install --upgrade selenium')

from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

url = "https://naver.com"

options = Options()

# 화면이 제일 크게 열림
options.add_argument("--start-maximized")
# 헤드리스 모드 (브라우저 창을 띄우지 않음)
# options.add_argument('--headless')

# 화면이 안꺼짐
options.add_experimental_option("detach", True)

# driver = webdriver.Edge()
# C:\Users\772vj\.cache\selenium 이 경로에 Edge드라이버 생김
driver = webdriver.Chrome(options=options)

driver.get(url)

time.sleep(2)


#네이버에 검색이 입력창 id="query"
driver.find_element(By.ID, "query").send_keys("인공지능")
time.sleep(2)

#네이버에 검색어 찾기 버튼 id="search-btn"
driver.find_element(By.CSS_SELECTOR, "#search-btn").click()
time.sleep(2)

#스크린샷
driver.save_screenshot("naver_인공지능.png")


# 웹드라이버 종료
driver.quit()