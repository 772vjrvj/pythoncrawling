from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, NoSuchElementException
from time import sleep
import pandas as pd
import os

def wait_until_element_present(driver, by, value, wait_time=30):
    element_present = EC.presence_of_element_located((by, value))
    WebDriverWait(driver, wait_time).until(element_present)

def wait_until_page_changed(driver, current_url, wait_time=30):
    def page_changed(driver):
        return driver.current_url != current_url

    WebDriverWait(driver, wait_time).until(page_changed)

def switch_to_new_tab(driver):
    driver.switch_to.window(driver.window_handles[-1])

def switch_to_main_tab(driver):
    driver.switch_to.window(driver.window_handles[0])

def close_current_tab(driver):
    driver.close()

# 저장할 폴더 지정
# save_folder = r"N:\개인\파이썬\쌍촌동"
save_folder = r"D:\GIT\크롤링\한방\쌍촌동"
# 웹 드라이버 초기화
driver = webdriver.Chrome()

# 웹페이지 열기
url = "https://karhanbang.com/map/?topM=03&gure_cd=3&mamulGubun=07&cate_cd=14&sido=%EA%B4%91%EC%A3%BC%EA%B4%91%EC%97%AD%EC%8B%9C&gugun=%EC%84%9C%EA%B5%AC&dong=%EC%8C%8D%EC%B4%8C%EB%8F%99&sido_no=6&gugun_no=113&dong_no=4822&hDong_no=&danji_no=&schType=3&tab_gubun=map&gugun_chk=&danji_name=&schGongMeter=&schdanjiDongNm=&schdanjiCurrFloor=&stateCheck=&trade_yn=&txt_amt_sell_s=&txt_amt_sell_e=&txt_amt_guar_s=&txt_amt_guar_e=&txt_amt_month_s=&txt_amt_month_e=&txt_amt_month2_s=&txt_amt_month2_e=&sel_area=&txt_area_s=&txt_area_e=&txt_room_cnt_s=&txt_room_cnt_e=&won_room_cnt=&txt_const_year=&txt_estimate_meter_s=&txt_estimate_meter_e=&sel_area3=&txt_area3_s=&txt_area3_e=&sel_building_use_cd=&sel_gunrak_cd=&sel_area5=&txt_area5_s=&txt_area5_e=&sel_area6=&txt_area6_s=&txt_area6_e=&txt_floor_high_s=&txt_floor_high_e=&officetel_use_cd=&sel_option_cd=&txt_land_s=&txt_land_e=&sel_jimok_cd=&txt_road_meter_s=&txt_road_meter_e=&sel_store_use_cd=&sel_sangga_cd=&sangga_cd=&sangga_chk=&sel_sangga_ipji_cd=&sel_office_use_cd=&orderByGubun=&regOrderBy=&confirmOrderBy=&meterOrderBy=&priceOrderBy=&currFloorBy=&chk_rentalhouse_yn=NN&chk_soon_move_yn=NN&chk_kyungmae_yn=NN&txt_yong_jiyuk2_nm=&txt_amt_dang_s=&txt_amt_dang_e=&maxLat=&maxLng=&minLat=&minLng=&gong_meter_s=&gong_meter_e=&gun_meter_s=&gun_meter_e=&toji_meter_s=&toji_meter_e=&txt_const_year_s=&txt_const_year_e=&txt_curr_floor_s=&txt_curr_floor_e=&marker_lat=&marker_lng=&lat=&lng=&page=1&flag=D&mapGubun=N&ftGubun=Y"
driver.get(url)

# 페이지 로딩을 기다릴 최대 시간(초) 설정
wait_time = 30

# 크롤링 결과를 저장할 빈 리스트
results = []

# Selenium Implicit Wait 설정
driver.implicitly_wait(5)  # 5초 동안 대기

try:
    # 폴더가 존재하는지 확인
    if not os.path.exists(save_folder):
        raise FileNotFoundError("지정된 폴더가 존재하지 않습니다.")

    while True:
        # 로딩이 완료되고, 클릭 가능한 상태일 때까지 대기
        wait_until_element_present(driver, By.CSS_SELECTOR, '#mamul_list_div > div > div.list_group > div.inr > ul > li')

        # 현재 페이지 URL 저장
        current_page_url = driver.current_url

        # 매물 목록의 각 항목에 대해 반복
        mamul_items = driver.find_elements(By.CSS_SELECTOR, '#mamul_list_div > div > div.list_group > div.inr > ul > li')
        for index, mamul_item in enumerate(mamul_items, start=1):
            # 특정 부동산 확인
            특정부동산들 = ["특정단어1", "특정단어2", "특정단어3"]
            if any(부동산 in mamul_item.text for 부동산 in 특정부동산들):
                print(f"특정부동산이 포함되어 있어 매물 {index}은 클릭하지 않습니다.")
                continue

            try:
                # 상세페이지 클릭
                mamul_item.click()

                # 새 창으로 전환
                switch_to_new_tab(driver)

                # 로딩이 완료되고, 요소가 나타날 때까지 대기
                wait_until_element_present(driver, By.CSS_SELECTOR, '#contents > div.dateArea.clearFix > dl > dt > table > tbody > tr > td:nth-child(2) > font:nth-child(2)')

                # 등록일을 찾아서 텍스트 출력
                등록일_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#contents > div.dateArea.clearFix > dl > dt > table > tbody > tr > td:nth-child(2) > font:nth-child(2)')))
                등록일_text = 등록일_element.text

                # 특정 단어가 등록일에 포함되어 있는지 확인
                if "재전송일 : 24.11.00 l" in 등록일_text:
                    print("등록일에 특정 단어가 포함되어 크롤링을 중단합니다.")
                    break

                # 매물번호를 찾아서 텍스트 출력
                매물번호_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#contents > div.dateArea.clearFix > dl > dt > table > tbody > tr > td:nth-child(2) > font:nth-child(3)')))
                매물번호_text = 매물번호_element.text

                # 위치를 찾아서 텍스트 출력
                try:
                    위치_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "위치")]/following-sibling::span')))
                    위치_text = 위치_element.text
                except TimeoutException:
                    위치_text = "위치 정보 없음"

                # 추천1을 찾아서 텍스트 출력
                try:
                    추천1_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "추천1")]/following-sibling::span')))
                    추천1_text = 추천1_element.text
                except TimeoutException:
                    추천1_text = "추천1 정보 없음"

                # 층/총층을 찾아서 텍스트 출력
                try:
                    층_총층_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "층/총층")]/following-sibling::span')))
                    층_총층_text = 층_총층_element.text
                except TimeoutException:
                    층_총층_text = "층/총층 정보 없음"

                # 방향을 찾아서 텍스트 출력
                try:
                    방향_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "방향")]/following-sibling::span')))
                    방향_text = 방향_element.text
                except TimeoutException:
                    방향_text = "방향 정보 없음"

                # 건축물용도를 찾아서 텍스트 출력
                try:
                    건축물용도_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "건축물용도")]/following-sibling::span')))
                    건축물용도_text = 건축물용도_element.text
                except TimeoutException:
                    건축물용도_text = "건축물용도 정보 없음"

                # 사용승인일을 찾아서 텍스트 출력
                try:
                    사용승인일_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "사용승인일")]/following-sibling::span')))
                    사용승인일_text = 사용승인일_element.text
                except TimeoutException:
                    사용승인일_text = "사용승인일 정보 없음"

                # 매물특징 요소 텍스트 출력
                매물특징_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#contents > div.detailviwe_group > div.mamul_information > div.feature_box > span')))
                매물특징_text = 매물특징_element.text

                # id_meter 요소 텍스트 출력
                id_meter_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#id_meter')))
                id_meter_text = id_meter_element.text

                # 마지막 요소 텍스트 출력
                마지막_element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#contents > div.detailviwe_group > div.inr > div.mamul_title > span.deposit > em')))
                마지막_text = 마지막_element.text

                # 결과를 딕셔너리로 저장
                result_dict = {
                    '등록일': 등록일_text,
                    '매물번호': 매물번호_text,
                    '위치': 위치_text,
                    '추천1': 추천1_text,
                    '층/총층': 층_총층_text,
                    '방향': 방향_text,
                    '건축물용도': 건축물용도_text,
                    '사용승인일': 사용승인일_text,
                    '매물특징': 매물특징_text,
                    'id_meter': id_meter_text,
                    '마지막': 마지막_text,
                }

                # 결과를 리스트에 추가
                results.append(result_dict)

            except NoSuchElementException as e:
                print(f"매물 {index} - 해당 요소가 없어 무시합니다. 에러 메시지: {e}")

            finally:
                # 현재 창 닫기
                close_current_tab(driver)

                # 이전 창으로 전환
                switch_to_main_tab(driver)

        # 특정 단어가 등록일에 포함되지 않았을 때만 다음 페이지로 이동
        else:
            # 다음 매물 페이지로 이동
            current_page = int(driver.current_url.split('&page=')[-1].split('&')[0])
            next_page_url = driver.current_url.replace(f'&page={current_page}', f'&page={current_page + 1}')

            # 대기 시간 설정
            next_page_wait_time = 5

            while True:
                try:
                    # 세션 ID 유효성 확인
                    driver.execute_script("return 1;")

                    # 세션 ID가 유효하면 페이지 이동
                    driver.get(next_page_url)
                    wait_until_page_changed(driver, current_page_url, wait_time=next_page_wait_time)
                    break
                except InvalidSessionIdException:
                    print("세션 ID가 유효하지 않습니다. 잠시 대기 후 다시 시도합니다.")
                    # 일정 시간 기다리기
                    sleep(3)
            continue
        # 특정 단어가 등록일에 포함되어 크롤링을 중단했을 때 반복문 종료
        break

except FileNotFoundError as e:
    print(f"에러 발생: {e}")

except TimeoutException:
    print("페이지 로딩이 제한 시간 내에 완료되지 않았거나 요소가 나타나지 않았습니다.")

except InvalidSessionIdException:
    print("세션 ID가 여러 번 유효하지 않습니다. 자동 크롤링을 중단합니다.")

finally:
    # 웹 드라이버 종료
    driver.quit()

    if results:
        # 결과를 DataFrame으로 변환
        df = pd.DataFrame(results)

        # 저장할 파일의 상대 경로 설정
        excel_file_path = os.path.join(save_folder, "~2025.03.11_쌍촌동한방.xlsx")

        # 엑셀로 저장
        df.to_excel(excel_file_path, index=False)

        print(f"크롤링 결과가 {excel_file_path}에 저장되었습니다.")
    else:
        print("크롤링 결과가 없습니다.")



