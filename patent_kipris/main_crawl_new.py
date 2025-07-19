from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd


# 💾 1. 데이터 클래스 정의
class PatentDetail:
    def __init__(self, ap, no, ipc):
        self.ap = str(ap).strip()
        self.no = str(no).zfill(7)  # 7자리 보존
        self.ipc = str(ipc).strip()


# 🔍 2. 검색 실행 함수
def search_patents(detail_list):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.kipris.or.kr/khome/main.do")
        time.sleep(2)

        for num, patent in enumerate(detail_list, start=1):
            print(f"🔍 상세검색 중: {num} - AP: {patent.ap}, NO: {patent.no}, IPC: {patent.ipc}")

            # 상세검색 열기
            driver.find_element(By.ID, "btnOpenSearchDetail").click()
            time.sleep(1)

            # IPC 입력
            ipc_input = driver.find_element(By.CSS_SELECTOR, 'input[data-field="IPC"]')
            ipc_input.clear()
            ipc_input.send_keys(patent.ipc)
            time.sleep(0.5)

            # AP 입력
            ap_input = driver.find_element(By.CSS_SELECTOR, 'input[data-field="AP"]')
            ap_input.clear()
            ap_input.send_keys(patent.ap)
            time.sleep(0.5)

            # 검색 버튼 클릭
            search_btn = driver.find_element(By.CSS_SELECTOR, 'button.btn-search[data-lang-id="adsr.search"]')
            search_btn.click()

            # 결과 대기
            time.sleep(3)

            # 메인 페이지로 돌아가기
            driver.get("https://www.kipris.or.kr/khome/main.do")
            time.sleep(2)

        input("✅ 전체 검색 완료. 브라우저 닫으려면 Enter를 누르세요.")

    finally:
        driver.quit()


# 🧠 3. main 함수
def main():
    # Sheet1 읽기 (상세 검색용)
    df1 = pd.read_excel("data_new.xlsx", sheet_name="Sheet1", dtype=str)
    if not {'AP', 'NO', 'IPC'}.issubset(df1.columns):
        print("❌ Sheet1에 AP, NO, IPC 컬럼이 존재하지 않습니다.")
        return

    detail_list = [
        PatentDetail(row['AP'], row['NO'], row['IPC'])
        for _, row in df1.iterrows()
        if pd.notna(row['NO']) and pd.notna(row['IPC']) and pd.notna(row['AP'])
    ]

    if not detail_list:
        print("❌ Sheet1에 유효한 데이터가 없습니다.")
        return

    # 상세검색 수행
    search_patents(detail_list)


if __name__ == "__main__":
    main()
