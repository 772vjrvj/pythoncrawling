import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

def setup_driver():
    chrome_options = Options()  # 크롬 옵션 설정

    # 헤드리스 모드로 실행
    # chrome_options.add_argument("--headless")

    # GPU 비활성화
    chrome_options.add_argument("--disable-gpu")

    # 샌드박스 보안 모드를 비활성화합니다.
    chrome_options.add_argument("--no-sandbox")

    # /dev/shm 사용 비활성화
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 시크릿 모드로 실행
    chrome_options.add_argument("--incognito")

    # 사용자 에이전트를 설정하여 브라우저의 기본값 대신 특정 값을 사용하게 합니다.
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 감지 우회 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 웹 드라이버 설정
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # navigator.webdriver 속성 우회 설정
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    return driver

def main():
    driver = setup_driver()
    urls = [
        "https://www.youtube.com/watch?v=QFHpl362P5U&t=47s",
        "https://www.youtube.com/watch?v=6i-bHf3OiIg",
        "https://www.youtube.com/watch?v=uUWdYkAIGtU",
        "https://www.youtube.com/c/danbiii/videos",
        "https://www.youtube.com/watch?v=PMhkuv3xLTA&t=120s",  # 안됨
        "https://www.youtube.com/channel/UCfAmK0K_H6e2xQSz_uIJMJg/videos",
        "https://www.youtube.com/watch?v=OSLXQOEsYDc&t=9s",
        "https://www.youtube.com/watch?v=a-H-SMInU18&t=123s",
        "https://www.youtube.com/watch?v=7-HCVk-9jFY",
        "https://www.youtube.com/watch?v=yqVYEQW089E&t=46s",
        "https://www.youtube.com/watch?v=tDmrMCBgELk&t=23s"
    ]

    try:
        start_time = datetime.now()
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        for url in urls:
            print(f"Processing URL: {url}")
            loop_start_time = datetime.now()
            print(f"Loop start time: {loop_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

            driver.get(url)
            wait = WebDriverWait(driver, 10)
            time.sleep(random.uniform(2, 3))

            # "player-error-message-container" ID가 존재하면 다음 URL로 건너뛰는 로직 추가
            try:
                # 요소가 나타날 때까지 최대 10초 대기
                error_message = wait.until(
                    EC.presence_of_element_located((By.ID, "player-error-message-container"))
                )

                if error_message:
                    print(f"Error message found on URL: {url}. Skipping this video.")
                    continue
            except TimeoutException:
                # 에러 메시지가 없을 경우 넘어감
                pass

            if "/channel/" in url or "/c/" in url:
                # 채널 URL일 때
                try:
                    # "동영상" 탭으로 이동
                    video_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//yt-tab-shape[@tab-title="동영상"]')))
                    video_tab.click()
                except (TimeoutException, ElementClickInterceptedException) as e:
                    print(f"Error while navigating to videos tab on URL: {url} - {e}")
                    continue
            else:
                # 동영상 URL일 때
                try:
                    # 채널 링크 찾기
                    channel_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "yt-simple-endpoint.style-scope.ytd-video-owner-renderer")))

                    # 스크롤하여 요소를 화면 중앙에 위치시킴
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", channel_link)
                    time.sleep(1)

                    # JavaScript를 이용해 직접 클릭
                    driver.execute_script("arguments[0].click();", channel_link)

                    # "동영상" 탭으로 이동
                    video_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//yt-tab-shape[@tab-title="동영상"]')))
                    video_tab.click()
                except (TimeoutException, ElementClickInterceptedException) as e:
                    print(f"Error while navigating to channel on URL: {url} - {e}")
                    continue

            time.sleep(random.uniform(2, 3))
            try:
                # 첫 번째 비디오 요소 대기 및 찾기
                first_video = wait.until(EC.presence_of_element_located((By.XPATH, '(//ytd-rich-item-renderer)[1]')))

                # 시간 정보 (예: "4개월 전")를 추출
                time_element = first_video.find_element(By.XPATH, './/span[contains(@class, "inline-metadata-item") and contains(text(), "전")]')
                time_text = time_element.text
                print(f"영상 업로드 시간: {time_text}")

                # 비디오 URL 추출
                video_url_element = first_video.find_element(By.XPATH, './/a[@id="video-title-link"]')
                video_url = video_url_element.get_attribute('href')
                print(f"영상 URL: {video_url}")

            except (NoSuchElementException, TimeoutException) as e:
                print(f"Error while extracting video info on URL: {url} - {e}")
                continue  # 예외 발생 시 다음 URL로 넘어감

            loop_end_time = datetime.now()
            print(f"Loop end time: {loop_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total loop time: {str(loop_end_time - loop_start_time)}")

            print("\n" + "-"*50 + "\n")  # 구분선 추가

        end_time = datetime.now()
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total elapsed time: {str(end_time - start_time)}")

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # 작업이 완료된 후 드라이버 종료
        driver.quit()

if __name__ == "__main__":
    main()
