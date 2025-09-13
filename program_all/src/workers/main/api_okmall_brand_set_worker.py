import time
from urllib.parse import urlparse, unquote_to_bytes

import re
import time
from urllib.parse import quote, unquote
from urllib.parse import urlparse, unquote_to_bytes

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.number_utils import divide_and_truncate_per
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


# API
class ApiOkmallBrandSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://www.okmall.com"
        self.base_main_url_login = "https://www.okmall.com/members/login"
        self.url_list = []
        self.user = None
        self.driver = None
        self.version = ""
        self.running = True  # 실행 상태 플래그 추가
        self.company_name = "okmall"
        self.site_name = "okmall"
        self.excel_filename = ""
        self.brand_obj_list = []
        self.product_obj_list = []
        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.current_page = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

    # 초기화
    def init(self):
        self.driver_set(False)
        self.login()
        return True

    # 메인
    def main(self):
        try:
            self.set_cookies()

            self.log_signal.emit("크롤링 시작")

            self.url_list = [
                str(row[k]).strip()
                for row in self.excel_data_list
                for k in row.keys()
                if k.lower() == "url" and row.get(k) and str(row[k]).strip()
            ]
            # [{'url': '...', 'file': '...'}, {'url': '...', 'file': '...'}, ...]

            self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.excel_filename, self.columns)

            # 브랜드 리스트 세팅 전체 갯수 조회
            self.brand_init()

            # 제품 목록 가져오기
            self.brand_obj_list_call_product_list()

            # CSV -> 엑셀 변환
            self.excel_driver.convert_csv_to_excel_and_delete(self.excel_filename)

            return True
        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False


    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)

        # 드라이버 세팅
        self.driver = self.selenium_driver.start_driver(1200)

    # 쿠키세팅
    def set_cookies(self):
        self.log_signal_func("📢 쿠키 세팅 시작")
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)
        self.log_signal_func("📢 쿠키 세팅 완료")
        time.sleep(2)


    # 브랜드에서 제품 목록 호출
    def brand_obj_list_call_product_list(self):
        if self.brand_obj_list:
            for index, brand_obj in enumerate(self.brand_obj_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break
                self.product_list_get(index, brand_obj)

    # 제품 목록 가져오기
    def product_list_get(self, index, brand_obj):
        if brand_obj:
            total_page = brand_obj['total_page']
            brand = brand_obj['brand']
            for idx, page in enumerate(range(1, total_page + 1), start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_page += 1
                brd_ob = self.brand_api_data(brand, page, False)
                product_list = brd_ob['product_list']
                self.product_detail(index, idx, product_list, brand_obj)
                time.sleep(0.5)

    # 제품 상세정보
    def product_detail(self, index, idx, product_list, brand_obj):
        if product_list:
            for ix, product in enumerate(product_list, start=1):
                if not self.running:  # 실행 상태 확인
                    break
                self.current_cnt += 1
                prdt_obj_list = self.product_api_data(product)
                now_per = divide_and_truncate_per(self.current_cnt, self.total_cnt)

                self.log_signal.emit("====================================================================================================")
                self.log_signal.emit(f"전체 브랜드({index}/{len(self.brand_obj_list)})[{now_per}%],  전체 페이지({self.current_page}/{self.total_pages}),  전체 상품({self.current_cnt}/{self.total_cnt})")
                self.log_signal.emit("----------------------------------------------------------------------------------------------------")
                self.log_signal.emit(f"현재 브랜드({brand_obj['brand']}),  현재 페이지({idx}/{brand_obj['total_page']}),  현재 상품({ix}/{brand_obj['total_cnt']})")
                self.log_signal.emit(f"현재 상품 상세 : {prdt_obj_list}")
                self.log_signal.emit("====================================================================================================")

                self.excel_driver.append_to_csv(self.excel_filename, prdt_obj_list, self.columns)

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                time.sleep(1)


    def get_query_params(self, url, name):
        parsed_url = urlparse(url)
        query = parsed_url.query

        match = re.search(rf"{name}=([^&]+)", query)
        if not match:
            return None

        encoded = match.group(1).replace('+', ' ')  # ➕ 먼저 + 를 공백으로 변환

        try:
            # 1차 시도: EUC-KR
            return unquote_to_bytes(encoded).decode('euc-kr')
        except UnicodeDecodeError:
            try:
                # 2차 fallback: UTF-8
                return unquote(encoded)
            except Exception as e:
                self.log_signal.emit(f"[❌ 디코딩 실패] {e}")
                return encoded


    # 브랜드 api_data
    def product_api_data(self, url):
        product_detail_list = []
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "host": "www.okmall.com",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
        try:
            response = self.api_client.get(url, headers=headers)
            soup = BeautifulSoup(response, 'html.parser')

            # 브랜드명
            brand_tag = soup.select_one("span.brand_tit")
            brand = brand_tag.get_text(strip=True) if brand_tag else ""

            # 상품명
            season = soup.select_one("h3#ProductNameArea .prd_name_season")
            name = soup.select_one("h3#ProductNameArea .prd_name")
            more = soup.select_one("h3#ProductNameArea .prd_name_more")
            product_name = " ".join(filter(None, [
                season.get_text(strip=True) if season else "",
                name.get_text(strip=True) if name else "",
                more.get_text(strip=True) if more else ""
            ]))

            # 가격 (div.last_price 내부 span.price만 타겟)
            base_price = ""
            price_tag = soup.select_one("div.last_price span.price")
            if price_tag:
                price_text = price_tag.get_text(strip=True).replace(",", "").replace("원", "")
                # 숫자만 필터링
                price_digits = ''.join(filter(str.isdigit, price_text))
                if price_digits:
                    base_price = int(price_digits)

            # 사이즈/옵션 행
            size_rows = soup.select('table.shoes_size tr[name="selectOption"]')
            for row in size_rows:
                tds = row.select("td.t_center")
                if len(tds) < 2:
                    continue

                size = tds[1].get_text(strip=True)

                # 1) sprice 속성 우선
                row_price = base_price
                sprice_attr = row.get("sprice")
                if sprice_attr:
                    sdigits = ''.join(ch for ch in sprice_attr if ch.isdigit())
                    if sdigits:
                        row_price = int(sdigits)
                else:
                    # 2) set_etc_opt2(행 내 표시가) 있으면 사용
                    etc_td = row.select_one("td.set_etc")
                    if etc_td:
                        opt2 = etc_td.select_one(".set_etc_opt2")
                        if opt2:
                            odigits = ''.join(ch for ch in opt2.get_text(strip=True) if ch.isdigit())
                            if odigits:
                                row_price = int(odigits)

                obj = {
                    "브랜드명": brand,
                    "상품명": product_name,
                    "가격": row_price,
                    "택 사이즈": size,
                    "상품 링크": url
                }
                product_detail_list.append(obj)

        except requests.exceptions.RequestException as e:
            print(f"HTTP 요청 에러: {e}")
        except Exception as e:
            print(f"알 수 없는 에러 발생: {e}")
        return product_detail_list

    # 브랜드 리스트 초기화
    def brand_init(self):
        if self.url_list:
            self.log_signal.emit(f"전체 상품수 계산을 시작합니다. 잠시만 기다려주세요.")
            self.brand_obj_list = self.brand_obj_list_get()
            self.total_cnt = sum(int(obj['total_cnt']) for obj in self.brand_obj_list)
            self.total_pages = sum(int(obj['total_page']) for obj in self.brand_obj_list)
            self.log_signal.emit(f"전체 브랜드수 {len(self.brand_obj_list)}개")
            self.log_signal.emit(f"전체 상품수 {self.total_cnt} 개")
            self.log_signal.emit(f"전체 페이지수 {self.total_pages} 개")


    # 브랜드 리스트 가져오기
    def brand_obj_list_get(self):
        brand_obj_list = []
        for index, url in enumerate(self.url_list, start=1):
            brand = self.get_query_params(url, 'brand')
            brand_obj = self.brand_api_data(brand, 1, True)
            time.sleep(0.5)
            brand_obj_list.append(brand_obj)
            self.log_signal.emit(f"brand: {brand_obj}")
            time.sleep(0.5)
        return brand_obj_list

    # 브랜드 api data
    def brand_api_data(self, brand, page, count_flag):
        obj = {
            'brand': brand, 'page': page,
            'total_cnt': 0, 'total_page': 0,
            'product_list': []
        }

        url = "https://www.okmall.com/products/list"
        payload = {
            "key_type": "on",
            "brand": brand,
            "search_keyword": "",
            "detail_search_keyword": "",
            "page": page
        }
        encoded_brand = quote(brand)
        headers = {
            "accept": "text/html, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "host": "www.okmall.com",
            "referer": f"https://www.okmall.com/products/list?brand={encoded_brand}",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-csrf-token": "",
            "x-requested-with": "XMLHttpRequest"
        }

        # XSRF-TOKEN 추출 (이름만 필터, 값은 unquote)
        xsrf_list = self.api_client.cookie_get(name="XSRF-TOKEN")
        if xsrf_list:
            headers["x-csrf-token"] = unquote(xsrf_list[0].value or "")

        try:
            html = self.api_client.get(url, headers=headers, params=payload)  # APIClient가 text 반환
            if not html:
                self.log_signal_func("⚠️ 응답이 비어 있음")
                return obj
            if not isinstance(html, str):
                # 혹시 JSON/dict로 온 경우 방어
                try:
                    html = str(html)
                except Exception:
                    self.log_signal_func(f"⚠️ 예상치 못한 응답 타입: {type(html)}")
                    return obj

            soup = BeautifulSoup(html, 'html.parser')

            if count_flag:
                input_tag = soup.find('input', {'name': 'total_count'})
                if input_tag and input_tag.get('value'):
                    total_cnt = int(input_tag['value'])
                    q, r = divmod(total_cnt, 80)
                    obj['total_cnt'] = total_cnt
                    obj['total_page'] = q + (1 if r else 0)
                    obj['page'] = page

            product_list = []
            for item in soup.find_all(class_="item_box"):
                p_tag = item.find("p", attrs={"name": "shortProductName"})
                if not p_tag:
                    continue
                a_tags = p_tag.find_all("a")
                if len(a_tags) >= 2:
                    href = a_tags[1].get("href", "")
                    base = getattr(self, "base_main_url", "https://www.okmall.com")  # 방어
                    full = href if href.startswith("http") else base + href
                    product_list.append(full)

            obj['product_list'] = product_list

        except SystemExit as e:
            # 디버깅 중 pydevd가 SystemExit를 전파할 때 안전히 흡수
            self.log_signal_func(f"⚠️ SystemExit 캡처: {e}")
        except requests.exceptions.RequestException as e:
            self.log_signal_func(f"HTTP 요청 에러: {e}")
        except Exception as e:
            self.log_signal_func(f"알 수 없는 에러 발생: {e}")

        return obj

    # 로그인 쿠키가져오기
    def login(self):
        self.driver.get(self.base_main_url_login)

        # 3초 대기
        time.sleep(2)

        try:
            # ID 입력
            id_input = self.driver.find_element(By.NAME, "txt_id")
            id_input.clear()
            id_input.send_keys(self.user.get("id", ""))

            # PW 입력
            pw_input = self.driver.find_element(By.NAME, "txt_pw")
            pw_input.clear()
            pw_input.send_keys(self.user.get("pw", ""))

            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login-default")
            login_button.click()

            time.sleep(3)

        except Exception as e:
            log_signal_func(f"[❌ 로그인 자동 입력 오류] {e}")


    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()




