# ssg 로그인 (팝업창) 자동화 예제
# - 메인 페이지 접속
# - 로그인 버튼 클릭 → 팝업창 전환
# - ID / PW 입력 후 로그인 버튼 클릭
# - 이후 원하는 관리자/마이페이지 등으로 이동해서 크롤링하면 됨

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


SSG_MAIN_URL = "https://www.ssg.com/"

# 로그인 정보
LOGIN_ID = "ooos1103"
LOGIN_PW = "oktech431!@"

def main():
    # =========================
    # 1. 드라이버 세팅
    # =========================
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # 필요하면 user-agent, 헤드리스 등 추가 가능
    driver = webdriver.Chrome(options=options)

    wait = WebDriverWait(driver, 15)

    try:
        # =========================
        # 2. 메인 페이지 접속
        # =========================
        driver.get(SSG_MAIN_URL)

        # =========================
        # 3. 상단 GNB 로그인 버튼 클릭
        #    <div id="loginBtn"> ... </div> 이거 클릭
        # =========================
        login_btn_gnb = wait.until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn_gnb.click()

        # =========================
        # 4. 팝업창으로 전환
        # =========================
        main_handle = driver.current_window_handle

        # 새 창(팝업)이 열릴 때까지 기다렸다가, 새 핸들로 전환
        wait.until(lambda d: len(d.window_handles) > 1)

        login_handle = None
        for handle in driver.window_handles:
            if handle != main_handle:
                login_handle = handle
                break

        if login_handle is None:
            raise Exception("로그인 팝업 창을 찾지 못했습니다.")

        driver.switch_to.window(login_handle)

        # =========================
        # 5. 팝업 내 로그인 폼에 ID/PW 입력
        #    <input type="text" name="mbrLoginId" id="mem_id">
        #    <input type="password" name="password" id="mem_pw">
        # =========================
        id_input = wait.until(
            EC.presence_of_element_located((By.ID, "mem_id"))
        )
        pw_input = wait.until(
            EC.presence_of_element_located((By.ID, "mem_pw"))
        )

        id_input.clear()
        id_input.send_keys(LOGIN_ID)

        pw_input.clear()
        pw_input.send_keys(LOGIN_PW)

        # =========================
        # 6. 로그인 버튼 클릭
        #    <button ... id="loginBtn"><span>로그인</span></button>
        #    (팝업 안에도 id="loginBtn"일 수 있으니, 현재 창 기준으로 다시 찾음)
        # =========================
        login_submit_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_submit_btn.click()

        # =========================
        # 7. 로그인 완료 대기
        #    - 보통 팝업이 닫히거나, URL/요소 변화로 확인
        #    - 여기서는 "창이 1개만 남을 때"까지 기다리도록 처리
        # =========================
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) == 1)

        # 메인 창으로 다시 전환
        driver.switch_to.window(main_handle)

        # =========================
        # 8. 이제 로그인된 상태로 관리자/마이페이지 등 이동해서 크롤링
        # =========================
        # 예시: 마이페이지 같은 곳으로 이동 (실제 URL로 교체해서 사용)
        # driver.get("https://www.ssg.com/mypage/main.ssg")

        # 여기서부터는 평소처럼 find_elements 등으로 크롤링
        # ex)
        # some_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "원하는-selector")))
        # print(some_elem.text)

        print("로그인 절차까지 정상 수행 완료")

    finally:
        # 개발 중에는 바로 닫기 싫으면 주석 처리해서 확인하면서 쓰면 됨
        # driver.quit()
        pass


if __name__ == "__main__":
    main()
