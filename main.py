from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import pandas as pd

# Excel 저장 경로
excel_file_path = r'D:\GIT\크롤링\부동산\네이버\~2025.03.11_쌍촌동네이버(테스트).xlsx'

# 경로 유효성 검사
try:
    with open(excel_file_path, 'w'):
        pass
except Exception as e:
    print("에러 발생:", e)
    print("저장 경로가 올바르지 않습니다. 크롤링을 중단합니다.")
    exit()

# 드라이버 초기화 함수
def initialize_driver():
    return webdriver.Chrome()

# 안전하게 텍스트 추출하는 함수
def safe_find_text(driver, by, value):
    try:
        return driver.find_element(by, value).text
    except NoSuchElementException:
        return ""

# 중복 텍스트 제외 필터
제외문구 = ["양지공인중개사사무소", "피터팬의 좋은방구하기 제공", "부동산114 제공", "아실", "강호"]

# 드라이버 시작 및 페이지 접근
driver = initialize_driver()
driver.get("https://new.land.naver.com/offices?ms=35.1546,126.863,16&a=SG&b=B2&e=RETAIL&u=ONEFLOOR&ad=true")
time.sleep(1)

data_list = []
wait = WebDriverWait(driver, 10)

try:
    for i in range(1, 99999):
        if i == 20:
            break
        try:
            매물_selector = f"#listContents1 > div > div > div:nth-child(1) > div:nth-child({i}) > div"
            매물요소 = driver.find_elements(By.CSS_SELECTOR, 매물_selector)

            if 매물요소:
                매물요소[0].location_once_scrolled_into_view
                clickable = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 매물_selector)))
                time.sleep(2)

                text = clickable.text
                if not any(word in text for word in 제외문구):
                    clickable.click()
                    time.sleep(2)

                    등록일자 = safe_find_text(driver, By.CSS_SELECTOR,
                                          "#ct > div.map_wrap > div.detail_panel > div > div.detail_contents_inner > div.detail_fixed > div.main_info_area > div.info_label_wrap.is-function > span.label.label--confirm > em.data")

                    if "24.05.00." in 등록일자:
                        print("등록일자에 특정 단어가 포함되어 크롤링을 중단합니다.")
                        break

                    data = {
                        '등록일자': 등록일자,
                        '매물번호': safe_find_text(driver, By.XPATH, "//th[contains(text(), '매물번호')]/following-sibling::td"),
                        '위치': safe_find_text(driver, By.XPATH, "//th[contains(text(), '소재지')]/following-sibling::td"),
                        '업종': safe_find_text(driver, By.XPATH, "//th[contains(text(), '현재업종')]/following-sibling::td"),
                        '층수': safe_find_text(driver, By.XPATH, "//th[contains(text(), '해당층')]/following-sibling::td"),
                        '방향': safe_find_text(driver, By.XPATH, "//th[contains(text(), '방향')]/following-sibling::td"),
                        '용도': safe_find_text(driver, By.XPATH, "//th[contains(text(), '건축물 용도')]/following-sibling::td"),
                        '사용승인일': safe_find_text(driver, By.XPATH, "//th[contains(text(), '사용승인일')]/following-sibling::td"),
                        '주차': safe_find_text(driver, By.XPATH, "//th[contains(text(), '총주차대수')]/following-sibling::td"),
                        '매물특징': safe_find_text(driver, By.XPATH, "//th[contains(text(), '매물특징')]/following-sibling::td"),
                        '면적': safe_find_text(driver, By.XPATH, "//th[contains(text(), '계약') or contains(text(), '전용면적')]/following-sibling::td"),
                        '가격': safe_find_text(driver, By.XPATH, "//span[@class='price']")
                    }

                    # 데이터 출력 (옵션)
                    for key, value in data.items():
                        print(f"{key}: {value}")
                    print("-" * 50)

                    data_list.append(data)

        except Exception as e:
            print(f"{i}번째 매물 처리 중 에러 발생:", e)
            continue

finally:
    # 결과 저장
    df = pd.DataFrame(data_list)
    df.to_excel(excel_file_path, index=False)
    print(f"\n총 {len(data_list)}건 저장 완료 → {excel_file_path}")

    # 브라우저 종료
    driver.quit()