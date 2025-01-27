import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main(email, password):
    # Chrome WebDriver 설정
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://ads.google.com/")

        # 'aria-label' 속성이 '로그인'인 <a> 태그를 찾아 클릭
        wait = WebDriverWait(driver, 20)
        login_button = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='로그인']")))

        # JavaScript를 사용하여 클릭
        driver.execute_script("arguments[0].click();", login_button)

        # # '다른 계정 사용' <div> 요소를 기다리고 클릭
        # other_account_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'AsY17b') and text()='다른 계정 사용']")))
        # driver.execute_script("arguments[0].click();", other_account_button)


        # 이메일 입력 필드를 기다리고 이메일 주소 입력
        email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='identifierId']")))
        email_field.send_keys("772vjrvj@gmail.com")

        # '다음' 버튼을 기다리고 클릭
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='다음']")))
        next_button.click()


        time.sleep(10)
    except Exception as e:
        print(f"작업 중 오류 발생: {e}")

    # 브라우저 종료
    #driver.quit()

if __name__ == "__main__":
    email = "772vjrvj@gmail.com"
    password = "Ksh@8818510"
    main(email, password)
    input("Press any key to exit...")  # 사용자가 키를 입력할 때까지 브라우저 유지