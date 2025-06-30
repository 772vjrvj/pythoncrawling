from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd


# 💾 1. 데이터 클래스 정의
class PatentData:
    def __init__(self, reg_no):
        self.reg_no = str(reg_no).strip()


# 🔍 2. 검색 실행 함수
def search_patents(patent_list):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.kipris.or.kr/khome/main.do")
        time.sleep(2)

        search_box = driver.find_element(By.ID, "inputQuery")

        for patent in patent_list:
            print(f"🔍 검색 중: {patent.reg_no}")

            # 검색어 입력 및 실행
            search_box.clear()
            search_box.send_keys(patent.reg_no)
            time.sleep(0.3)
            search_box.send_keys(Keys.ENTER)

            time.sleep(3)  # 결과 페이지 대기

            # 다시 메인 페이지로 이동
            driver.get("https://www.kipris.or.kr/khome/main.do")
            time.sleep(3)

            # 새로고침 후 검색창 재지정
            search_box = driver.find_element(By.ID, "inputQuery")

        input("✅ 전체 검색 완료. 브라우저 닫으려면 Enter를 누르세요.")

    finally:
        driver.quit()


# 🧠 3. main 함수
def main():
    # Excel에서 데이터 읽기
    df = pd.read_excel("data.xlsx")

    # 등록번호 컬럼명 예시: '등록번호' (수정 가능)
    if '등록번호' not in df.columns:
        print("❌ '등록번호' 컬럼이 존재하지 않습니다.")
        return

    patent_list = [PatentData(reg_no) for reg_no in df['등록번호'] if pd.notna(reg_no)]

    if not patent_list:
        print("❌ 등록번호 데이터가 비어 있습니다.")
        return

    # 검색 실행
    search_patents(patent_list)


if __name__ == "__main__":
    main()
