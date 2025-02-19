import os
import os
import ssl
import time

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver

from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime

ssl._create_default_https_context = ssl._create_unverified_context

image_main_directory = 'oldnavy_images'
company_name = 'oldnavy'
site_name = 'OLDVNAVY'
excel_filename = ''
baseUrl = "https://oldnavy.gap.com/"


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
        global image_main_directory, company_name, site_name, excel_filename, baseUrl

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
                for indx, page in enumerate(range(int(checked_model['start_page']) - 1, int(checked_model['end_page'])), start=1):
                    self.current_page = self.current_page + 1
                    time.sleep(1)
                    self.log_signal.emit(f'{checked_model["name"]}({index}/{len(self.checked_list)})  TotalPage({self.current_page}/{self.total_pages})')
                    if not self.running:
                        break
                    detail_list = self.get_api_request(checked_model['cid'], page)
                    if not detail_list:
                        break
                    for pid_dic in detail_list:
                        pid = pid_dic.get("ccId")
                        if pid not in all_detail_list:
                            all_detail_list[pid] = {
                                "page": page,
                                "pid": pid,
                            }

                all_detail_list = list(all_detail_list.values())  # 리스트 변환
                self.product_info_list = all_detail_list

                self.get_product_info_list(checked_model)

        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()



    def get_product_info_list(self, checked_model):
        result_list = []

        # CSV 파일 경로 설정
        csv_filename = os.path.join(os.getcwd(), f"{checked_model['name']}_{get_current_yyyymmddhhmmss()}.csv")

        # CSV 파일 초기 생성
        columns = ["name", "product", "product_no", "description", "image_url", "image_name", "success", "reg_date", "page", "error"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False)

        for index, product in enumerate(self.product_info_list):
            time.sleep(1)
            obj = self.get_api_product_info(product.get('pid'), product.get('cid'))
            product['product'] = obj.get('product')
            product['description'] = obj.get('description')
            product['img_list'] = obj.get('img_list')
            product['product_no'] = index + 1

            # images 폴더 생성
            images_dir = os.path.join(os.getcwd(), 'images')
            os.makedirs(images_dir, exist_ok=True)

            for ix, image_url in enumerate(product.get('img_list'), start=1):
                if not self.running:
                    break

                obj_copy = product.copy()  # 객체 복사
                obj_copy['name'] = checked_model['name']
                obj_copy['image_url'] = image_url
                obj_copy['success'] = 'N'
                obj_copy['reg_date'] = get_current_formatted_datetime()  # 시간 추가

                try:
                    # 이미지 다운로드
                    response = requests.get(image_url, stream=True)
                    response.raise_for_status()

                    # 이미지 저장 경로
                    img_filename = f"{product.get('pid')}_{ix}.jpg"
                    img_path = os.path.join(images_dir, img_filename)

                    # 이미지 저장
                    with open(img_path, 'wb') as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)

                    obj_copy['success'] = 'Y'  # 성공하면 Y
                    obj_copy['image_name'] = img_filename
                    self.log_signal.emit(f"성공 {obj_copy}")
                except Exception as e:
                    print(f"이미지 다운로드 실패: {image_url}, 오류: {e}")
                    obj_copy['success'] = 'N'  # 실패하면 N 유지
                    obj_copy['error'] = e

            self.current_cnt = self.current_cnt + 1
            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            result_list.append(obj_copy)
            self.log_signal.emit(f'{checked_model["name"]} TotalPage({self.current_page}/{self.total_pages})  TotalProduct({self.current_cnt}/{self.total_cnt}) Product({index+1}/{len(self.product_info_list)})')

            # 5개마다 CSV에 저장
            if index % 5 == 0 and index > 0:
                df = pd.DataFrame(result_list, columns=columns)
                df.to_csv(csv_filename, mode='a', header=False, index=False)
                result_list.clear()  # 저장 후 리스트 초기화

        # 남은 데이터 저장
        if result_list:
            df = pd.DataFrame(result_list, columns=columns)
            df.to_csv(csv_filename, mode='a', header=False, index=False)



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

            obj = {
                "product": soup.find("h1", class_="sitewide-1t5lfed").get_text(strip=True) if soup.find("h1", class_="sitewide-1t5lfed") else "",
                "description": "\n".join(li.get_text(strip=True) for li in soup.select(".drawer-trigger-container .sitewide-jxz45b:nth-of-type(2) .product-information-item__list li")) or "",
                "img_list": [
                    (src if src.startswith("http") else f"https://oldnavy.gap.com/{src.lstrip('/')}")
                    for src in [img["src"] for img in soup.select(".slick-slider.sitewide-zuynlm.slick-initialized img") if "src" in img.attrs]
                ]
            }
            return obj

        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}
        except Exception as e:
            return {"error": f"Parsing error: {e}"}




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
        webdriver_options.add_argument("--headless")

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
        self.driver.quit()


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
    def get_api_request(self, cid, pageNumber):

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


    # URL 가져오기
    def get_cid(self, item):
        cid = ""
        if item:
            name = item

            if name == 'Now Trending!':
                cid = "3028309"
            elif name == 'Activewear':
                cid = "3028158"
            elif name == 'Women':
                cid = "1185233"
            elif name == 'Men':
                cid = "1031099"
            elif name == 'Girls':
                cid = "1185229"
            elif name == 'Boys':
                cid = "1185232"
            elif name == 'Toddler':
                cid = "1185224"
            elif name == 'Baby':
                cid = "1185226"
            elif name == 'Maternity':
                cid = "1185228"
        return cid


    # 전체 갯수 조회
    def total_cnt_cal(self):
        check_obj_list = []
        for index, checked_obj in enumerate(self.checked_list, start=1):
            name = checked_obj['name']

            cid = self.get_cid(name)
            cnt_result = self.main_request(cid, 0)

            checked_obj['cid'] = cid
            checked_obj['total_page_cnt'] = cnt_result['total_page_cnt']
            checked_obj['total_product_cnt'] = cnt_result['total_product_cnt']

            check_obj_list.append(checked_obj)

            time.sleep(1)

        return check_obj_list

