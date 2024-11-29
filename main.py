import os
import urllib.request
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import urllib.request
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains



# 드라이버 세팅 크롬
def setup_driver():
    chrome_options = Options()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--window-size=1080,750")
    chrome_options.add_argument("--remote-debugging-port=9222")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver


def open_facebook(driver):
    """Navigate to Facebook's main page."""
    driver.get("https://www.facebook.com/")
    print("아무 키나 누르세요...")
    input()


def navigate_to_page(driver, page_url):
    """Navigate to a specific Facebook page."""
    driver.get(page_url)
    time.sleep(2)


def extract_caption(driver, feed_unit):
    """Extract caption text with emojis in correct order using BeautifulSoup."""
    try:
        # story_message_element 찾기
        story_message_element = feed_unit.find_element(By.CSS_SELECTOR, '[data-ad-rendering-role="story_message"]')

        # '더 보기' 버튼 찾기 및 클릭
        try:
            # '더 보기' 버튼 대기 및 찾기
            more_button = WebDriverWait(feed_unit, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                './/div[contains(@class, "x1i10hfl") and contains(@class, "xjbqb8w") and @role="button" and text()="더 보기"]'
                                                ))
            )

            # '더 보기' 버튼 스크롤로 가시성 확보
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)

            # 강제 클릭 시도
            try:
                ActionChains(driver).move_to_element(more_button).click().perform()
                print("'더 보기' 버튼 클릭 성공!")
            except Exception as e:
                print("'더 보기' 기본 클릭 실패, JavaScript로 클릭 시도:", e)
                driver.execute_script("arguments[0].click();", more_button)

        except Exception as e:
            print("'더 보기' 버튼 처리 중 오류:", e)

        # story_message_element의 innerHTML 추출
        caption_html = story_message_element.get_attribute("innerHTML")

        # HTML이 비었는지 확인
        if not caption_html:
            print("캡션 HTML이 비어 있습니다.")
            return None

        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(caption_html, 'html.parser')

        # 순차적으로 요소를 순회하며 텍스트와 이모지를 조합
        final_text = ""
        for element in soup.descendants:
            if element.name == 'img':  # 이모지 <img> 태그 처리
                emoji_alt = element.get('alt', '')  # <img alt="💕">
                final_text += emoji_alt
            elif element.name in ['br', 'div']:  # 줄바꿈 태그 처리
                final_text += '\n'
            elif element.string:  # 일반 텍스트 처리
                final_text += element.string.strip()

        # 결과 텍스트 반환
        return final_text.strip()

    except Exception as e:
        print("캡션 추출 중 오류 발생:", e)
        return None


def click_first_image(driver, feed_unit):
    """Click the first image within a specific feed unit."""
    try:

        if not feed_unit:
            print('feed_unit이 None입니다.')
            return

        print('1111111111111111111=====')
        # Explicit Wait로 이미지 컨테이너 대기
        image_container = WebDriverWait(feed_unit, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.x1n2onr6[style*="padding-top: calc(83.3333%);"]')
            )
        )
        print('2222222222222222222=====')

        # 첫 번째 이미지 링크 찾기
        first_image_link = WebDriverWait(image_container, 10).until(
            EC.element_to_be_clickable((By.TAG_NAME, 'a'))
        )
        print('33333333333333333333=====')

        # 스크롤로 가시성 확보
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_image_link)
        time.sleep(1)
        # 기본 클릭
        try:
            first_image_link.click()
        except Exception as e:
            print("기본 클릭 실패, JavaScript로 클릭 시도:", e)
            driver.execute_script("arguments[0].click();", first_image_link)

        # 클릭 후 대기
        time.sleep(2)

    except Exception as e:
        print("첫 번째 이미지를 클릭하는 중 오류 발생:", e)


def extract_image_sources(driver):
    """Extract image sources and handle '다음 사진' button clicks."""
    img_list = []
    try:
        while True:
            img_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'img[data-visualcompletion="media-vc-image"]'))
            )
            img_src = img_element.get_attribute("src")
            if img_src in img_list:
                # 중복된 이미지를 발견한 경우 사진 뷰어 닫기
                try:
                    close_button = driver.find_element(By.CSS_SELECTOR, 'div[aria-label="닫기"]')
                    close_button.click()
                    time.sleep(1)  # 닫는 동작을 위해 잠시 대기
                except Exception as close_error:
                    print("닫기 버튼을 클릭하는 중 오류 발생:", close_error)
                break  # 중복된 이미지가 발견되면 루프 종료
            img_list.append(img_src)

            # Click 'Next Photo' button
            next_button = driver.find_element(By.CSS_SELECTOR, 'div[aria-label="다음 사진"]')
            next_button.click()
            time.sleep(2)
    except Exception as e:
        print("이미지를 가져오는 중 오류 발생:", e)
    return img_list


def extract_date(feed_unit):
    """Extract the date from the designated 'a' tag inside the specified div element."""
    try:
        # 대기 후 지정된 class 이름을 가진 div 요소 찾기
        date_container = WebDriverWait(feed_unit, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.html-div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1q0g3np')
            )
        )

        # div 요소 안에서 a 태그 찾기
        date_link = date_container.find_element(By.TAG_NAME, 'a')

        # a 태그의 텍스트 추출
        date_text = date_link.text

        # "년"이 포함되어 있지 않으면 앞에 "2024년 " 추가
        if "년" not in date_text:
            date_text = f"2024년 {date_text}"

        return date_text
    except Exception as e:
        print("날짜를 추출하는 중 오류 발생:", e)
        return None


def sanitize_folder_name(folder_name):
    """폴더 이름에서 Windows 금지 문자를 제거합니다."""
    return re.sub(r'[\\/:*?"<>|]', '_', folder_name)


def download_with_retry(url, save_path, retries=3, delay=2):
    """이미지 다운로드를 재시도합니다."""
    for attempt in range(retries):
        try:
            urllib.request.urlretrieve(url, save_path)
            return True
        except Exception as e:
            print(f"다운로드 실패 (시도 {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    return False


def create_folder_and_save_files(date, caption, img_list):
    """teps4u 폴더를 생성하고 캡션 저장 및 이미지 다운로드를 처리합니다."""
    try:
        # 프로그램이 실행 중인 현재 디렉터리 기준으로 teps4u 폴더 설정
        base_path = os.getcwd()
        teps4u_path = os.path.join(base_path, "teps4u")
        os.makedirs(teps4u_path, exist_ok=True)

        # 날짜별 폴더 생성
        folder_path = os.path.join(teps4u_path, sanitize_folder_name(date))
        os.makedirs(folder_path, exist_ok=True)

        # 캡션 저장
        caption_file_path = os.path.join(folder_path, "caption.txt")
        with open(caption_file_path, "w", encoding="utf-8") as f:
            f.write(caption[:10000])  # 캡션 길이 제한 (예: 10000자)

        # 이미지 다운로드
        for idx, img_url in enumerate(img_list):
            img_path = os.path.join(folder_path, f"image_{idx + 1}.jpg")
            if not download_with_retry(img_url, img_path):
                print(f"이미지 다운로드 포기: {img_url}")

        print(f"파일 저장 완료: {folder_path}")
    except Exception as e:
        print("파일 저장 중 오류 발생:", e)


def process_feed_unit(driver, feed_unit):
    """Process a single feed unit."""
    try:

        date = extract_date(feed_unit)
        caption = extract_caption(driver, feed_unit)
        click_first_image(driver, feed_unit)
        img_list = extract_image_sources(driver)

        obj = {
            '날짜': date,
            'caption': caption,
            '이미지 리스트': img_list
        }
        print(f'obj : {obj}')
        create_folder_and_save_files(date, caption, img_list)

    except Exception as e:
        print("피드 처리 중 오류 발생:", e)


def main():
    driver = setup_driver()
    try:
        open_facebook(driver)
        navigate_to_page(driver, "https://www.facebook.com/teps4u/")

        """스크롤하면서 피드의 총 개수를 기준으로 새로운 피드 로드를 확인하고 처리."""
        previous_feed_count = 0  # 이전 피드 개수를 추적

        while True:
            try:
                # 스크롤하여 새로운 콘텐츠 로드 시도
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

                # 현재 뷰에 표시된 모든 피드 가져오기
                feed_units = driver.find_elements(By.CSS_SELECTOR, '[data-pagelet^="TimelineFeedUnit_"]')
                current_feed_count = len(feed_units)

                # 피드 개수가 이전과 같으면 중지
                if current_feed_count == previous_feed_count:
                    print("더 이상 새로운 피드가 없습니다.")
                    break

                # 새로운 피드 처리
                for feed_unit in feed_units[previous_feed_count:]:
                    try:
                        process_feed_unit(driver, feed_unit)
                    except Exception as e:
                        print(f"피드 처리 중 오류 발생: {e}")

                # 현재 피드 개수를 이전 피드 개수로 업데이트
                previous_feed_count = current_feed_count

            except WebDriverException as e:
                print(f"스크롤 중 오류 발생: {e}")
                break
            except Exception as e:
                print(f"알 수 없는 오류 발생: {e}")
                break

        print("스크롤 및 처리 완료.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
