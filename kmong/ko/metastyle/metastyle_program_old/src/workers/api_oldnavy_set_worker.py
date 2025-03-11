import os
import ssl
import time

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime
import re

ssl._create_default_https_context = ssl._create_unverified_context

company_name = 'oldnavy'
site_name = 'OLDVNAVY'
excel_filename = ''
baseUrl = "https://oldnavy.gap.com"


# API
class ApiOldnavySetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널


    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.baseUrl = baseUrl
        self.sess = requests.Session()
        self.checked_list = checked_list

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.checked_model_list = []
        self.main_model = None
        self.product_info_list = []

        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0


    # 프로그램 실행
    def run(self):
        global company_name, site_name, excel_filename, baseUrl

        self.log_signal.emit("✅ 최신 데이터가 없습니다.")
        self.log_signal.emit("크롤링 시작")

        if self.checked_list:
            self.log_signal.emit("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
            self.login()
            self.log_signal.emit("크롤링 사이트 인증에 성공하였습니다.")

            self.log_signal.emit(f"전체 상품수 계산을 시작합니다. 잠시만 기다려주세요.")
            check_obj_list = self.total_cnt_cal()
            self.total_cnt = sum(int(obj['total_product_cnt']) for obj in check_obj_list)
            self.total_pages = sum(int(obj['total_page_cnt']) for obj in check_obj_list)

            self.log_signal.emit(f"전체 항목수 {len(check_obj_list)}개")
            self.log_signal.emit(f"전체 상품수 {self.total_cnt} 개")
            self.log_signal.emit(f"전체 페이지수 {self.total_pages} 개")

            for index, checked_model in enumerate(self.checked_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                all_detail_list = {}

                self.current_cnt = (int(checked_model['start_page']) - 1) * 300
                self.current_page = int(checked_model['start_page'])

                for indx, page in enumerate(range(int(checked_model['start_page']) - 1, int(checked_model['end_page'])), start=1):
                    self.current_page = self.current_page + 1
                    time.sleep(0.5)
                    self.log_signal.emit(f'{checked_model["name"]}({index}/{len(self.checked_list)})  TotalPage({self.current_page}/{self.total_pages})')
                    if not self.running:
                        break
                    detail_list = self.get_api_request(checked_model['url'], page)
                    self.log_signal.emit(f'detail_list : {len(detail_list)}')
                    if not detail_list:
                        break
                    for pid_dic in detail_list:
                        pid = pid_dic.get("ccId")
                        if pid not in all_detail_list:
                            all_detail_list[pid] = {
                                "page": page + 1,
                                "pid": pid,
                            }
                all_detail_list = list(all_detail_list.values())  # 리스트 변환
                self.log_signal.emit(f'detail_list : {len(all_detail_list)}')
                self.product_info_list = all_detail_list

                self.get_product_info_list(checked_model)

        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.driver.quit()
        self.log_signal.emit("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()


    def get_product_info_list_multi(self, checked_model):
        result_list = []

        # CSV 파일 경로 설정
        csv_filename = os.path.join(os.getcwd(), f"{checked_model['name']}_{get_current_yyyymmddhhmmss()}.csv")

        # CSV 파일 초기 생성
        columns = ["name", "product", "product_id" , "product_no", "description", "image_no", "image_url", "image_name", "success", "reg_date", "page", "error"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')

        for index, product in enumerate(self.product_info_list):

            if not product:  # product가 None인지 확인
                print(f"경고: index {index}의 product가 None입니다. 건너뜁니다.")
                continue

            time.sleep(1)
            obj = self.get_api_product_info_multi(product.get('pid'), product.get('cid'))

            if obj:

                product['product'] = obj.get('product')
                product['description'] = obj.get('description')
                product['img_list'] = obj.get('img_list')
                product['product_id'] = product.get('pid')
                product['product_no'] = index + 1

                # images 폴더 생성
                images_dir = os.path.join(os.getcwd(), 'images')
                os.makedirs(images_dir, exist_ok=True)

                for ix, image_url in enumerate(product.get('img_list'), start=1):
                    if not self.running:
                        break

                    obj_copy = product.copy()  # 객체 복사
                    obj_copy['name'] = checked_model['name']
                    obj_copy['image_no'] = ix + 1
                    obj_copy['image_url'] = image_url
                    obj_copy['success'] = 'N'
                    obj_copy['image_yn'] = 'N'
                    obj_copy['reg_date'] = get_current_formatted_datetime()  # 시간 추가

                    try:
                        # 이미지 다운로드
                        # response = requests.get(image_url, stream=True)
                        # response.raise_for_status()

                        # 이미지 저장 경로
                        img_filename = f"{product.get('pid')}_{ix}.jpg"
                        # img_path = os.path.join(images_dir, img_filename)

                        # 이미지 저장
                        # with open(img_path, 'wb') as file:
                            # for chunk in response.iter_content(1024):
                                # file.write(chunk)

                        # obj_copy['success'] = 'Y'  # 성공하면 Y
                        obj_copy['image_name'] = img_filename
                        self.log_signal.emit(f"성공 {obj_copy}")
                    except Exception as e:
                        print(f"이미지 다운로드 실패: {image_url}, 오류: {e}")
                        obj_copy['success'] = 'N'  # 실패하면 N 유지
                        obj_copy['error'] = e

                    result_list.append(obj_copy)

                self.current_cnt = self.current_cnt + 1
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal.emit(f'{checked_model["name"]} TotalPage({self.current_page}/{self.total_pages})  TotalProduct({self.current_cnt}/{self.total_cnt}) Product({index+1}/{len(self.product_info_list)})')

                # 5개마다 CSV에 저장
                if index % 5 == 0 and index > 0:
                    df = pd.DataFrame(result_list, columns=columns)
                    df.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8-sig')
                    result_list.clear()  # 저장 후 리스트 초기화

        # 남은 데이터 저장
        if result_list:
            df = pd.DataFrame(result_list, columns=columns)
            df.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8-sig')


    def get_api_product_info_multi(self, pid, cid):
        url = "https://oldnavy.gap.com/browse/product.do"
        params = {"pid": pid, "cid": cid, "pcid": cid, "ctype": "Listing"}
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }

        try:
            res = self.sess.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            obj = {
                "product": soup.find("h1", class_="sitewide-1t5lfed").get_text(strip=True) if soup.find("h1", class_="sitewide-1t5lfed") else "",
                "description": "\n".join(li.get_text(strip=True) for li in soup.select(".drawer-trigger-container .sitewide-jxz45b:nth-of-type(2) .product-information-item__list li")) or "",
                "img_list": [
                    (img["src"] if img["src"].startswith("http") else f"https://oldnavy.gap.com/{img['src'].lstrip('/')}")
                    for div in soup.find_all("div", class_="brick__product-image-wrapper")
                    for img in div.find_all("img")
                    if img.get("src")
                ]
            }
            return obj

        except requests.exceptions.RequestException as e:
            self.log_signal.emit(f"Request failed: {e}")
            return None
        except Exception as e:
            self.log_signal.emit(f"Parsing error: {e}")
            return None


    def sanitize_filename(self, text):
        """파일명에서 특수 문자 제거 및 '_'로 변환"""
        if text:
            return re.sub(r'[\\/:*?"<>|]', '_', text)  # 파일명에서 사용할 수 없는 문자 변환
        return text  # 값이 없을 경우 기본값 설정


    def get_product_info_list(self, checked_model):
        global site_name
        result_list = []

        main_name = checked_model['name']
        if main_name and " / " in main_name:
            main_name = main_name.replace(" / ", "_")

        # CSV 파일 경로 설정
        csv_filename = os.path.join(os.getcwd(), f"{main_name}_{get_current_yyyymmddhhmmss()}.csv")

        # CSV 파일 초기 생성
        columns = ["name", "product", "product_id" , "product_no", "Materials & Care", "image_url", "image_name", "success", "reg_date", "page", "error"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')

        for index, product in enumerate(self.product_info_list):

            if not product:  # product가 None인지 확인
                print(f"경고: index {index}의 product가 None입니다. 건너뜁니다.")
                continue

            time.sleep(1)
            obj = self.get_api_product_info(product.get('pid'), product.get('cid'))

            if obj:

                product['product'] = obj.get('product')
                product['Materials & Care'] = obj.get('Materials & Care')
                product['image_url'] = obj.get('image_url')
                product['product_id'] = product.get('pid')
                product['product_no'] = index + 1

                # images 폴더 생성
                images_dir = os.path.join(os.getcwd(), 'images', site_name, main_name)
                os.makedirs(images_dir, exist_ok=True)

                product['name'] = checked_model['name']
                product['success'] = 'Y'
                product['reg_date'] = get_current_formatted_datetime()  # 시간 추가

                try:
                    # 이미지 다운로드
                    response = requests.get(obj.get('image_url'), stream=True)
                    response.raise_for_status()

                    # 이미지 저장 경로 처리
                    product_name = self.sanitize_filename(obj.get('product'))  # 특수 문자 제거된 파일명
                    img_filename = f"{product_name}_{product.get('pid')}.jpg"
                    img_path = os.path.join(images_dir, img_filename)

                    # 이미지 저장
                    with open(img_path, 'wb') as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)

                    # obj_copy['success'] = 'Y'  # 성공하면 Y
                    product['image_name'] = img_filename
                    self.log_signal.emit(f"성공 {img_filename}")
                except Exception as e:
                    self.log_signal.emit(f"이미지 다운로드 실패: {obj.get('image_url')}, 오류: {e}")
                    product['success'] = 'N'  # 실패하면 N 유지
                    product['error'] = e

                result_list.append(product)

                self.current_cnt = self.current_cnt + 1
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal.emit(f'{checked_model["name"]} TotalPage({self.current_page}/{self.total_pages})  TotalProduct({self.current_cnt}/{self.total_cnt})')

                # 5개마다 CSV에 저장
                if index % 5 == 0 and index > 0:
                    df = pd.DataFrame(result_list, columns=columns)
                    df.to_csv(csv_filename, mode='a', header=False, index=False , encoding='utf-8-sig')
                    result_list.clear()  # 저장 후 리스트 초기화

        # 남은 데이터 저장
        if result_list:
            df = pd.DataFrame(result_list, columns=columns)
            df.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8-sig')


    def get_api_product_info(self, pid, cid):
        url = "https://oldnavy.gap.com/browse/product.do"
        params = {"pid": pid, "cid": cid, "pcid": cid, "ctype": "Listing"}
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }

        try:
            res = self.sess.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            # "Materials & Care" 버튼 찾기
            button = soup.find("button", string="Materials & Care")  # HTML 엔티티 변환 적용

            # 버튼이 존재하면, 그 다음 div 내부의 ul > li들을 찾음
            li_texts = []
            if button:
                div_after_button = button.find_next_sibling("div")
                if div_after_button:
                    ul = div_after_button.find("ul")
                    if ul:
                        li_texts = [li.get_text(strip=True) for li in ul.find_all("li")]

            # 첫 번째 div 찾기
            first_div = soup.find("div", class_="brick__product-image-wrapper")

            # 첫 번째 div 안에서 a 태그 찾기
            href = None
            if first_div:
                a_tag = first_div.find("a")
                if a_tag and a_tag.has_attr("href"):
                    href = a_tag["href"]
                    # https://oldnavy.gap.com 가 포함되어 있지 않으면 앞에 추가
                    if not href.startswith(self.baseUrl):
                        href = self.baseUrl + href

            obj = {
                "product": soup.find("h1", class_="sitewide-1t5lfed").get_text(strip=True) if soup.find("h1", class_="sitewide-1t5lfed") else "",
                "Materials & Care": li_texts,
                "image_url": href,
            }
            return obj

        except requests.exceptions.RequestException as e:
            self.log_signal.emit(f"Request failed: {e}")
            return None
        except Exception as e:
            self.log_signal.emit(f"Parsing error: {e}")
            return None


    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False


    # 로그인 쿠키가져오기
    def login(self):
        webdriver_options = webdriver.ChromeOptions()

        # 이 옵션은 Chrome이 자동화 도구(예: Selenium)에 의해 제어되고 있다는 것을 감지하지 않도록 만듭니다.
        # AutomationControlled 기능을 비활성화하여 webdriver가 브라우저를 자동으로 제어하는 것을 숨깁니다.
        # 이는 일부 웹사이트에서 자동화 도구가 감지되는 것을 방지하는 데 유용합니다.
        ###### 자동 제어 감지 방지 #####
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')

        # Chrome 브라우저를 실행할 때 자동으로 브라우저를 최대화 상태로 시작합니다.
        # 이 옵션은 사용자가 브라우저를 처음 실행할 때 크기가 자동으로 최대로 설정되도록 합니다.
        ##### 화면 최대 #####
        webdriver_options.add_argument("--start-maximized")

        # headless 모드로 Chrome을 실행합니다.
        # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
        # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
        ##### 화면이 안보이게 함 #####
        # webdriver_options.add_argument("--headless")

        #이 설정은 Chrome의 자동화 기능을 비활성화하는 데 사용됩니다.
        #기본적으로 Chrome은 자동화가 활성화된 경우 브라우저의 콘솔에 경고 메시지를 표시합니다.
        #이 옵션을 설정하면 이러한 경고 메시지가 나타나지 않도록 할 수 있습니다.
        ##### 자동 경고 제거 #####
        webdriver_options.add_experimental_option('useAutomationExtension', False)

        # 이 옵션은 브라우저의 로깅을 비활성화합니다.
        # enable-logging을 제외시키면, Chrome의 로깅 기능이 활성화되지 않아 불필요한 로그 메시지가 출력되지 않도록 할 수 있습니다.
        ##### 로깅 비활성화 #####
        webdriver_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 이 옵션은 enable-automation 스위치를 제외시킵니다.
        # enable-automation 스위치가 활성화되면,
        # 자동화 도구를 사용 중임을 알리는 메시지가 브라우저에 표시됩니다.
        # 이를 제외하면 자동화 도구의 사용이 감지되지 않습니다.
        ##### 자동화 도구 사용 감지 제거 #####
        webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=webdriver_options)
        self.driver.set_page_load_timeout(120)
        self.driver.get(self.baseUrl)
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])
        # self.driver.quit()


    def main_request(self, cid, pageNumber):

        url = "https://api.gap.com/commerce/search/products/v2/cc"

        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": "https://oldnavy.gap.com",
            "referer": "https://oldnavy.gap.com/",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "x-client-application-name": "Browse"
        }

        params = {
            "brand": "on",
            "market": "us",
            "cid": cid,
            "locale": "en_US",
            "pageSize": "300",
            "ignoreInventory": "false",
            "includeMarketingFlagsDetails": "true",
            "enableDynamicFacets": "true",
            "enableSwatchSort": "true",
            "sortSwatchesBy": "bestsellers",
            "pageNumber": pageNumber,
            "vendor": "Certona",
        }

        try:
            res = self.sess.get(url, params=params, headers=headers, timeout=10)

            # 응답 상태 확인
            if res.status_code == 200:
                try:
                    response_json = res.json()  # JSON 응답 파싱
                    rs = response_json.get('pagination', {})  # pagination 키가 없을 경우 빈 딕셔너리 반환

                    if not rs:  # pagination 키가 없는 경우
                        self.log_signal.emit("경고: 응답에 'pagination' 키가 없음")
                        return None

                    return {
                        "total_page_cnt": rs.get('pageNumberTotal', 0),
                        "total_product_cnt": response_json.get('totalColors', 0)
                    }
                except ValueError as e:
                    # JSON 파싱 실패
                    self.log_signal.emit(f"JSON 파싱 에러: {e}")
                    return None
            else:
                # 상태 코드가 200이 아닌 경우
                self.log_signal.emit(f"HTTP 요청 실패: 상태 코드 {res.status_code}, 내용: {res.text}")
                return None

        except Exception as e:
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal.emit(f"요청 중 에러 발생: {e}")
            return None


    # 페이지 데이터 가져오기
    def _get_api_request(self, cid, pageNumber):

        url = "https://api.gap.com/commerce/search/products/v2/cc"

        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": "https://oldnavy.gap.com",
            "referer": "https://oldnavy.gap.com/",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "x-client-application-name": "Browse"
        }

        params = {
            "brand": "on",
            "market": "us",
            "cid": cid,
            "locale": "en_US",
            "pageSize": "300",
            "ignoreInventory": "false",
            "includeMarketingFlagsDetails": "true",
            "enableDynamicFacets": "true",
            "enableSwatchSort": "true",
            "sortSwatchesBy": "bestsellers",
            "pageNumber": pageNumber,
            "vendor": "Certona",
        }

        try:
            res = self.sess.get(url, params=params, headers=headers, timeout=10)

            # 응답 상태 확인
            if res.status_code == 200:
                try:
                    self.log_signal.emit(f"제품 list 가져오기 성공")
                    response_json = res.json()  # JSON 응답 파싱
                    # return [category.get("ccList", []) for category in response_json.get("categories", [])]
                    categories = response_json.get("categories", [])
                    if categories and isinstance(categories, list):
                        return categories[0].get("ccList", [])
                    return []
                except ValueError as e:
                    # JSON 파싱 실패
                    self.log_signal.emit(f"JSON 파싱 에러: {e}")
                    return None
            else:
                # 상태 코드가 200이 아닌 경우
                self.log_signal.emit(f"HTTP 요청 실패: 상태 코드 {res.status_code}, 내용: {res.text}")
                return None

        except Exception as e:
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal.emit(f"요청 중 에러 발생: {e}")
            return None


    def smooth_scroll(self, start, end, step=150, delay=0.1):
        """부드럽게 스크롤을 이동하는 함수 (스크롤 이벤트 감지 활성화)"""
        if start < end:
            for i in range(start, end, step):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(delay)
        else:
            for i in range(start, end, -step):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(delay)


    def get_api_request(self, url, pageNumber):
        scroll_pause_time = 1  # 스크롤 후 대기 시간
        max_no_change = 5  # 높이가 변하지 않으면 종료할 기준 횟수
        no_change_count = 0  # 연속 높이 변화 없음 카운트

        if pageNumber > 0:
            url = f"{url}#pageId={pageNumber}"

        self.driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기

        product_dict = {}  # 중복 제거를 위해 dict 사용
        last_height = self.driver.execute_script("return document.body.scrollHeight")  # 초기 높이 저장

        # ✅ 1. 첫 번째 50% 위치로 부드럽게 이동
        print("➡️ 초기 50% 위치로 부드럽게 이동")
        current_position = int(last_height * 0.5)
        self.smooth_scroll(0, current_position, step=100, delay=0.02)
        time.sleep(2)  # 데이터 로딩 대기

        # ✅ 2. 현재 위치에서 남은 높이의 50%씩 부드럽게 이동 반복
        while True:
            prev_count = len(product_dict)  # 기존 제품 개수 저장

            # ✅ 남은 높이의 50% 계산
            remaining_height = self.driver.execute_script("return document.body.scrollHeight") - current_position
            move_distance = int(remaining_height * 0.5)
            if move_distance < 1:  # 더 이상 이동할 높이가 없으면 종료
                print("⚠️ 이동할 높이 없음, 종료!")
                break

            # ✅ 현재 위치에서 남은 50% 높이만큼 부드럽게 이동
            print(f"⬇️ {current_position} → {current_position + move_distance} 부드럽게 이동")
            self.smooth_scroll(current_position, current_position + move_distance, step=100, delay=0.02)
            current_position += move_distance
            time.sleep(scroll_pause_time)

            # 현재 페이지에서 새로운 제품 요소 수집
            product_elements = self.driver.find_elements(By.CLASS_NAME, "cat_product-image")

            for elem in product_elements:
                product_id = elem.get_attribute("id")
                if product_id:
                    match = re.search(r'product(\d+)', product_id)
                    if match:
                        ccId = match.group(1)
                        if ccId not in product_dict:  # 중복 방지
                            product_dict[ccId] = {'ccId': ccId}

            # ✅ 조건 1: 300개를 모으면 중단
            if len(product_dict) >= 300:
                print("✅ 300개 수집 완료, 종료!")
                break

            # ✅ 높이 변화를 감지하여 종료 조건 확인
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                no_change_count += 1  # 높이가 변하지 않으면 카운트 증가
                if no_change_count >= max_no_change:
                    print(f"⚠️ {max_no_change}번 연속 높이 변화 없음, 스크롤 종료!")
                    break  # **높이가 5번 변하지 않으면 종료**
            else:
                no_change_count = 0  # 데이터가 추가되면 초기화

            last_height = new_height  # 높이 업데이트

        print("✅ 스크롤 완료, 데이터 수집 완료")

        return list(product_dict.values())  # 중복 제거된 객체 배열 반환


    # URL 가져오기
    def get_cid(self, item):
        # CID와 URL을 매핑하는 딕셔너리
        cid_map = {
            "Now Trending!": ("3028309", ""),
            "Activewear": ("3028158", ""),
            "Women": ("1185233", ""),
            "Men": ("1031099", ""),
            "Girls": ("1185229", ""),
            "Boys": ("1185232", ""),
            "Toddler": ("1185224", ""),
            "Baby": ("1185226", ""),
            "Maternity": ("1185228", ""),
            "Women / Women’s Tops / Shirts & Blouses": (
                "72087",
                "https://oldnavy.gap.com/browse/women/shirts-and-blouses?cid=72087&nav=meganav%3AWomen%3AWomen%E2%80%99s+Tops%3AShirts+%26+Blouses"
            ),
            "Women / Women’s Tops / Button-down Shirts": (
                "3031932",
                "https://oldnavy.gap.com/browse/women/button-down-shirts?cid=3031932&nav=meganav%3AWomen%3AWomen%E2%80%99s+Tops%3AButton-Down+Shirts"
            ),
            "Women / Women’s Bottoms / Pants": (
                "5475",
                "https://oldnavy.gap.com/browse/women/pants?cid=5475&nav=meganav%3AWomen%3AWomen%27s%20Bottoms%3APants"
            ),
            "Women / Women’s Bottoms / Shorts": (
                "35158",
                "https://oldnavy.gap.com/browse/women/shorts?cid=35158&nav=meganav%3AWomen%3AWomen%27s%20Bottoms%3AShorts"
            ),
            "Women / Women’s Bottoms / Skirts": (
                "79586",
                "https://oldnavy.gap.com/browse/women/skirts?cid=79586&nav=meganav%3AWomen%3AWomen%27s%20Bottoms%3ASkirts"
            ),
            "Women / Shop Women’s Categories / Dresses & Jumpsuits": (
                "15292",
                "https://oldnavy.gap.com/browse/women/dresses-and-jumpsuits?cid=15292&nav=meganav%3AWomen%3AShop%20Women%27s%20Categories%3ADresses%20%26%20Jumpsuits"
            ),
        }

        # 값 조회 (존재하지 않으면 기본값 "" 반환)
        return cid_map.get(item, ("", ""))


    # 전체 갯수 조회
    def total_cnt_cal(self):
        check_obj_list = []

        for checked_obj in self.checked_list:
            name = checked_obj.get('name', '')  # 안전한 딕셔너리 접근

            # cid 및 url 조회
            cid, url = self.get_cid(name)

            # cid가 없으면 요청 생략
            cnt_result = self.main_request(cid, 0) if cid else {'total_page_cnt': 0, 'total_product_cnt': 0}

            # 값 업데이트
            checked_obj.update({
                'cid': cid,
                'url': url,
                'total_page_cnt': cnt_result['total_page_cnt'],
                'total_product_cnt': cnt_result['total_product_cnt']
            })

            check_obj_list.append(checked_obj)

            time.sleep(0.5)  # API 요청 간격 유지

        return check_obj_list

