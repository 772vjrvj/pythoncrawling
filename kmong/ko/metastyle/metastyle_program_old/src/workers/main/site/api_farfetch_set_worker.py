import re
import time

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.workers.main.api_base_worker import BaseApiWorker


# API
class ApiFarfetchSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("FARFETCH", checked_list)

    def init_set(self):
        self.refresh_if_429()
        self.click_close_button()
        self.selenium_set_region()

    # 제품 목록 가져오기
    def selenium_get_product_list(self, product_url):
        page = 1
        while True:
            if product_url.endswith("items.aspx"):
                url = f'{product_url}?page={page}'
            else:
                url = f'{product_url}&page={page}'
            self.driver.get(url)
            time.sleep(3)  # 페이지 로딩 대기
            self.refresh_if_429()
            self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)
            time.sleep(3)
            try:
                product_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='productCard']"))
                )
            except TimeoutException:
                self.log_func("🔴 상품을 찾을 수 없습니다. 종료합니다.")
                break  # 상품이 없으면 종료
            time.sleep(3)
            for product in product_list:
                try:
                    a_tag = product.find_element(By.TAG_NAME, "a")
                    if a_tag:
                        href = a_tag.get_attribute("href")
                        if href:
                            if not href.startswith(self.base_url):
                                href = self.base_url + href

                            # 정규식을 사용하여 product_id 추출 (숫자만 찾기)
                            product_id_match = re.search(r"item-(\d+)", href)
                            product_id = product_id_match.group(1) if product_id_match else ""

                            key = (product_id, href)
                            if not product_id or not href or key in self.seen_keys:
                                continue  # 중복이면 건너뜀

                            self.product_list.append({
                                "product_id": product_id,
                                "url": href
                            })
                            self.seen_keys.add(key)

                except (NoSuchElementException, TimeoutException):
                    self.log_func("⚠️ a 태그를 찾을 수 없습니다. 다음 상품으로 넘어갑니다.")
            page += 1  # 다음 페이지로 이동

        self.log_func('상품목록 수집완료...')

    # 상세목록
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:

        self.driver.get(url)
        self.refresh_if_429()
        time.sleep(2)  # 페이지 로딩 대기

        error = ""
        img_src = ""
        product_name = ""
        price = ""
        content = ""
        brand = ""

        # 첫번째 이미지 가져오기
        try:
            image_containers = self.driver.find_elements(By.CSS_SELECTOR, '.ltr-bjn8wh.ed0fyxo0')
            if len(image_containers) >= 2:
                img = image_containers[1].find_element(By.TAG_NAME, 'img')
                img_src = img.get_attribute('src')
            else:
                img_src = None
        except Exception as e:
            error = f'이미지 src 추출 실패 : {e}'
            self.log_func(f"이미지 src 추출 실패")

        # 제품명
        try:
            product_name = self.driver.find_element(By.CSS_SELECTOR, '.ltr-13ze6d5-Body.efhm1m90').text.strip()
        except Exception as e:
            error = f'제품명 추출 실패 : {e}'
            self.log_func(f"제품명 없음")

        # 가격
        try:
            price = self.driver.find_element(By.CSS_SELECTOR, '.ltr-s7112i-Heading.ehhcbme0').text.strip()
        except Exception as e:
            error = f'가격 추출 실패 : {e}'
            self.log_func(f"가격 없음")

        # 설명
        try:
            desc_block = self.driver.find_element(By.CSS_SELECTOR, 'div.ltr-fzg9du.e1yiqd0 ul._fdc1e5')
            desc_items = desc_block.find_elements(By.TAG_NAME, 'li')
            content = [li.text.strip() for li in desc_items]
        except Exception as e:
            error = f'설명 추출 실패 : {e}'
            self.log_func(f"설명 없음")

        # brand
        try:
            brand = self.driver.find_element(By.CSS_SELECTOR, '.ltr-183yg4m-Body-Heading-HeadingBold.e1h8dali1').text.strip()
        except Exception as e:
            error = f'brand 추출 실패 : {e}'
            self.log_func(f"brand 없음")

        categories = name.split(" _ ")

        return {
            "website"       : self.name,
            "brandType"     : self.brand_type,
            "category"      : categories[0],
            "categorySub"   : categories[1],
            "url"           : self.base_url,
            "categoryFull"  : name,
            "country"       : self.country,
            "brand"         : brand,
            "productUrl"    : url,
            "product"       : product_name,
            "productId"     : product_id,
            "productNo"     : no,
            "description"   : content,
            "price"         : price,
            "imageNo"       : '1',
            "imageUrl"      : img_src,
            "imageName"     : f'{product_id}_1.jpg',
            "success"       : "Y",
            "regDate"       : "",
            "page"          : "",
            "error"         : error,
            "imageYn"       : "Y",
            "imagePath"     : "",
            "projectId"     : "",
            "bucket"        : ""
        }


    def click_close_button(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="btnClose"]')))
            close_btn.click()
            self.log_func("✅ 닫기 버튼 클릭 완료")
        except Exception as e:
            self.log_func(f"❌ 닫기 버튼 없음")


    def refresh_if_429(self):
        wait_time = 5  # 초기 대기 시간 (초)
        max_wait = 60  # 최대 대기 시간 제한 (원하는 만큼 조절 가능)

        while True:
            try:
                h1 = self.driver.find_element(By.TAG_NAME, "h1")
                if "429 Too Many Requests" in h1.text:
                    self.log_func(f"⏳ 429 감지됨. {wait_time}초 대기 후 새로고침합니다.")
                    time.sleep(wait_time)
                    self.driver.refresh()
                    wait_time = min(wait_time + 1, max_wait)  # 1초씩 증가, 최대 max_wait
                else:
                    self.log_func("✅ 429 메시지 없음. 정상 접속됨.")
                    break
            except Exception:
                self.log_func(f"❌ h1 태그가 없음")
                break  # 예외 발생 시 루프 종료 (필요 시 continue로 바꿀 수 있음)


    def selenium_set_region(self):

        wait = WebDriverWait(self.driver, 10)

        try:
            # 1. flash-notification 버튼 클릭
            flash_btn = wait.until(EC.element_to_be_clickable((By.ID, "flash-notification")))
            flash_btn.click()
            time.sleep(1)  # 1초 대기

            # 2. TabList에서 두 번째 버튼 (Region) 클릭
            tab_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component="TabList"]')))
            tabs = tab_list.find_elements(By.TAG_NAME, "button")
            if len(tabs) >= 2:
                tabs[1].click()
            else:
                self.log_func("Tab 버튼이 2개 미만입니다.")
                return

            # 3. PopperContainer 안의 input에 'us' 입력
            search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component="PopperContainer"] input[data-component="SearchInputControlled"]')))
            search_input.clear()
            search_input.send_keys("us")

            # 4. 'United States' 버튼 클릭
            us_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="btn-region-us"]')))
            us_button.click()
            time.sleep(2)

            self.log_func("✅ 지역이 United States로 변경되었습니다.")

        except Exception as e:
            self.log_func(f"❌ 지역 화면 없음", )
