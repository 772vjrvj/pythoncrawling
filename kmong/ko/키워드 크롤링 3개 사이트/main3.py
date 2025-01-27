import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login_and_navigate(email, password):
    # Chrome WebDriver 설정
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://loword.co.kr/login")
        driver.maximize_window()
        # 이메일 로그인 버튼 클릭
        email_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "이메일로 로그인하기")]/ancestor::div[@type="secondary"]'))
        )
        email_login_button.click()

        # 이메일 입력 필드
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="이메일 주소를 입력해주세요."]'))
        )
        email_field.send_keys(email)

        # 비밀번호 입력 필드
        password_field = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="비밀번호를 입력해주세요."]')
        password_field.send_keys(password)

        # 로그인 버튼 클릭
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='로그인']/ancestor::div[@type='point']"))
        )
        submit_button.click()

        # "넘어가기" 버튼 클릭
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='넘어가기']"))
        )
        next_button.click()

        # 기다림: 페이지 로딩 및 광고 사라지기 대기
        time.sleep(2)  # 광고가 사라지기를 기다리기 위한 대기 시간

        # 전체 화면 클릭
        action = ActionChains(driver)
        action.move_by_offset(100, 100).click().perform()  # 예를 들어, (100, 100) 좌표를 클릭

        # 검색어 입력 필드 입력
        search_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[tagsboxmaxwidth="650"]'))
        )
        search_field.send_keys("현충일")


        # 검색하기 버튼 클릭
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[text()="검색하기"]/ancestor::div[@type="point"]'))
        )
        search_button.click()

        time.sleep(10)
    except Exception as e:
        print(f"작업 중 오류 발생: {e}")

    # 브라우저 종료
    #driver.quit()

if __name__ == "__main__":
    email = "772vjrvj@naver.com"
    password = "Ksh@8818510"
    login_and_navigate(email, password)
    input("Press any key to exit...")  # 사용자가 키를 입력할 때까지 브라우저 유지