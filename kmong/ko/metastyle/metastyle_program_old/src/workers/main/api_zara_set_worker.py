import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from src.workers.main.api_base_worker import BaseApiWorker


# API
class ApiZaraSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("ZARA", checked_list)

    # 제품 목록 가져오기
    def selenium_get_product_list(self, main_url: str):

        # 쿠키 수락 버튼 클릭
        try:
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_button.click()
            time.sleep(1)
            self.log_func("쿠키 수락 버튼 클릭 완료")
        except Exception as e:
            self.log_func(f"쿠키 수락 버튼 클릭 중 오류 발생: {e}", )

        # 국가 유지 버튼 클릭
        try:

            stay_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qa-action='stay-in-store']"))
            )
            stay_button.click()
            time.sleep(1)
            self.log_func("국가 유지 버튼 클릭 완료")
        except Exception as e:
            self.log_func(f"국가 유지 버튼 클릭 중 오류 발생: {e}", )

        # "3" 버튼 클릭
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.view-option-selector-button")
            for button in buttons:
                span = button.find_element(By.CSS_SELECTOR, "span.view-option-selector-button__option")
                if span.text.strip() == "3":
                    ActionChains(self.driver).move_to_element(button).click().perform()
                    time.sleep(2)
                    break  # 클릭했으면 반복 중단
        except Exception as e:
            self.log_func(f"3 버튼 클릭 실패: {e}")

        self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)

        self.log_func('상품목록 수집시작... 1분 이상 소요 됩니다. 잠시만 기다려주세요')
        product_list = self.driver.find_elements(By.CSS_SELECTOR, "li.product-grid-product")
        self.log_func(f'추출 목록 수: {len(product_list)}')
        # 결과 저장 리스트

        for product in product_list:
            if not self.running:  # 실행 상태 확인
                self.log_func("크롤링이 중지되었습니다.")
                break

            try:
                # 1. info-wrapper가 없으면 건너뛰기
                try:
                    info_wrapper = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__data > div.product-grid-product__info-wrapper")
                except NoSuchElementException:
                    continue

                # 2. "LOOK"인 경우 건너뛰기
                try:
                    name_tag = info_wrapper.find_element(By.CSS_SELECTOR, "a.product-grid-product-info__name")
                    product_name = name_tag.text.strip()
                    if product_name == "LOOK":
                        continue
                except NoSuchElementException:
                    continue

                # 3. 링크 및 상품 ID 수집
                try:
                    link_tag = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__figure a.product-grid-product__link")
                    href = link_tag.get_attribute("href")
                    product_id = product.get_attribute("data-productid")
                    if href and product_id:
                        self.product_list.append({
                            "url": href,
                            "product_id": str(product_id)
                        })
                except NoSuchElementException:
                    continue

            except Exception as e:
                self.log_func(f"상품 처리 중 오류 발생: {e}")
        self.log_func('상품목록 수집완료...')

    # 상세목록
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:
        self.driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기

        error = ""
        img_src = ""
        product_name = ""
        price = ""
        content = ""

        # 1. 지역 선택 버튼 클릭 (있다면)
        try:
            stay_btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa-action='stay-in-store']"))
            )
            stay_btn.click()
            self.log_func("지역 선택 버튼 클릭")
            time.sleep(1)
        except Exception as e:
            error = f"국가 유지 버튼 클릭 중 오류 발생: {e}"
            self.log_func(error)

        # 2. product-detail-view__main-content 영역
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-detail-view__main-content"))
        )

        # 이미지 src 추출
        try:
            img_tags = self.driver.find_elements(By.CSS_SELECTOR,
                                                 "img.media-image__image.media__wrapper--media")
            img_src = img_tags[0].get_attribute("src")
        except Exception as e:
            error = f'이미지 src 추출 실패 : {e}'
            self.log_func("❌ 제품 이미지 가져오기 실패")

        # 제품명
        try:
            product_name = self.driver.find_element(By.CSS_SELECTOR,
                                       "div.product-detail-view__main-info .product-detail-info__header-name").text.strip()
        except Exception as e:
            error = f'제품명 추출 실패 : {e}'
            self.log_func("❌ 제품 제품명 가져오기 실패")

        # 가격
        try:
            price = self.driver.find_element(By.CSS_SELECTOR,
                                        "div.product-detail-view__main-info .money-amount__main").text.strip()
        except Exception as e:
            error = f'가격 추출 실패 : {e}'
            self.log_func("❌ 제품 가격 가져오기 실패")

        # 설명
        try:
            content = self.driver.find_element(By.CSS_SELECTOR,
                                          "div.product-detail-view__main-info .expandable-text__inner-content").text.strip()
        except Exception as e:
            error = f'설명 추출 실패 : {e}'
            self.log_func("❌ 제품 설명 가져오기 실패")

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
            "error"         : error,
            "imageYn"       : "Y",
            "imagePath"     : "",
            "projectId"     : "",
            "bucket"        : ""
        }