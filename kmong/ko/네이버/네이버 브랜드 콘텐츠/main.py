from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=500,750")

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 크롬 드라이버 자동화 감지 회피 옵션
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 자동화 탐지 회피 스크립트 실행
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 페이지의 끝까지 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 페이지가 로드될 시간을 충분히 기다림

        # 스크롤 후의 새로운 높이
        new_height = driver.execute_script("return document.body.scrollHeight")

        # 더 이상 스크롤할 수 없으면 종료
        if new_height == last_height:
            print("더 이상 스크롤할 내용이 없습니다.")
            break

        last_height = new_height

def main(query):
    # 파라미터로 받은 query로 URL을 설정
    url = f"https://m.search.naver.com/search.naver?sm=mtp_hty.top&where=m&query={query}"

    # 드라이버 설정 및 페이지 열기
    driver = setup_driver()
    driver.get(url)

    try:
        # 첫 번째 동작: 특정 섹션 클릭
        wait = WebDriverWait(driver, 10)
        block_container = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "mIFG0GvQh5APzId0BqgQ.fds-comps-footer-full-container")))
        block_container.click()
        print("첫 번째 요소 클릭 완료.")
        time.sleep(2)  # 2초 대기

        # 화면이 바뀌면 block_container _lb_content_root 클래스 요소를 찾고 클릭
        new_page_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".block_container._lb_content_root")))
        new_page_element.click()
        print("두 번째 요소 클릭 완료.")
        time.sleep(2)  # 2초 대기

        # 스크롤을 끝까지 내림
        scroll_to_bottom(driver)

    except Exception as e:
        print(f"오류 발생: {e}")

    finally:
        # 마지막으로 50초 대기
        time.sleep(50)
        driver.quit()

if __name__ == "__main__":
    # 원하는 query를 여기에 입력
    query = "미국유학"
    main(query)
