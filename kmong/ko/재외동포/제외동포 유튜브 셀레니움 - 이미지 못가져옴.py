from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pandas as pd
import time

# 웹드라이버 설정 함수
def setup_driver():
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Uncomment if you want to run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--incognito")  # Use incognito mode

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

        driver.maximize_window()  # Maximize the window

        return driver
    except WebDriverException as e:
        if driver:
            driver.quit()
        return None


# 콘텐츠 주소 추출 함수
def extract_content_url(content):
    try:
        thumbnail = content.find_element(By.CSS_SELECTOR, '#thumbnail.yt-simple-endpoint.inline-block.style-scope.ytd-thumbnail')
        return thumbnail.get_attribute("href")
    except:
        return None

# 콘텐츠 이미지 URL 추출 함수
def extract_content_image_url(content):
    try:
        thumbnail_tag = content.find_element(By.CSS_SELECTOR, 'a#thumbnail')

        # 이미지 로드 대기를 위해 WebDriverWait 사용
        img_tag = WebDriverWait(thumbnail_tag, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )

        # 순차적으로 `src`, `data-src`, `data-thumb` 속성을 확인
        img_url = img_tag.get_attribute("src") or img_tag.get_attribute("data-src") or img_tag.get_attribute("data-thumb")

        return img_url if img_url else None
    except:
        return None

# 콘텐츠 명 추출 함수
def extract_content_name(content):
    try:
        details = content.find_element(By.CSS_SELECTOR, '#details.style-scope.ytd-rich-grid-media')
        title_element = details.find_element(By.CSS_SELECTOR, '#video-title.style-scope.ytd-rich-grid-media')
        return title_element.text.strip()
    except:
        return None


# 콘텐츠 공개 연도 계산 함수
def calculate_content_year(time_text, today):
    if "일 전" in time_text:
        days = int(time_text.split("일")[0].strip())
        return today - timedelta(days=days)
    elif "주 전" in time_text:
        weeks = int(time_text.split("주")[0].strip())
        return today - timedelta(weeks=weeks)
    elif "개월 전" in time_text:
        months = int(time_text.split("개월")[0].strip())
        return today - timedelta(days=months * 30)
    elif "년 전" in time_text:
        years = int(time_text.split("년")[0].strip())
        return today - timedelta(days=years * 365)
    return today

# 콘텐츠 리스트 생성 함수
def create_content_list(driver, today):
    content_data = []
    contents = driver.find_elements(By.CSS_SELECTOR, "#contents #content")

    for content in contents:
        data = {
            "콘텐츠 주소": extract_content_url(content),
            "콘텐츠 이미지 URL": extract_content_image_url(content),
            "콘텐츠 명": extract_content_name(content)
        }

        try:
            metadata_line = content.find_element(By.ID, "metadata-line")
            spans = metadata_line.find_elements(By.CLASS_NAME, "inline-metadata-item.style-scope.ytd-video-meta-block")
            if len(spans) > 1:
                time_text = spans[1].text.strip()
                data["콘텐츠 공개 연도"] = calculate_content_year(time_text, today).strftime('%Y-%m-%d')
        except:
            data["콘텐츠 공개 연도"] = None


        print(f'data : {data}')

        content_data.append(data)
    return content_data

# 엑셀 파일로 저장하는 함수
def save_to_excel(content_data, file_name="youtube_content_data.xlsx"):
    df = pd.DataFrame(content_data)
    df.to_excel(file_name, index=False)

# 메인 함수
def main():
    url = "https://www.youtube.com/@OKAKOREA/videos"  # 크롤링할 유튜브 채널 URL 설정
    today = datetime.today()

    # 드라이버 설정 및 페이지 열기
    driver = setup_driver()
    if not driver:
        return

    driver.get(url)
    time.sleep(3)  # 초기 페이지 로딩 대기

    all_content_data = []
    last_height = driver.execute_script("return document.documentElement.scrollHeight")

    while True:
        # 콘텐츠 리스트 크롤링
        new_content_data = create_content_list(driver, today)

        # 새로운 데이터가 없으면 종료
        if new_content_data == all_content_data:
            print("더 이상 새로운 콘텐츠가 없습니다. 크롤링 종료.")
            break
        all_content_data = new_content_data

        # 스크롤 내리고 2초 대기
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)

        # 새로운 높이를 확인하여 이전과 같으면 종료
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            print("더 이상 스크롤할 내용이 없습니다.")
            break
        last_height = new_height

    # 엑셀 파일로 저장
    save_to_excel(all_content_data)

    # 브라우저 종료
    driver.quit()

if __name__ == "__main__":
    main()
