from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
from datetime import datetime, timedelta
import time
import pytz


main_start_time = ""
main_end_time = ""
main_total_time = ""

start_time = ""
end_time = ""
total_time = ""


def get_url(page_no, current_date):
    formatted_date = current_date.strftime('%Y-%m-%d')
    url = f"https://section.blog.naver.com/Search/Post.naver?pageNo={page_no}&rangeType=PERIOD&orderBy=recentdate&startDate={formatted_date}&endDate={formatted_date}&keyword=%EC%84%9C%EC%9A%B8%20%EC%9B%A8%EC%9D%B4%ED%8C%85%20%EB%A7%9B%EC%A7%91"
    return url

def main():
    # Headless 모드 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless") #Headless 모드 활성화.
    chrome_options.add_argument("--disable-gpu") #GPU 비활성화 (일부 환경에서 필요).
    chrome_options.add_argument("--no-sandbox") # Linux 환경에서 안정성을 높이기 위해 추가.
    chrome_options.add_argument("--disable-dev-shm-usage") # Linux 환경에서 안정성을 높이기 위해 추가.

    # WebDriver 설정
    driver = webdriver.Chrome(options=chrome_options)

    # 시작 날짜와 끝 날짜 설정
    # 날짜별로 조회하는 이유는 한꺼번에 2022-01-01 ~ 2022-12-31 이렇게 하면 정확한 데이터가 안나온다.
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 1)

    titles = []  # 제목을 저장할 리스트

    current_date = start_date

    all_count = 0

    while current_date <= end_date:

        print(f"======================================")
        start_time = time.time()  # 시작 시간 기록
        get_current_time()


        page_no = 1
        start_url = get_url(page_no, current_date)
        driver.get(start_url)

        try:
            # 페이지 로딩 시 특정 요소가 나타날 때까지 기다립니다
            search_number_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'em.search_number'))
            )

            # 검색 결과 수 찾기
            search_number_text = search_number_element.text
            # 쉼표 제거 및 숫자만 추출
            # 숫자 문자열을 정수형으로 변환
            search_number = int(re.sub(r'[^\d]', '', search_number_text))

            print(f"날짜: {current_date}")
            print(f"전체 갯수: {search_number}")

            all_count = all_count + search_number

            # 7로 나누어 떨어지지 않으면 페이지 추가
            total_pages, remainder = divmod(search_number, 7)  # 페이지당 7개의 게시물
            if remainder > 0:
                total_pages += 1

            print(f"전체 페이지: {total_pages}")

            # 페이지 수만큼 for문 돌면서 크롤링
            for p in range(1, total_pages + 1):
                url = get_url(p, current_date)
                driver.get(url)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'strong.title_post .title'))
                )

                titles_elements = driver.find_elements(By.CSS_SELECTOR, 'strong.title_post .title')
                for title_element in titles_elements:
                    titles.append({
                        "제목" : title_element.text,
                        "날짜" : current_date.strftime('%Y-%m-%d'),
                    })

        except Exception as e:
            print(f"에러 발생: {e}")


        end_time = time.time()  # 시작 시간 기록

        total_time = end_time - start_time  # 총 걸린 시간 계산
        print(f"단위 걸린시간: {total_time} 초")

        total_time = end_time - main_start_time  # 총 걸린 시간 계산
        print(f"현재까지 걸린시간: {total_time} 초")

        get_current_time()
        print(f"======================================")


        current_date += timedelta(days=1)  # 하루씩 증가




    print(f"all_count: {all_count}")


    # WebDriver 종료
    driver.quit()

    # 데이터를 DataFrame으로 변환
    df = pd.DataFrame(titles, columns=["제목", "날짜"])

    # Excel 파일로 저장
    df.to_excel("titles.xlsx", index=False, engine='openpyxl')


def get_current_time():
    # 한국 시간대 정의
    korea_tz = pytz.timezone('Asia/Seoul')

    # 현재 시간을 UTC 기준으로 가져오기
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # 한국 시간으로 변환
    now_korea = now_utc.astimezone(korea_tz)

    # 시간을 "yyyy-mm-dd hh:mm:ss" 형식으로 포맷팅
    formatted_time_korea = now_korea.strftime('%Y-%m-%d %H:%M:%S')
    print(formatted_time_korea)


if __name__ == "__main__":
    main_start_time = time.time()  # 시작 시간 기록
    get_current_time()

    main()

    main_end_time = time.time()  # 종료 시간 기록
    get_current_time()

    main_total_time = main_end_time - main_start_time  # 총 걸린 시간 계산
    print(f"전체 걸린시간: {main_total_time} 초")