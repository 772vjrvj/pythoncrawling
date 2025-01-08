import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


def setup_driver():
    """Selenium WebDriver 설정"""
    chrome_options = Options()
    user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
    profile = "Default"

    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    chrome_options.add_argument(f"profile-directory={profile}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")  # 필요 시 활성화

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


def extract_data_from_new_divs(driver, collected_urls):
    """새로 추가된 HTML을 파싱하여 데이터 추출"""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    result = []

    # 최상위 div 탐색 (특정한 계층 구조)
    parent_div = soup.find("div", class_="xb57i2i x1q594ok x5lxg6s x78zum5 xdt5ytf x1ja2u2z x1pq812k x1rohswg xfk6m8 x1yqm8si xjx87ck xx8ngbg xwo3gff x1n2onr6 x1oyok0e x1e4zzel x1plvlek xryxfnj")
    if not parent_div:
        return result  # parent div가 없으면 빈 리스트 반환

    # 부모 div 내의 모든 추가된 div 가져오기
    new_divs = parent_div.find_all("div", class_="x78zum5 xdt5ytf x1iyjqo2 x1n2onr6")
    for new_div in new_divs:
        try:
            # 각 div의 고유 URL로 중복 검사
            url_tag = new_div.find("a")
            if url_tag and url_tag.get("href"):
                full_url = f"https://www.threads.net{url_tag['href']}"
                if full_url in collected_urls:
                    continue  # 이미 수집된 URL이면 무시
                collected_urls.add(full_url)  # 새로운 URL 추가

                # 데이터 추출
                obj = {"글본문": '', "좋아요": '', "url": full_url, "날짜": ''}

                # 글본문 추출
                text_div = new_div.find("div", class_="x78zum5 xdt5ytf")
                if text_div:
                    obj["글본문"] = text_div.get_text(strip=True)

                # 좋아요 및 날짜 추출
                like_div = new_div.find("span", class_="like-class-placeholder")  # 수정 필요
                if like_div:
                    obj["좋아요"] = like_div.get_text(strip=True)

                date_tag = new_div.find("time")
                if date_tag and date_tag.get("title"):
                    obj["날짜"] = date_tag["title"]

                result.append(obj)
        except Exception as e:
            print(f"오류 발생: {e}")

    return result


def scroll_and_collect_data(driver, url, max_scrolls=50):
    """스크롤하며 데이터 수집"""
    driver.get(url)
    time.sleep(3)  # 초기 로딩 대기

    collected_data = []
    collected_urls = set()  # 중복 방지용 URL 집합
    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(max_scrolls):
        # 새로 추가된 데이터 추출
        new_data = extract_data_from_new_divs(driver, collected_urls)
        print(f'new_data : {new_data}')
        collected_data.extend(new_data)

        # 스크롤 내리기
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 로딩 대기

        # 스크롤 종료 조건 확인
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # 더 이상 새로운 내용이 없으면 종료
        last_height = new_height

    return collected_data


def save_to_excel(data, output_file):
    """데이터를 엑셀 파일로 저장"""
    try:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"데이터가 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"엑셀 저장 중 오류 발생: {e}")


def main():
    url = "https://www.threads.net/@lecor.creator?igshid=NTc4MTIwNjQ2YQ%3D%3D"
    output_file = "extracted_data.xlsx"

    driver = setup_driver()
    if driver is None:
        print("드라이버 설정 실패")
        return

    try:
        collected_data = scroll_and_collect_data(driver, url)
        if collected_data:
            save_to_excel(collected_data, output_file)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
