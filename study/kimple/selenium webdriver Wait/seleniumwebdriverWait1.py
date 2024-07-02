from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


import time


options = Options()

# 화면이 제일 크게 열림
options.add_argument("--start-maximized")
# 헤드리스 모드 (브라우저 창을 띄우지 않음)
# options.add_argument('--headless')

# 화면이 안꺼짐
options.add_experimental_option("detach", True)


driver = webdriver.Chrome(options=options)

# time.sleep(10) #자동으로 안보이게 할려고
driver.implicitly_wait(10)
driver.get('https://www.naver.com/')

#네이버에 검색어 찾기 버튼 id="search-btn"
# button = driver.find_element(By.CSS_SELECTOR, "#search-btn")
button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#search-btn')))

#검색버튼 클릭
button.click()


