import time
from src.workers.main.api_base_worker import BaseApiWorker
from selenium.webdriver.common.by import By


# API
class ApiAritziaSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("ARITZIA", checked_list)

    # 제품 목록 가져오기
    def selenium_get_product_list(self, main_url: str):

        # 쿠키 수락 버튼 클릭
        # "3" 버튼 클릭
        try:
            # Sticky_viewItem__7OMDF 클래스를 가진 요소 찾기 (3개 중 3번째 요소 클릭)
            view_items = self.driver.find_elements(By.CLASS_NAME, "Sticky_viewItem__7OMDF")
            if len(view_items) >= 3:
                view_items[2].click()
                time.sleep(3)
        except Exception as e:
            self.log_func(f"3 버튼 클릭 실패: {e}")
        
        # 스크롤
        self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)

        self.log_func('상품목록 수집시작... 1분 이상 소요 됩니다. 잠시만 기다려주세요')
        product_list = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="plp-product-tile-12"]')
        self.log_func(f'추출 목록 수: {len(product_list)}')
        for product in product_list:
            try:
                product_id = str(product.get_attribute("data-mpid"))
                # 안전한 방식
                a_tag = product.find_element(By.TAG_NAME, "a")
                if a_tag:
                    href = a_tag.get_attribute("href")
                    if not href.startswith("http"):
                        href = self.base_url + href
                    if href:
                        key = (product_id, href)
                        if not product_id or not href or key in self.seen_keys:
                            continue  # 중복이면 건너뜀
                        self.product_list.append({
                            "url": href,
                            "product_id": product_id
                        })
                        self.seen_keys.add(key)
                else:
                    self.log_func(f"[경고] a 태그 없음 - product_id: {product_id}")
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

        # 첫번째 이미지 가져오기
        try:
            img_tag = self.driver.find_element(By.TAG_NAME, "img")
            img_src = img_tag.get_attribute('src')
            if not img_src:
                img_src = ""
                error = "이미지 srcset 속성이 비어있습니다."
        except Exception as e:
            error = f'이미지 src 추출 실패 : {e}'

        # 제품명 class=""
        try:
            name_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="product-name-text"]')
            product_name = name_element.text.strip()
        except Exception as e:
            error = f'제품명 추출 실패 : {e}'

        # 가격
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="product-list-price-text"]')
            if element:
                price = element.text.strip()
        except Exception as e:
            error = f'가격 추출 실패 : {e}'
            self.log_func("가격 추출 실패")

        # 제품 설명
        try:
            container = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="product-description"]')
            inner_ps = container.find_elements(By.TAG_NAME, "p")

            if len(inner_ps) >= 2:
                # 두 번째 div 안에서 p 태그 찾기
                paragraph = inner_ps[1]
                content = paragraph.text.strip()
        except Exception as e:
            error = f'제품 설명 가져오기 실패 : {e}'
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
