import time

from selenium.common import NoSuchElementException

from src.workers.main.api_base_worker import BaseApiWorker
from selenium.webdriver.common.by import By


# API
class ApiMangoSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("MANGO", checked_list)

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

        self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)

        self.log_func('상품목록 수집시작... 1분 이상 소요 됩니다. 잠시만 기다려주세요')
        grid_container = self.driver.find_element(By.CLASS_NAME, "Grid_grid__fLhp5.Grid_overview___rpEH")
        product_list = grid_container.find_elements(By.TAG_NAME, "li")
        self.log_func(f'추출 목록 수: {len(product_list)}')
        for product in product_list:
            try:
                data_slot = product.get_attribute("data-slot")
                product_id = data_slot.replace(":", "_")

                # 안전한 방식
                a_tags = product.find_elements(By.TAG_NAME, "a")
                if a_tags:
                    href = a_tags[0].get_attribute("href")
                    if href:
                        self.product_list.append({
                            "url": href,
                            "product_id": str(product_id)
                        })
                else:
                    self.log_func(f"[경고] a 태그 없음 - data-slot: {data_slot}")

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
            image_grid = self.driver.find_element(By.CLASS_NAME, "ImageGrid_imageGrid__0lrrn")
            li_element = image_grid.find_element(By.TAG_NAME, "li")
            img_tag = li_element.find_element(By.TAG_NAME, "img")
            srcset = img_tag.get_attribute("srcset")
            if srcset:
                img_src = srcset.split(",")[0].split(" ")[0]
            else:
                img_src = ""
                error = "이미지 srcset 속성이 비어있습니다."
        except Exception as e:
            error = f'이미지 src 추출 실패 : {e}'

        # 제품명
        try:
            name_element = self.driver.find_element(By.CLASS_NAME, "ProductDetail_title___WrC_.texts_titleL__HgQ5x")
            product_name = name_element.text.strip()
        except Exception as e:
            error = f'제품명 추출 실패 : {e}'

        # 가격
        try:
            elements  = self.driver.find_elements(By.CSS_SELECTOR, "span.SinglePrice_center__mfcM3.texts_bodyM__lR_K7")
            if elements:
                price = elements[0].text.strip()
        except Exception as e:
            error = f'가격 추출 실패 : {e}'

        # 설명
        try:
            description_element = self.driver.find_element(By.ID, "truncate-text")
            paragraphs = description_element.find_elements(By.TAG_NAME, "p")
            content = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
        except Exception as e:
            error = f'설명 추출 실패 : {e}'

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