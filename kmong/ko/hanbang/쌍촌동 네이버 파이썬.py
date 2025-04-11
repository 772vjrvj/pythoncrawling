from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def initialize_driver():
    return webdriver.Chrome()

# 저장 경로 지정
excel_file_path = r'N:\개인\파이썬\쌍촌동\~2025.03.11_쌍촌동네이버(테스트).xlsx'  # 원하는 디렉토리 경로로 변경

# 저장 경로가 올바르지 않은 경우에는 크롤링을 실행하지 않음
try:
    with open(excel_file_path, 'w'):
        pass
except Exception as e:
    print("에러 발생:", e)
    print("저장 경로가 올바르지 않습니다. 크롤링을 중단합니다.")
    exit()

# 웹 드라이버 초기화
driver = initialize_driver()

# 주소로 이동
driver.get("https://new.land.naver.com/offices?ms=35.1546,126.863,16&a=SG&b=B2&e=RETAIL&u=ONEFLOOR&ad=true")

# 페이지 로딩 대기
time.sleep(1.0)

data_list = []

try:
    for i in range(1, 99999):
        try:
            # 매물이 있는지 확인
            매물 = driver.find_elements(By.CSS_SELECTOR, f"#listContents1 > div > div > div:nth-child(1) > div:nth-child({i}) > div")
            if len(매물) > 0:
                # 매물이 있는 위치로 스크롤
                driver.find_element(By.CSS_SELECTOR, f"#listContents1 > div > div > div:nth-child(1) > div:nth-child({i}) > div").location_once_scrolled_into_view

                # 네이버에서 보기 링크 확인
                네이버에서보기 = driver.find_elements(By.CSS_SELECTOR, f"#listContents1 > div > div > div:nth-child(1) > div:nth-child({i}) > div")

                # 네이버에서 보기 링크 클릭
                if len(네이버에서보기) > 0:
                    # 대기하여 클릭 가능한 상태가 될 때까지 기다림
                    wait = WebDriverWait(driver, 10)
                    네이버에서보기[0] = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"#listContents1 > div > div > div:nth-child(1) > div:nth-child({i}) > div")))

                    # 텍스트 확인
                    text = 네이버에서보기[0].text

                    # "양지공인중개사사무소" 텍스트가 아니라면 클릭 진행
                    if "양지공인중개사사무소" not in text and "피터팬의 좋은방구하기 제공" not in text and "부동산114 제공" not in text and "아실" not in text and "강호" not in text:
                        네이버에서보기[0].click()

                        # 페이지 로딩 대기
                        time.sleep(0.5)

                        # 데이터 가져오기
                        등록일자 = driver.find_element(By.CSS_SELECTOR, "#ct > div.map_wrap > div.detail_panel > div > div.detail_contents_inner > div.detail_fixed > div.main_info_area > div.info_label_wrap.is-function > span.label.label--confirm > em.data").text

                        # 특정 단어가 등록일자에 포함되어 있는지 확인
                        if "24.05.00." in 등록일자:
                            print("등록일자에 특정 단어가 포함되어 크롤링을 중단합니다.")
                            break

                        매물번호 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(12) > td:nth-child(4)").text
                        위치 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(1) > td").text
                        업종 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(8) > td:nth-child(2)").text
                        층수 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(4) > td:nth-child(2)").text
                        방향 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(7) > td:nth-child(4)").text
                        용도 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(11) > td:nth-child(2)").text
                        주차 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(9) > td:nth-child(4)").text
                        사용승인일 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(12) > td:nth-child(2)").text
                        매물특징 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(2) > td").text
                        면적 = driver.find_element(By.CSS_SELECTOR, "#detailContents1 > div.detail_box--summary > table > tbody > tr:nth-child(3) > td").text
                        가격 = driver.find_element(By.CSS_SELECTOR, "#ct > div.map_wrap > div.detail_panel > div > div.detail_contents_inner > div.detail_fixed > div.main_info_area > div.info_article_price > span.price").text

                        # 데이터 출력
                        print(등록일자)
                        print(매물번호)
                        print(위치)
                        print(업종)
                        print(층수)
                        print(방향)
                        print(용도)
                        print(사용승인일)
                        print(매물특징)
                        print(면적)
                        print(가격)
                        print("-" * 50)

                        # 데이터를 리스트에 추가
                        data = {
                            '등록일자': 등록일자,
                            '매물번호': 매물번호,
                            '위치': 위치,
                            '업종': 업종,
                            '층수': 층수,
                            '방향': 방향,
                            '용도': 용도,
                            '사용승인일': 사용승인일,
                            '매물특징': 매물특징,
                            '면적': 면적,
                            '가격': 가격
                        }

                        data_list.append(data)

        except Exception as e:
            print("에러 발생:", e)
            break

finally:
    # 크롤링이 끝난 후 데이터를 DataFrame으로 변환하고, Excel 파일로 저장
    df = pd.DataFrame(data_list)
    df.to_excel(excel_file_path, index=False)

    # 웹 드라이버 종료
    driver.quit()