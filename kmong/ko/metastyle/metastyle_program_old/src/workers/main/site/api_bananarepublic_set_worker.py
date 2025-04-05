import time
from selenium.common.exceptions import NoSuchElementException
from src.workers.main.api_base_worker import BaseApiWorker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# API
class ApiBananarepublicSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("BANANAREPUBLIC", checked_list)

    def init_set(self):
        self.log_func("초기화 시작")

    # 제품 목록 가져오기
    def selenium_get_product_list(self, product_url):
        page = 0
        while True:
            self.log_func(f"현재 페이지 {page}")
            if page == 0:
                url = f'{product_url}#pageId={page}' #은 spa방식이라 get(url)로 이동 안됌
                self.driver.get(url)
            else:
                try:
                    # 스크롤 많이 했을 수 있으니 다시 버튼 위치로 스크롤 조정
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Next Page"]'))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)  # 가운데로 가져오기
                    WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Next Page"]')))
                    time.sleep(0.3)
                    next_button.click()
                    self.log_func("다음 페이지 버튼 클릭 성공")
                except Exception as e:
                    self.handle_selenium_exception("다음 페이지 버튼 클릭", e)
                    break

            time.sleep(3)
            try:
                # SVG 아이콘이 나타날 때까지 대기 (최대 10초)
                svg_icon = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'svg[data-testid="large-grid-icon"]'))
                )

                # 클릭 가능한 상태인지 확인 후 클릭
                svg_icon.click()
            except Exception as e:
                self.handle_selenium_exception("3 버튼 클릭", e)

            time.sleep(1)
            self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)
            time.sleep(2)
            # 1. UL 태그 찾기 class="cat_product-image sitewide-15ltmfs"
            try:
                # 최대 10초 동안 div 요소들이 로드되기를 기다림
                div_elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.cat_product-image'))
                )
            except Exception as e:
                self.handle_selenium_exception("div_elements", e)
                break

            if not div_elements:
                self.log_func("ul 태그를 찾을 수 없습니다. 종료합니다.")
                break

            for div in div_elements:
                try:
                    full_id = div.get_attribute("id")
                    product_id = ""
                    if full_id and full_id.startswith("product"):
                        product_id = full_id[len("product"):]

                    a_tag = div.find_element(By.TAG_NAME, "a")

                    if a_tag:
                        href = a_tag.get_attribute("href")
                        if href:
                            if not href.startswith("http"):
                                href = self.base_url + href
                            key = (product_id, href)
                            if not product_id or not href or key in self.seen_keys:
                                continue  # 중복이면 건너뜀

                            self.product_list.append({
                                "product_id": product_id,
                                "url": href
                            })
                            self.seen_keys.add(key)
                except Exception as e:
                    self.handle_selenium_exception("product_id", e)

            page += 1  # 다음 페이지로 이동
        self.log_func('상품목록 수집완료...')

    # 상세목록
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:

        self.driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기

        img_src = ""
        product_name = ""
        price = ""
        content = ""

        # 이미지 src
        try:
            div = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="grid"]')
            img = div.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src')
        except Exception as e:
            self.handle_selenium_exception("이미지 src", e)

        # 제품명
        try:
            h1 = self.driver.find_element(By.TAG_NAME, 'h1')
            product_name = h1.text.strip()
        except Exception as e:
            self.handle_selenium_exception("제품명", e)

        # 가격
        try:
            # 1. div.amount-price 요소 찾기
            div = self.driver.find_element(By.CSS_SELECTOR, 'div.amount-price')
            # 2. 그 안에 있는 span 요소 찾기
            span = div.find_element(By.TAG_NAME, 'span')
            # 3. 텍스트 가져오기
            price = span.text.strip()  # 예: "$120.00"
        except Exception as e:
            self.handle_selenium_exception("가격", e)

        categories = name.split(" _ ")

        return {
            "website"        : self.name,
            "brandType"      : self.brand_type,
            "category"       : categories[0],
            "categorySub"    : categories[1],
            "url"            : self.base_url,
            "categoryFull"   : name,
            "country"        : self.country,
            "brand"          : self.name,
            "productUrl"     : url,
            "product"        : product_name,
            "productId"      : product_id,
            "productNo"      : no,
            "description"    : content,
            "price"          : price,
            "imageNo"        : '1',
            "imageUrl"       : img_src,
            "imageName"      : f'{product_id}_1.jpg',
            "success"        : "Y",
            "regDate"        : "",
            "page"           : "",
            "error"          : "",
            "imageYn"        : "Y",
            "imagePath"      : "",
            "projectId"      : "",
            "bucket"         : ""
        }
