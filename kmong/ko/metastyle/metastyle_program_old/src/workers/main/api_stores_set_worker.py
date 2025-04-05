import time
from selenium.common.exceptions import NoSuchElementException
from src.workers.main.api_base_worker import BaseApiWorker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# API
class ApiStoresSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("&OTHER STORIES", checked_list)


    def selenium_get_product_list(self, main_url: str):
        page = 1
        while True:
            url = f'{main_url}?page={page}'
            self.driver.get(url)
            time.sleep(2)
            current_url = self.driver.current_url  # 현재 페이지의 실제 URL 가져오기
            if 'page=' not in current_url:
                self.log_func("❌ page 파라미터 없음. 반복 중단.")
                break
            self.log_func(f"현제 page: {page}")
            self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)
            time.sleep(2)
            div_elements = []
            try:

                products_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'reloadProducts'))
                )
                if products_element:
                    div_elements = products_element.find_elements(By.CSS_SELECTOR, "div.o-product.producttile-wrapper")
            except NoSuchElementException:
                self.log_func("ul 태그를 찾을 수 없습니다. 종료합니다.")
                break  # 상품이 없으면 종료
            except TimeoutException:
                self.log_func("ul 태그를 찾을 수 없습니다. 종료합니다.")
                break

            for index, div in enumerate(div_elements, start=1):
                try:

                    product_id = div.get_attribute("data-product-id")
                    if product_id is None:
                        continue

                    a_tag = div.find_element(By.TAG_NAME, "a")
                    if a_tag is None:
                        continue

                    href = a_tag.get_attribute("href")
                    if not href:
                        continue
                    else:
                        self.product_list.append({
                            "product_id": product_id,
                            "url": href
                        })
                    self.log_func(f"product_id : {product_id} / index : {index}")
                except NoSuchElementException:
                    self.log_func("div안에 태그를 찾을 수 없습니다. 다음 상품으로 넘어갑니다.")
                    continue
                except Exception as e:
                    self.log_func(f"예기치 못한 오류 발생: {e}")
                    continue

            page += 1  # 다음 페이지로 이동
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
            picture = self.driver.find_element(By.CSS_SELECTOR, 'picture.a-picture')
            img = picture.find_element(By.CSS_SELECTOR, 'img.a-image') if picture else None

            # 우선순위: data-zoom-src → src
            img_src = img.get_attribute('data-zoom-src') or img.get_attribute('src') if img else None

            # '//'로 시작하는 경우 https: 붙이기
            if img_src and img_src.startswith('//'):
                img_src = 'https:' + img_src
            self.log_func(f"✅ 이미지 주소: {img_src}")
        except Exception as e:
            error = f'가격 추출 실패 : {e}'
            self.log_func("❌ 이미지 가져오기 실패")

        # 제품명
        try:
            h1 = self.driver.find_element(By.CSS_SELECTOR, 'h1.a-heading-1.q-mega.product-name')
            if h1:
                product_name = h1.text.strip() or ""
            else:
                self.log_func("제품명 태그가 존재하지 않습니다.")
        except Exception as e:
            error = f'제품명 추출 실패 : {e}'
            self.log_func("❌ 제품명 추출 실패")

        # 가격
        try:
            span = self.driver.find_element(By.CSS_SELECTOR, 'div.m-product-price')
            if span:
                price = span.text.strip() or ""
            else:
                self.log_func("가격 태그가 존재하지 않습니다.")
        except Exception as e:
            error = f'가격 추출 실패 : {e}'
            self.log_func("❌ 가격 추출 실패")

        # 설명
        try:
            # 1. div id="product-description" 찾기
            desc_div = self.driver.find_element(By.ID, "product-description")

            # 2. div 안의 모든 <p> 태그 찾기
            p_tags = desc_div.find_elements(By.TAG_NAME, "p")

            # 3. 첫 번째 <p> 태그의 텍스트 추출
            first_p = p_tags[0] if p_tags else None
            content = first_p.text.strip() if first_p else ""
        except Exception as e:
            error = f'설명 가져오기 실패 : {e}'
            self.log_func("❌ 설명 가져오기 실패:")

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
