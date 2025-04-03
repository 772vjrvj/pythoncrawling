import time
from selenium.common.exceptions import NoSuchElementException
from src.workers.main.api_base_worker import BaseApiWorker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

# API
class ApiGoogleMapSetLoadWorker(BaseApiWorker):
    def __init__(self, name,item_list):
        super().__init__(name, item_list)


    def selenium_get_product_list(self, index: int, item: str):
        self.driver.get(self.base_url)

        search_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )

        # 확실한 초기화 방법: clear() 후 backspace/delete 키 반복 전송
        search_input.click()
        search_input.clear()

        # 기존 내용을 완벽히 지우기 위한 확실한 조작 추가
        search_input.send_keys(Keys.CONTROL + "a")  # Ctrl + A 전체 선택
        search_input.send_keys(Keys.DELETE)  # Delete 키 눌러서 삭제
        time.sleep(0.3)

        search_input.send_keys(item)
        time.sleep(0.5)

        # 4. 검색 버튼 클릭
        # Enter 키를 눌러 검색 실행
        search_input.send_keys(Keys.ENTER)

        time.sleep(3)  # 검색 결과 대기 (필요 시 더 조절)

        self.driver_manager.scroll_to_bottom_of_feed()

        results = []

        # 정확히 class="UaQhfb fontBodyMedium"인 div 찾기
        place_elements = self.driver.find_elements(
            By.XPATH, '//div[@class="UaQhfb fontBodyMedium"]'
        )

        for idx, place in enumerate(place_elements, start=1):
            try:
                # title: 정확히 class="qBF1Pd fontHeadlineSmall " 인 요소
                title_element = place.find_element(
                    By.XPATH, './/div[@class="qBF1Pd fontHeadlineSmall "]'
                )
                title = title_element.text.strip()

                # place 바로 아래의 class="W4Efsd" 2개 중 두 번째
                w4efsd_direct_children = place.find_elements(
                    By.XPATH, './div[@class="W4Efsd"]'
                )
                if len(w4efsd_direct_children) < 2:
                    continue

                second_w4efsd = w4efsd_direct_children[1]

                # 그 안의 class="W4Efsd" 두 개 중 첫 번째에서 주소 추출
                inner_w4efsd = second_w4efsd.find_elements(
                    By.XPATH, './div[@class="W4Efsd"]'
                )
                if len(inner_w4efsd) < 1:
                    continue

                address = inner_w4efsd[0].text.strip().replace('\n', ' ')
                obj = {
                    "product_id": f"{index}_{idx}",
                    "title": title,
                    "address": address,
                    "keyword": item
                }

                self.log_func(f'{obj}')

                results.append(obj)

                self.csv_appender.append_row(obj)

            except Exception as e:
                print(f"[에러] 요소 파싱 중 오류 발생: {e}")
                continue




    # 상세목록
    def selenium_get_product_detail_list(self):
        pass