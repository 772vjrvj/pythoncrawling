import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from src.workers.main.api_base_worker import BaseApiWorker


# API
class ApiZaraSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("ZARA", checked_list)

    # 초기화
    def init_set(self):
        self.log_func("초기화 시작")

    # 화면 처리
    def init_view_clear(self):
        # 1. 쿠키 수락 버튼 클릭
        try:
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_button.click()
            time.sleep(1)
            self.log_func("✅ 쿠키 수락 버튼 클릭 완료")
        except Exception as e:
            self.handle_selenium_exception("쿠키 버튼", e)

        # 2. 국가 유지 버튼 클릭
        try:
            stay_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qa-action='stay-in-store']"))
            )
            stay_button.click()
            time.sleep(1)
            self.log_func("✅ 국가 유지 버튼 클릭 완료")
        except Exception as e:
            self.handle_selenium_exception("국가 유지 버튼", e)

        # 3. 버튼 클릭 (뷰 옵션)
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.view-option-selector-button")
        except Exception as e:
            self.handle_selenium_exception("옵션 버튼 목록 찾기", e)
            return  # 더 진행할 수 없으므로 함수 종료

        found = False
        for button in buttons:
            try:
                span = button.find_element(By.CSS_SELECTOR, "span.view-option-selector-button__option")
                if span.text.strip() == "3":
                    ActionChains(self.driver).move_to_element(button).click().perform()
                    time.sleep(2)
                    self.log_func("✅ '3' 옵션 버튼 클릭 완료")
                    found = True
                    break
            except Exception as e:
                self.handle_selenium_exception("'3' 옵션 버튼 내부 span 찾기", e)

        if not found:
            self.log_func("⚠️ '3' 옵션 버튼을 찾지 못했습니다.")

    # 제품 목록 가져오기
    def selenium_get_product_list(self, main_url: str):
        self.driver.get(main_url)
        time.sleep(2)

        self.init_view_clear()

        self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)

        self.log_func('상품목록 수집시작... 1분 이상 소요 됩니다. 잠시만 기다려주세요')
        product_list = self.driver.find_elements(By.CSS_SELECTOR, "li.product-grid-product")

        try:
            product_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.product-grid-product"))
            )
        except Exception as e:
            self.handle_selenium_exception("product_list", e)


        self.log_func(f'추출 목록 수: {len(product_list)}')
        # 결과 저장 리스트

        for product in product_list:
            if not self.running:
                self.log_func("크롤링이 중지되었습니다.")
                break

            # 1. info-wrapper 확인
            info_wrapper = None
            try:
                info_wrapper = product.find_element(
                    By.CSS_SELECTOR,
                    "div.product-grid-product__data > div.product-grid-product__info-wrapper"
                )
            except Exception as e:
                self.handle_selenium_exception("info_wrapper", e)


            # 2. 상품명 확인 및 "LOOK" 필터링
            try:
                name_tag = info_wrapper.find_element(By.CSS_SELECTOR, "a.product-grid-product-info__name")
                product_name = name_tag.text.strip()
                if product_name.upper() == "LOOK":
                    self.log_func("🚫 'LOOK' 상품은 건너뜀")
                    continue
            except Exception as e:
                self.handle_selenium_exception("product_name", e)

            # 3. 링크 및 product_id 추출
            try:
                link_tag = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__figure a.product-grid-product__link")
                href = link_tag.get_attribute("href")
                product_id = product.get_attribute("data-productid")
                if href and product_id:
                    self.product_list.append({
                        "url": href,
                        "productId": str(product_id)
                    })
            except Exception as e:
                self.handle_selenium_exception("href 및 product_id", e)

        self.log_func('✅ 상품 목록 수집 완료')

    # 상세목록
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:
        self.log_func(f'상품 상세 목록 product_id : {product_id}')
        self.driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기

        img_src = ""
        product_name = ""
        price = ""
        content = ""

        # 이미지 src
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, "button.product-detail-image.product-detail-view__main-image")
            img = button.find_element(By.CSS_SELECTOR, "img.media-image__image.media__wrapper--media")
            img_src = img.get_attribute("src")
        except Exception as e:
            self.handle_selenium_exception("이미지 src 추출", e)

        # 제품명
        try:
            name_element = self.driver.find_element(By.CSS_SELECTOR,
                                                    "div.product-detail-view__main-info .product-detail-info__header-name")
            product_name = name_element.text.strip()
        except Exception as e:
            self.handle_selenium_exception("제품명", e)

        # 가격
        try:
            price_elem = self.driver.find_element(By.CSS_SELECTOR,
                                                  "div.product-detail-view__main-info .money-amount__main")
            price = price_elem.text.strip()
        except Exception as e:
            self.handle_selenium_exception("가격", e)

        # 설명
        try:
            content_elem = self.driver.find_element(By.CSS_SELECTOR,
                                                    "div.product-detail-view__main-info .expandable-text__inner-content")
            content = content_elem.text.strip()
        except Exception as e:
            self.handle_selenium_exception("설명", e)

        categories = name.split(" _ ")

        return {
            "website"       : self.name,
            "brandType"     : self.brand_type,
            "category"      : categories[0],
            "categorySub"   : categories[1],
            "url"           : self.base_url,
            "categoryFull"  : name,
            "country"       : self.country,
            "brand"         : self.name,
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
            "error"         : "",
            "imageYn"       : "Y",
            "imagePath"     : "",
            "projectId"     : "",
            "bucket"        : ""
        }