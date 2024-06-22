import re
import pytz
import logging
from datetime import datetime
import time
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

import random



class Product:
    def __init__(self,
                 temporarilyOutOfStock,
                 no,
                 category,
                 manage_code,
                 product_code,
                 name,
                 wholesale_price,
                 inventory,
                 option,
                 features,
                 manufacturer,
                 material,
                 packaging,
                 size,
                 color,
                 delivery,
                 weight,
                 main_slide_images,
                 main_images,
                 detail_image,
                 country_of_origin):
        self.temporarilyOutOfStock = temporarilyOutOfStock
        self.no = no
        self.category = category
        self.manage_code = manage_code
        self.product_code = product_code
        self.name = name
        self.wholesale_price = wholesale_price
        self.inventory = inventory
        self.option = option
        self.features = features
        self.manufacturer = manufacturer
        self.material = material
        self.packaging = packaging
        self.size = size
        self.color = color
        self.delivery = delivery
        self.weight = weight
        self.main_slide_images = main_slide_images
        self.main_images = main_images
        self.detail_image = detail_image
        self.country_of_origin = country_of_origin

    def __str__(self):
        return (f"구매가능: {self.temporarilyOutOfStock}\n"
                f"번호: {self.no}\n"
                f"카테고리: {self.category}\n"
                f"관리코드: {self.manage_code}\n"
                f"상품코드: {self.product_code}\n"
                f"상품명: {self.name}\n"
                f"도매가: {self.wholesale_price}\n"
                f"재고현황: {self.inventory}\n"
                f"옵션: {len(self.option)}\n"
                f"대표 슬라이드 이미지 수: {len(self.main_slide_images)}\n"
                f"대표이미지 수: {len(self.main_images)}\n"
                f"상세이미지 수: {len(self.detail_image)}\n"
                f"제조국: {self.country_of_origin}")

def get_current_time():
    korea_tz = pytz.timezone('Asia/Seoul')
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    now_korea = now_utc.astimezone(korea_tz)
    formatted_time_korea = now_korea.strftime('%Y-%m-%d %H:%M:%S')
    print(formatted_time_korea)
    return formatted_time_korea

def get_info(driver, th_string):
    th_elements = driver.find_elements(By.XPATH, f"//th[contains(text(), '{th_string}')]")
    if th_elements:
        td_element = th_elements[0].find_element(By.XPATH, "./following-sibling::td")
        return td_element.text.strip()
    return ''

def fetch_product_details(driver, values, search_text):
    products = []
    for idx, value in enumerate(values):
        print(f"== 순서 : {idx + 1}====================")
        print(f"== value : {value}====================")
        url = f"https://dometopia.com/goods/view?no={value}&code="
        driver.get(url)
        time.sleep(random.uniform(1, 1.5))

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "goods_code")))
        except TimeoutException:
            print(f"Timeout waiting for goods_code for product {value}")
            return None

        try:
            goods_codes = driver.find_elements(By.CLASS_NAME, "goods_code")
            if len(goods_codes) < 2:
                print(f"Error: Not enough 'goods_code' elements found for product {value}")
                continue
        except NoSuchElementException:
            print(f"No elements found with class name goods_code for product {value}")
            return None

        temporarilyOutOfStock = ''
        try:
            temporarilyOutOfStock_element = driver.find_elements(By.CLASS_NAME, 'button.bgred')
            if temporarilyOutOfStock_element:
                temporarilyOutOfStock = temporarilyOutOfStock_element[0].text.strip()
        except NoSuchElementException:
            print(f"No elements found with class name button.bgred for product {value}")

        product_code = goods_codes[0].text.strip()

        doto_option_hide_div = ''
        try:
            doto_option_hide_div_element = driver.find_elements(By.CLASS_NAME, 'doto-option-hide')
            if doto_option_hide_div_element:
                doto_option_hide_div = doto_option_hide_div_element[0].get_attribute('outerHTML')
        except NoSuchElementException:
            print(f"No elements found with class name doto-option-hide for product {value}")

        features = get_info(driver, '상품용도 및 특징')
        manufacturer = get_info(driver, '제조자/수입자')
        material = get_info(driver, '상품재질')
        packaging = get_info(driver, '포장방법')
        size = get_info(driver, '사이즈')
        color = get_info(driver, '색상종류')
        delivery = get_info(driver, '배송기일')
        weight = get_info(driver, '무게(포장포함)')

        manage_code = goods_codes[1].text.strip()

        try:
            name = driver.find_element(By.CLASS_NAME, "pl_name").find_element(By.TAG_NAME, "h2").text.strip()
        except NoSuchElementException:
            print(f"No elements found with class name pl_name for product {value}")
            return None

        wholesale_price = "0"
        try:
            list2_elements = driver.find_elements(By.CLASS_NAME, "fl.tc.w20.list2.lt_line")
            if list2_elements:
                price_red_element = list2_elements[0].find_elements(By.CLASS_NAME, "price_red")
                if price_red_element:
                    price_text = price_red_element[0].text
                    wholesale_price = re.sub(r'\D', '', price_text)
            else:
                if len(goods_codes) > 2:
                    wholesale_price = re.sub(r'\D', '', goods_codes[2].text.strip())
        except NoSuchElementException:
            print(f"No elements found with class name fl.tc.w20.list2.lt_line for product {value}")

        if wholesale_price == "0":
            try:
                li_tags = driver.find_elements(By.CLASS_NAME, "fl.tc.w50.list2.lt_line")
                if li_tags and len(li_tags) == 2:
                    wholesale_price = re.sub(r'\D', '', li_tags[0].text.strip())
            except NoSuchElementException:
                print(f"No elements found with class name fl.tc.w50.list2.lt_line for product {value}")

        main_slide_images = []
        try:
            slides_container = driver.find_elements(By.CLASS_NAME, 'slides_container.hide')
            if slides_container:
                img_tags = slides_container[0].find_elements(By.TAG_NAME, 'img')
                for img_tag in img_tags[:100]:
                    src = img_tag.get_attribute('src')
                    if src:
                        main_slide_images.append(src)
        except NoSuchElementException:
            print(f"No elements found with class name slides_container.hide for product {value}")

        main_images = []
        try:
            pagination = driver.find_elements(By.CLASS_NAME, 'pagination.clearbox')
            if pagination:
                img_tags = pagination[0].find_elements(By.TAG_NAME, 'img')
                for img_tag in img_tags[:100]:
                    src = img_tag.get_attribute('src')
                    if src:
                        main_images.append(src)
        except NoSuchElementException:
            print(f"No elements found with class name pagination.clearbox for product {value}")

        detail_images = []
        try:
            detail_img_div = driver.find_elements(By.CLASS_NAME, 'detail-img')
            if detail_img_div:
                img_tags = detail_img_div[0].find_elements(By.TAG_NAME, 'img')
                for img_tag in img_tags:
                    src = img_tag.get_attribute('src')
                    if src:
                        if not src.startswith('http'):
                            src = 'https://dometopia.com' + src
                        detail_images.append(f'<img src="{src}">')
                detail_image = '<div style="text-align: center;">' + ''.join(detail_images) + '<br><br><br></div>'
            else:
                detail_image = ""
        except NoSuchElementException:
            print(f"No elements found with class name detail-img for product {value}")
            detail_image = ""

        country_text = ""
        try:
            # gilTable 요소가 로드될 때까지 대기
            gil_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'gilTable'))
            )

            th_tags = gil_table.find_elements(By.TAG_NAME, 'th')
            for th in th_tags:
                # JavaScript를 사용하여 'innerText'를 가져옴
                th_text = driver.execute_script("return arguments[0].innerText;", th)
                if '원산지' in th_text or '제조국' in th_text:
                    try:
                        # JavaScript를 사용하여 'td' 요소의 'innerText' 가져오기
                        td = th.find_element(By.XPATH, "./following-sibling::td")
                        td_text = driver.execute_script("return arguments[0].innerText;", td)
                        country_text = td_text.strip()
                        print(f"Country of origin/manufacture: {country_text}")
                        break
                    except NoSuchElementException:
                        print(f"Corresponding 'td' not found for th: {th_text}")
                        continue
        except NoSuchElementException:
            print(f"No elements found with class name gilTable for product {value}")

        inventory = ''
        try:
            th_elements = driver.find_elements(By.XPATH, "//th[contains(text(), '재고현황')]")
            if th_elements:
                td_element = th_elements[0].find_element(By.XPATH, "./following-sibling::td")
                td_text = td_element.text
                current_inventory = re.findall(r'\d+', td_text)
                if current_inventory:
                    inventory = current_inventory[0]
        except NoSuchElementException:
            print(f"No elements found with text 재고현황 for product {value}")

        product = Product(
            temporarilyOutOfStock=temporarilyOutOfStock,
            no=value,
            category=search_text,
            manage_code=manage_code,
            product_code=product_code,
            name=name,
            wholesale_price=wholesale_price,
            inventory=inventory,
            option=doto_option_hide_div,
            features=features,
            manufacturer=manufacturer,
            material=material,
            packaging=packaging,
            size=size,
            color=color,
            delivery=delivery,
            weight=weight,
            main_slide_images=main_slide_images,
            main_images=main_images,
            detail_image=detail_image,
            country_of_origin=country_text
        )

        print(product)
        products.append(product)
    return products

def fetch_goods_values(driver, page, search_text):
    print("fetch_goods_values")
    values = []
    try:
        for i in range(2, page + 1):
            url = f"https://dometopia.com/goods/search?page={i}&search_text={search_text}&popup=&iframe=&category1=&old_category1=&old_search_text={search_text}"
            driver.get(url)
            time.sleep(random.uniform(2, 3))

            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "goodsDisplayCode")))
            except TimeoutException:
                print(f"Timeout waiting for goodsDisplayCode on page {i}")
                return None

            try:
                dd_tags = driver.find_elements(By.CLASS_NAME, 'goodsDisplayCode')
            except NoSuchElementException:
                print(f"No elements found with class name goodsDisplayCode on page {i}")
                return None

            for dd in dd_tags:
                try:
                    label_tag = dd.find_elements(By.CLASS_NAME, 'hand')
                    if label_tag:
                        span_tag = label_tag[0].find_elements(By.CLASS_NAME, 'goods_scode')
                        if span_tag:
                            product_code = span_tag[0].text.strip()
                            if product_code[:2] != search_text or "GKM" in product_code[:3] or "GKD" in product_code[:3]:
                                print(f"not product_code : {product_code}")
                                continue

                        input_tag = label_tag[0].find_elements(By.XPATH, ".//input[@type='checkbox'][@class='list_goods_chk'][@name='goods_seq[]']")
                        if input_tag:
                            values.append(input_tag[0].get_attribute('value'))
                except NoSuchElementException:
                    print(f"Error processing element on page {i}")
                    continue

            print(f"page {i}, values len: {len(values)}")
    except WebDriverException as e:
        print(f"WebDriverException encountered: {e}")
        return None

    return values

def save_to_excel(products, filename='products.xlsx'):

    print(f"save_to_excel")

    workbook = Workbook()
    sheet = workbook.active
    headers = (['구매가능여부',
                'NO',
                '카테고리',
                '관리코드',
                '상품코드 (모델명)',
                '상품명',
                '도매가',
                '재고',
                '옵션',
                '상품용도 및 특징',
                '제조자/수입자',
                '상품재질',
                '포장방법',
                '사이즈',
                '색상종류',
                '배송기일',
                '무게(포장포함)',
                '제조국',
                '상세이미지']
               + [f'대표 슬라이드 이미지{i+1}' for i in range(100)]
               + [f'대표이미지{i+1}' for i in range(100)])
    sheet.append(headers)

    for product in products:
        row = [
            product.temporarilyOutOfStock,
            product.no,
            product.category,
            product.manage_code,
            product.product_code,
            product.name,
            product.wholesale_price,
            product.inventory,
            product.option,
            product.features,
            product.manufacturer,
            product.material,
            product.packaging,
            product.size,
            product.color,
            product.delivery,
            product.weight,
            product.country_of_origin,
            product.detail_image
        ]

        row.extend(product.main_slide_images[:100])
        row.extend([''] * (100 - len(product.main_slide_images)))

        row.extend(product.main_images[:100])
        row.extend([''] * (100 - len(product.main_images)))
        sheet.append(row)

    workbook.save(filename)

def initialize_driver():
    print(f"initialize_driver")
    try:
        # 크롬 옵션 설정
        chrome_options = Options()

        # 이 옵션을 사용하면 브라우저가 백그라운드에서 실행됩니다. 즉, 브라우저 창이 표시되지 않고 모든 작업이 백그라운드에서 이루어집니다. 주로 서버 환경에서 자동화 작업을 수행할 때 유용합니다.
        chrome_options.add_argument("--headless")  # 브라우저를 표시하지 않고 실행

        # GPU 가속을 비활성화합니다. 일반적으로 헤드리스 모드에서 사용됩니다. 이 옵션은 그래픽 하드웨어 가속을 비활성화하여 성능을 향상시킬 수 있습니다.
        chrome_options.add_argument("--disable-gpu")  # GPU 사용 안함

        # 브라우저 창의 크기를 설정합니다. 여기서는 960x540 크기로 설정하여 화면의 절반 크기로 브라우저를 실행합니다. 헤드리스 모드에서 특정 요소의 위치나 크기를 맞추기 위해 사용할 수 있습니다.
        chrome_options.add_argument("--window-size=960,540")  # 창 크기 설정 (화면의 절반 크기)

        # 샌드박스 모드를 비활성화합니다. 이 옵션은 보안과 관련된 기능을 비활성화하여 브라우저가 더 쉽게 실행되도록 합니다. 일부 환경에서는 이 옵션을 사용해야 브라우저가 제대로 실행됩니다.
        chrome_options.add_argument("--no-sandbox")  # 샌드박스 모드 비활성화

        # 공유 메모리 사용을 비활성화합니다. 이는 Docker와 같은 컨테이너 환경에서 사용됩니다. 기본적으로 크롬은 /dev/shm 디렉토리를 사용하여 공유 메모리를 저장하지만, 컨테이너 환경에서는 이 디렉토리가 작을 수 있습니다. 이 옵션을 사용하면 디스크를 대신 사용합니다.
        chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 사용 비활성화

        # 모든 브라우저 확장 프로그램을 비활성화합니다. 자동화 테스트에서는 확장 프로그램이 필요하지 않으므로 이를 비활성화하여 브라우저를 더 가볍고 빠르게 실행할 수 있습니다.
        chrome_options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화

        # 팝업 차단 기능을 비활성화합니다. 자동화 테스트 중에 팝업이 필요한 경우 이를 사용하여 팝업이 차단되지 않도록 합니다.
        chrome_options.add_argument("--disable-popup-blocking")  # 팝업 차단 비활성화

        # 브라우저의 로그 출력을 비활성화합니다. 자동화 테스트 중에 불필요한 로그를 줄이기 위해 사용됩니다.
        chrome_options.add_argument("--disable-logging")  # 로그 비활성화

        # 시크릿 모드로 브라우저를 실행합니다. 시크릿 모드는 쿠키나 캐시 등을 저장하지 않아 매번 깨끗한 상태에서 테스트를 시작할 수 있습니다.
        chrome_options.add_argument("--incognito")  # 시크릿 모드

        # 브라우저의 User-Agent 문자열을 변경합니다. 이를 통해 브라우저가 자동화된 스크립트가 아닌 일반 사용자의 브라우저처럼 보이도록 할 수 있습니다.
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # 브라우저의 자동화 메시지를 제거합니다. 이를 통해 "Chrome is being controlled by automated test software"와 같은 메시지를 숨길 수 있습니다.
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 자동화 메시지 제거

        # 크롬의 자동화 확장 프로그램을 비활성화합니다. 이를 통해 브라우저가 자동화된 환경에서 실행되고 있음을 감추는 데 도움이 됩니다.
        chrome_options.add_experimental_option('useAutomationExtension', False)  # 자동화 확장 프로그램 비활성화

        # Selenium에서 브라우저가 자동화된 스크립트에 의해 제어되는지 감지하지 않도록 설정
        # 브라우저의 추가적인 기능을 설정할 수 있습니다. 여기서는 goog:loggingPrefs를 통해 퍼포먼스 로그를 모두 캡처하도록 설정합니다.
        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, desired_capabilities=caps)

        # 자바스크립트 실행을 통해 navigator.webdriver 속성 제거
        # 자바스크립트를 사용하여 navigator.webdriver 속성을 undefined로 설정합니다.
        # 이는 브라우저가 자동화된 스크립트에 의해 제어되고 있음을 숨기는 데 도움이 됩니다.
        # 웹사이트는 일반적으로 navigator.webdriver 속성을 확인하여 브라우저가 자동화된 환경에서 실행되고 있는지 감지합니다.
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        return driver
    except Exception as e:
        print(f"Error initializing the driver: {e}")
    return None

def login(driver, id, pw):
    print(f"login")
    driver.get("https://dometopia.com/member/login")

    # 아이디 입력
    userid_field = driver.find_element(By.ID, "userid")
    userid_field.send_keys(id)

    # 비밀번호 입력
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(pw)

    # 로그인 버튼 클릭
    login_button = driver.find_element(By.CLASS_NAME, "login-btn")
    login_button.click()

    # 로그인 완료 대기 (로그인 후 표시되는 특정 요소로 대기)
    time.sleep(10)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "dometopia_header")))



# 로거 설정
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)

# 핸들러 설정 (콘솔 출력)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 포맷터 설정
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 핸들러를 로거에 추가
logger.addHandler(console_handler)

# 현재 시간 로그 출력
logger.info('This is an info log message.')

def main():


    # 시작 시간 세팅
    main_start_time = time.time()
    get_current_time()


    id = "dreamtime"
    pw = "112233aa^^"


    # 크롬 드라이버 초기화
    driver = initialize_driver()
    login(driver, id, pw)

    # 파라미터 세팅
    search_texts = ["GK", "GT"]
    # pages = [52, 213]
    search_texts = ["GK"]
    pages = [52]
    products = []


    for search_text, page in zip(search_texts, pages):
        print(f"=======================================")
        print(f"search_text: {search_text}")
        print(f"page: {page}")

        start_time = time.time()
        get_current_time()

        values = fetch_goods_values(driver, page, search_text)

        print(f"목록 수: {len(values)}")
        end_time = time.time()
        total_time = end_time - start_time
        print(f"목록 전체조회 걸린시간: {total_time} 초")
        get_current_time()
        print(f"======================================")

        product = fetch_product_details(driver, values, search_text)

        if product:
            products.extend(product)
        else:
            break


    save_to_excel(products)
    driver.quit()

    # 종료시간 세팅
    main_end_time = time.time()
    get_current_time()
    main_total_time = main_end_time - main_start_time
    print(f"전체 걸린시간: {main_total_time} 초")

if __name__ == "__main__":
    main()
