import time
from selenium.common.exceptions import NoSuchElementException
from src.workers.main.api_base_worker import BaseApiWorker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class ApiHmSetLoadWorker(BaseApiWorker):
    def __init__(self, checked_list):
        super().__init__("H&M", checked_list)
    
    # 초기화
    def init_set(self):
        self.log_func("초기화 시작")
    
    # 목록
    def selenium_get_product_list(self, main_url: str):
        self.driver.get(main_url)
        page = 1
        while True:
            url = f'{main_url}?page={page}'
            self.driver.get(url)
            time.sleep(2)
            self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)
            time.sleep(2)
            li_elements = []
            try:
                ul_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-elid="product-grid"]'))
                )
                if ul_element:
                    # 바로 첫번째 자식 li들만
                    li_elements = ul_element.find_elements(By.CSS_SELECTOR, ":scope > li")
            except Exception as e:
                self.handle_selenium_exception("li_elements", e)

            if not li_elements:
                break

            for index, li in enumerate(li_elements, start=1):
                if not self.running:
                    self.log_func("크롤링이 중지되었습니다.")
                    break
                try:
                    article = li.find_element(By.TAG_NAME, "article")
                    if article is None:
                        continue

                    product_id = article.get_attribute("data-articlecode")
                    if not product_id:
                        continue

                    a_tag = article.find_element(By.TAG_NAME, "a")
                    if a_tag is None:
                        continue

                    href = a_tag.get_attribute("href")
                    if not href:
                        continue
                    else:
                        self.product_list.append({
                            "productId": product_id,
                            "url": href
                        })
                        self.log_func(f"product_id : {product_id} / index : {index}")
                except Exception as e:
                    self.handle_selenium_exception("product_id", e)
            page += 1
        self.log_func('상품목록 수집완료...')

    # 상세내용 추출
    def extract_product_detail(self, product_id: str, url: str, name: str, no: int) -> dict:
        self.driver.get(url)
        time.sleep(2)

        img_src = ""
        product_name = ""
        price = ""
        content = ""

        # 이미지 src
        try:
            ul = self.driver.find_element(By.CSS_SELECTOR, 'ul[data-testid="grid-gallery"]')
            li_list = ul.find_elements(By.TAG_NAME, 'li') if ul else []
            if li_list:
                first_li = li_list[0]
                img = first_li.find_element(By.TAG_NAME, 'img') if first_li else None
                img_src = img.get_attribute('src') if img else ""
            else:
                self.log_func("li 태그가 존재하지 않습니다.")
        except Exception as e:
            self.handle_selenium_exception("이미지 src", e)

        # 제품명
        try:
            h1 = self.driver.find_element(By.CSS_SELECTOR, 'h1.fa226d.af6753.d582fb')
            if h1:
                product_name = h1.text.strip() or ""
            else:
                self.log_func("제품명 태그가 존재하지 않습니다.")
        except Exception as e:
            self.handle_selenium_exception("제품명", e)

        # 가격
        try:
            span = self.driver.find_element(By.CSS_SELECTOR, 'span.edbe20.ac3d9e.d9ca8b')
            if span:
                price = span.text.strip() or ""
            else:
                self.log_func("가격 태그가 존재하지 않습니다.")
        except Exception as e:
            self.handle_selenium_exception("가격", e)

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