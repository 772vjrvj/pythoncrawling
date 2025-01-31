from PyQt5.QtCore import QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pyautogui
import pyperclip

blog_ing = 0

# API
class ApiNaverSetLoadWorker(QThread):
    api_data_received = pyqtSignal(object)  # API 호출 결과를 전달하는 시그널

    def __init__(self, url_list, query='', content='', blog_host_url = '', parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.cookie = None
        self.query = query
        self.content = content
        self.blog_host_url = blog_host_url
        self.driver = None
        self.setup_driver()

    def run(self):
        self.on_naver_login()
        for idx, place_id in enumerate(self.url_list, start=1):
            self.delete_images_in_directory('place_images')
            place_info = self.fetch_place_info(place_id)
            if place_info:
                # 이미지 폴더 삭제
                reviews_info = self.fetch_reviews(place_id)
                place_info["리뷰"] = reviews_info.get("reviews", [])
                place_info["리뷰 분석"] = reviews_info.get("stats", [])
                place_info["공유 URL"] = self.fetch_link_url(place_id)
                place_info["블로그 제목"] = f"{self.query} / {place_info['이름']} / 운영시간 가격 주차리뷰"
                image_urls = self.fetch_photos(place_id)
                time.sleep(2)
                os.makedirs('place_images', exist_ok=True)
                for i, image_url in enumerate(image_urls, start=1):
                    self.download_image(image_url, f'place_images/{i}.jpg')
                time.sleep(3)
                place_info['이미지 URLs'] = image_urls
                place_info["블로그 게시글"] = "\n\n\n\n".join([self.print_place_info(place_info), self.content])
                self.parent.add_log(f"번호 : {idx}, 이름 : {place_info}")

                self.naver_upload(place_info)

                pro_value = (idx / len(self.url_list)) * 1000000
                self.parent.set_progress(pro_value)


    # 이미지 삭제 함수
    def delete_images_in_directory(self, directory_path):
        # 디렉터리 내 모든 파일을 삭제
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):  # 파일만 삭제
                os.remove(file_path)


    def naver_upload(self, place_info):
        driver = self.driver
        driver.get(self.blog_host_url + "?Redirect=Write&")

        try:
            time.sleep(3)  # 페이지 로드 시간 추가

            # iframe으로 전환
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'mainFrame'))  # iframe의 ID로 전환
            )
            driver.switch_to.frame(iframe)

            try:
                # 작성중인글 확인
                time.sleep(1)
                # 이제 iframe 내에서 요소를 찾음
                popup_button = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-cancel'))
                )
                popup_button.click()

            except TimeoutException:
                # close_button이 없을 경우에 실행될 코드 (필요에 따라 생략 가능)
                self.parent.add_log("작성중인글이 존재하지 않습니다.")


            # 3초 후 텍스트 입력 (클래스 이름 'se-ff-nanumgothic se-fs32 __se-node' 내부에 텍스트 '1234' 입력)
            time.sleep(1)

            # 요소 찾기

            # 더 세밀하게 특정 요소를 클릭하고 텍스트 입력
            bb = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"제목")]'))
            )
            # 클릭 후 텍스트 삽입
            bb.click()
            actions = ActionChains(driver)
            actions.send_keys(place_info["블로그 제목"]).perform()




            if len(place_info['이미지 URLs']) > 0:

                # 이제 iframe 내에서 요소를 찾음
                image_upload_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-image-toolbar-button'))
                )
                image_upload_button.click()
                time.sleep(1)  # 파일 선택 창이 열릴 때까지 대기
                # 현재 프로그램이 실행되는 경로
                current_dir = os.getcwd()

                # 'images' 폴더의 경로
                images_dir = os.path.join(current_dir, 'place_images')

                # Windows 파일 선택 창에서 경로를 입력하고 '열기' 버튼을 누름

                # 경로가 정확한지 확인
                if not os.path.exists(images_dir):
                    messagebox.showerror("경로 오류", f"경로가 존재하지 않습니다: {images_dir}")
                    return


                try:
                    # 상단 경로 입력창에 포커스 맞추기 (탐색기 창에서 경로 입력)
                    pyautogui.hotkey('alt', 'd')  # 상단 경로창 선택
                    time.sleep(1)

                    # 클립보드를 사용해 경로 입력
                    pyperclip.copy(images_dir)  # 경로를 클립보드에 복사
                    pyautogui.hotkey('ctrl', 'v')  # 클립보드에서 붙여넣기 (Ctrl + V)
                    pyautogui.press('enter')  # 엔터키로 폴더 열기

                    time.sleep(1)  # 폴더 열리는 시간 대기

                    # 파일 목록에 포커스 맞추기 (탐색기 창에서 파일 선택으로 이동)
                    pyautogui.press('tab')  # 경로창에서 파일 목록으로 이동하기 위해 탭 누르기
                    pyautogui.press('tab')  # 두 번째 탭을 누르면 파일 목록에 포커스가 맞춰짐
                    pyautogui.press('tab')  # 세 번째 탭을 누르면 포커스가 맞춰짐
                    pyautogui.press('tab')  # 네 번째 탭을 누르면 포커스가 맞춰짐
                    pyautogui.press('down')  # 파일 목록의 첫 번째 파일로 이동

                    # 전체 파일 선택 (Ctrl + A)
                    pyautogui.hotkey('ctrl', 'a')  # 모든 파일 선택

                    # 파일 열기(확인) 버튼 클릭 (Windows 기준)
                    pyautogui.press('enter')  # 열기 버튼을 눌러 파일 업로드

                    time.sleep(3)

                    if len(place_info['이미지 URLs']) != 1:
                        # 이제 iframe 내에서 요소를 찾음 (이미지 업로드 후 추가 작업)
                        image_upload_button2 = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'se-image-type-label'))
                        )

                        driver.execute_script("arguments[0].click();", image_upload_button2)
                        time.sleep(3)
                except Exception as e:
                    self.parent.add_log(f"이미지 업로드 에러")


            # 스크롤을 맨 위로 올리기
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # 활성화된 요소 가져오기
            active_element = driver.switch_to.active_element
            # ActionChains로 클릭 후 텍스트 입력 시도
            actions = ActionChains(driver)

            if place_info["블로그 게시글"]:
                actions.move_to_element(active_element).click().send_keys(place_info["블로그 게시글"]).perform()
            else:
                actions.move_to_element(active_element).click().send_keys(place_info["블로그 제목"]).perform()



            # 지도 넣기

            image_map_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'se-map-toolbar-button'))
            )
            image_map_button.click()

            time.sleep(1)
            # input 필드 찾기
            input_field = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "react-autosuggest__input"))
            )

            # input 필드에 'a' 입력
            input_field.send_keys(place_info['이름'])
            time.sleep(2)
            # 검색 버튼 찾기
            search_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "se-place-search-button"))
            )

            # 검색 버튼 클릭
            search_button.click()

            time.sleep(2)

            try:
                # class가 'se-place-map-search-result-list'인 첫 번째 li 내의 'se-place-add-button' 찾기
                search_result_list = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-place-map-search-result-list'))
                )

                # 'se-place-map-search-result-list' 안에서 첫 번째 'li' 요소를 기다리며 찾음
                first_li = WebDriverWait(search_result_list, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'li'))
                )

                # 마우스를 'first_li' 위로 오버
                actions = ActionChains(driver)
                actions.move_to_element(first_li).perform()  # 마우스를 해당 요소 위로 이동

                # li 내부의 'se-place-add-button'이 로드될 때까지 기다림
                add_button = WebDriverWait(first_li, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-place-add-button'))
                )
                add_button.click()
                # li 내부의 'se-place-add-button'이 로드될 때까지 기다림
                confirm_map_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-confirm'))
                )

                confirm_map_button.click()

            except (NoSuchElementException, TimeoutException):

                a = self.process_address(place_info['주소'])

                driver.execute_script("arguments[0].value = '';", input_field)

                # input 필드에 'a' 입력
                input_field.send_keys(a)

                # 검색 버튼 찾기
                search_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "se-place-search-button"))
                )

                # 검색 버튼 클릭
                search_button.click()

                time.sleep(2)

                try:
                    # class가 'se-place-map-search-result-list'인 첫 번째 li 내의 'se-place-add-button' 찾기
                    search_result_list = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'se-place-map-search-result-list'))
                    )

                    # 'se-place-map-search-result-list' 안에서 첫 번째 'li' 요소를 기다리며 찾음
                    first_li = WebDriverWait(search_result_list, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'li'))
                    )

                    # 마우스를 'first_li' 위로 오버
                    actions = ActionChains(driver)
                    actions.move_to_element(first_li).perform()  # 마우스를 해당 요소 위로 이동

                    # li 내부의 'se-place-add-button'이 로드될 때까지 기다림
                    add_button = WebDriverWait(first_li, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'se-place-add-button'))
                    )
                    add_button.click()

                    # li 내부의 'se-place-add-button'이 로드될 때까지 기다림
                    confirm_map_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-confirm'))
                    )

                    confirm_map_button.click()

                except (NoSuchElementException, TimeoutException):

                    # 'se-place-add-button'이 없으면 'se-popup-close-button'을 찾아 클릭
                    try:
                        close_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, 'se-popup-close-button'))
                        )
                        close_button.click()
                    except (NoSuchElementException, TimeoutException):
                        self.parent.add_log("close_button을 찾을 수 없습니다.")



            # 3초 후 'publish_btn__m9KHH' 클래스 버튼 클릭
            # 발행
            publish_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'publish_btn__m9KHH'))
            )
            driver.execute_script("arguments[0].click();", publish_button)

            # 3초 후 'confirm_btn__WEaBq' 클래스 버튼 클릭
            confirm_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'confirm_btn__WEaBq'))
            )
            driver.execute_script("arguments[0].click();", confirm_button)

        except Exception as e:
            self.parent.add_log(f"에러 발생: {e}")


    def process_address(self, address):
        # 공백과 콤마, 점을 제거한 주소로 시작
        address = address.strip().rstrip(',').rstrip('.')

        # 공백으로 쪼갠다
        parts = address.split()

        # '층' 또는 '호'로 끝나는 단어가 있는지 확인
        for i in range(len(parts)-1, -1, -1):
            if parts[i].endswith('층') or parts[i].endswith('호'):
                # '층' 또는 '호'가 있으면 그 뒤의 모든 단어 삭제
                parts = parts[:i]
                break

        # 결과를 띄어쓰기로 이어서 반환
        return ' '.join(parts)



    def on_naver_login(self):

        self.driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

        # 로그인 여부를 주기적으로 체크
        logged_in = False
        max_wait_time = 300  # 최대 대기 시간 (초)
        start_time = time.time()

        while not logged_in:
            # 1초 간격으로 쿠키 확인
            time.sleep(1)
            elapsed_time = time.time() - start_time

            # 최대 대기 시간 초과 시 while 루프 종료
            if elapsed_time > max_wait_time:
                self.parent.add_log("경고 로그인 실패: 300초 내에 로그인하지 않았습니다.")
                self.driver.quit()
                break

            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

            # 쿠키 중 NID_AUT 또는 NID_SES 쿠키가 있는지 확인 (네이버 로그인 성공 시 생성되는 쿠키)
            if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                logged_in = True
                self.parent.add_log("로그인 성공 정상 로그인 되었습니다.")
                self.cookie = cookies


    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1080,750")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                '''
        })
        self.driver = driver


    def fetch_place_info(self, place_id):
        try:
            url = f"https://m.place.naver.com/place/{place_id}"

            headers = {
                'authority': 'm.place.naver.com',
                'method': 'GET',
                'scheme': 'https',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'priority': 'u=0, i',
                'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, cookies=self.cookie)

            if response.status_code == 200:
                response.encoding = response.apparent_encoding  # 자동 감지된 인코딩을 적용
                html_content = response.content.decode('utf-8', errors='ignore')  # UTF-8로 직접 디코딩
                soup = BeautifulSoup(html_content, 'html.parser')
                script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))

                if script_tag:
                    json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
                    if json_text:
                        data = json.loads(json_text.group(1))

                        address = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")
                        name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")
                        virtualPhone = data.get(f"PlaceDetailBase:{place_id}", {}).get("virtualPhone", "")

                        prices = []
                        for key, value in data.items():
                            if key.startswith(f"Menu:{place_id}"):
                                prices.append(value)

                        facilities = []
                        for key, value in data.items():
                            if key.startswith("InformationFacilities:"):
                                facilities.append(value)


                        root_query = data.get("ROOT_QUERY", {})
                        place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                        information = root_query.get(place_detail_key, {}).get('description({"source":["shopWindow","jto"]})', "")

                        business_hours = root_query.get(place_detail_key, {}).get('businessHours({"source":["tpirates","jto","shopWindow"]})', [])

                        new_business_hours = root_query.get(place_detail_key, {}).get('newBusinessHours', [])

                        url = f"https://m.place.naver.com/place/{place_id}/home"
                        map_url = f"https://map.naver.com/p/entry/place/{place_id}"

                        result = {
                            "아이디": place_id,
                            "이름": name,
                            "주소": address,
                            "가상번호": virtualPhone,
                            "금액": prices,
                            "편의": facilities,
                            "영업시간": business_hours,
                            "새로운 영업시간": new_business_hours,
                            "정보": information,
                            "정보 URL": url,
                            "지도 URL": map_url
                        }

                        return result

        except requests.exceptions.RequestException as e:
            self.parent.add_log(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
        except Exception as e:
            self.parent.add_log(f"Error processing data for Place ID: {place_id}: {e}")
        return None


    def fetch_reviews(self, place_id):
        try:
            url = "https://api.place.naver.com/place/graphql"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ko-KR,ko;q=0.9',
                'Origin': f'https://m.place.naver.com',
                'Referer': f'https://m.place.naver.com/place/{place_id}/home'
            }

            payload = [
                {
                    "operationName": "getVisitorReviews",
                    "variables": {
                        "input": {
                            "businessId": place_id,
                            "businessType": "place",
                            "size": 7,
                            "page": 1,
                            "includeContent": True,
                            "cidList": ["222412", "222415", "222446", "1004920"]
                        }
                    },
                    "query": """
                    query getVisitorReviews($input: VisitorReviewsInput) {
                      visitorReviews(input: $input) {
                        items {
                          id
                          rating
                          author {
                            nickname
                            imageUrl
                          }
                          body
                          created
                          tags
                          media {
                            type
                            thumbnail
                          }
                        }
                        total
                      }
                    }"""
                },
                {
                    "operationName": "getVisitorReviewStats",
                    "variables": {
                        "businessType": "place",
                        "id": place_id
                    },
                    "query": """
                    query getVisitorReviewStats($id: String, $businessType: String = "place") {
                      visitorReviewStats(input: {businessId: $id, businessType: $businessType}) {
                        id
                        name
                        review {
                          avgRating
                          totalCount
                        }
                        analysis {
                          votedKeyword {
                            totalCount
                            reviewCount
                            userCount
                            details {
                              code
                              iconUrl
                              displayName
                              count
                            }
                          }
                        }
                      }
                    }"""
                }
            ]

            response = requests.post(url, headers=headers, json=payload, cookies=self.cookie)
            response.raise_for_status()

            review_data = response.json()

            if review_data and len(review_data) > 1:
                visitor_reviews_data = review_data[0].get("data", {}).get("visitorReviews", {})
                visitor_reviews = visitor_reviews_data.get("items", []) if visitor_reviews_data else []

                analysis_data = review_data[1].get("data", {}).get("visitorReviewStats", {})
                voted_keyword_data = analysis_data.get("analysis", {}) if analysis_data else {}

                # 여기서 votedKeyword가 None일 때를 추가로 처리
                voted_keyword_details = (
                    voted_keyword_data.get("votedKeyword", {}).get("details", [])
                    if voted_keyword_data.get("votedKeyword") is not None
                    else []
                )

                return {
                    "reviews": visitor_reviews,
                    "stats": voted_keyword_details
                }
            else:
                self.parent.add_log(f"No review data available for Place ID: {place_id}")
                return {"reviews": [], "stats": []}

        except requests.exceptions.RequestException as e:
            self.parent.add_log(f"Failed to fetch reviews for Place ID: {place_id}. Error: {e}")
            return {"reviews": [], "stats": []}
        except Exception as e:
            self.parent.add_log(f"Error while processing data for Place ID: {place_id}: {e}")
            return {"reviews": [], "stats": []}


    def fetch_photos(self, place_id):
        url = "https://api.place.naver.com/graphql"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Origin': 'https://m.place.naver.com',
            'Referer': f'https://m.place.naver.com/place/{place_id}/home'
        }
        payload = [
            {
                "operationName": "getPhotoViewerItems",
                "variables": {
                    "input": {
                        "businessId": place_id,
                        "businessType": "restaurant",
                        "cursors": [
                            {"id": "biz"},
                            {"id": "cp0"},
                            {"id": "visitorReview"},
                            {"id": "clip"},
                            {"id": "imgSas"}
                        ],
                        "excludeAuthorIds": [],
                        "excludeSection": [],
                        "excludeClipIds": [],
                        "dateRange": ""
                    }
                },
                "query": """
                query getPhotoViewerItems($input: PhotoViewerInput) {
                  photoViewer(input: $input) {
                    cursors {
                      id
                      startIndex
                      hasNext
                      lastCursor
                      __typename
                    }
                    photos {
                      viewId
                      originalUrl
                      width
                      height
                      title
                      text
                      desc
                      link
                      date
                      photoType
                      mediaType
                      option {
                        channelName
                        dateString
                        playCount
                        likeCount
                        __typename
                      }
                      to
                      relation
                      logId
                      author {
                        id
                        nickname
                        from
                        imageUrl
                        objectId
                        url
                        borderImageUrl
                        __typename
                      }
                      votedKeywords {
                        code
                        iconUrl
                        iconCode
                        displayName
                        __typename
                      }
                      visitCount
                      originType
                      isFollowing
                      businessName
                      rating
                      externalLink {
                        title
                        url
                        __typename
                      }
                      sourceTitle
                      moment {
                        channelId
                        contentId
                        momentId
                        gdid
                        blogRelation
                        statAllowYn
                        category
                        docNo
                        __typename
                      }
                      video {
                        videoId
                        videoUrl
                        trailerUrl
                        __typename
                      }
                      music {
                        artists
                        title
                        __typename
                      }
                      clip {
                        viewerHash
                        __typename
                      }
                      __typename
                    }
                    __typename
                  }
                }
                """
            }
        ]
        image_urls = []
        try:
            response = requests.post(url, json=payload, headers=headers, cookies=self.cookie)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            data = response.json()

            # 원하는 데이터 추출 예시 (originalUrl만 추출)
            photos = data[0].get('data', {}).get('photoViewer', {}).get('photos', [])
            for photo in photos:
                image_urls.append(photo.get('originalUrl'))

            return image_urls[:5]

        except requests.exceptions.RequestException as e:
            self.parent.add_log(f"Request failed: {e}")
            return image_urls


    def fetch_link_url(self, place_id):
        url = "https://me2do.naver.com/common/requestJsonpV2"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "me2do.naver.com",
            "referer": f"https://pcmap.place.naver.com/{place_id}/home?from=map&fromPanelNum=1&additionalHeight=76&timestamp=202410090914",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "script",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        }
        params = {
            "_callback": "window.spi_9197316230",
            "svcCode": "0022",
            "url": f"https://m.place.naver.com/share?id={place_id}&tabsPath=%2Fhome&appMode=detail"
        }
        link_url = ""
        try:
            # GET 요청 보내기
            response = requests.get(url, headers=headers, params=params, cookies=self.cookie)

            # 응답 내용에서 콜백 함수 제거 (JSON 부분만 추출하기 위해 정규 표현식 사용)
            jsonp_data = response.text
            json_data = re.search(r'window\.spi_9197316230\((.*)\)', jsonp_data).group(1)

            # 추출된 JSON 문자열을 파이썬 딕셔너리로 변환
            data = json.loads(json_data)

            # 필요한 'url' 값 출력
            link_url = data['result']['url']
            return link_url

        except requests.exceptions.RequestException as e:
            self.parent.add_log(f"Request failed: {e}")
            return link_url


    def download_image(self, image_url, save_path):
        try:
            img_data = requests.get(image_url).content
            with open(save_path, 'wb') as handler:
                handler.write(img_data)
        except Exception as e:
            self.parent.add_log(f"Failed to download {image_url}: {e}")


    def print_place_info(self, place_info):
        try:
            # 각 항목을 포맷
            formatted_address = self.format_address(place_info.get("주소", ""))
            formatted_phone = self.format_phone_number(place_info.get("가상번호", ""), place_info.get("이름", ""))
            formatted_price = self.format_price(place_info.get("금액", []))
            formatted_facilities = self.format_facilities(place_info.get("편의", []))
            # formatted_business_hours = format_business_hours(place_info.get("영업시간", []))
            formatted_new_business_hours = self.format_new_business_hours(place_info.get("새로운 영업시간", []))
            formatted_information = self.extract_information(place_info.get("정보", []))
            formatted_reviews = self.format_review_analysis(place_info.get("리뷰 분석", []))
            map_url = place_info.get("지도", "")

            # 유효한 항목만을 리스트에 추가
            sections = [
                formatted_address,
                formatted_new_business_hours,
                # formatted_business_hours,
                formatted_phone,
                formatted_price,
                formatted_facilities,
                formatted_information,
                formatted_reviews,
                f"🗺️ 지도\n{formatted_address}" if formatted_address else ""
            ]

            # 유효한 항목을 합치고, 각 항목 사이에 3개의 엔터를 추가
            content = "\n\n\n\n".join(section for section in sections if section)

            return content.strip()  # 앞뒤 공백 제거
        except Exception as e:
            self.parent.add_log(f'e : {e}')
            return ""


    def format_review_analysis(self, review_analysis):
        formatted_items = []
        try:
            top_items = review_analysis[:7]
            for item in top_items:
                count = item.get('count', 0)
                display_name = item.get('displayName', '')
                if count and display_name:
                    if count == 1:
                        formatted_items.append(f"- 1명의 방문자가 \"{display_name}\"라고 언급했습니다.")
                    else:
                        formatted_items.append(f"- {count}명의 방문자분들이 \"{display_name}\"라고 언급했습니다.")
        except Exception:
            return ""
        return "⭐ 방문자 후기\n" + '\n'.join(formatted_items).strip() if formatted_items else ""


    def format_address(self, address):
        try:
            return f"📍 {address}".strip() if address else ""
        except Exception:
            return ""


    def format_phone_number(self, virtual_number, name=''):
        try:
            if virtual_number:
                formatted_phone = (f"📞 전화번호\n"
                                   f"{virtual_number}\n"
                                   f"‘{name}’(으)로 연결되는 스마트콜 번호입니다.\n"
                                   f"업체 전화번호 {virtual_number}".strip())
                return formatted_phone
            return ""
        except Exception:
            return ""


    def format_price(self, prices):
        formatted_prices = []
        try:
            for price_info in prices:
                name = price_info.get('name', '')
                price = price_info.get('price', '')
                if name and price:
                    try:
                        formatted_price = f"{int(price):,}원"
                        formatted_prices.append(f"- {name} {formatted_price}")
                    except ValueError:
                        continue
        except Exception:
            return ""
        return "💵 금액\n" + '\n'.join(formatted_prices).strip() if formatted_prices else ""


    def format_facilities(self, facilities):
        try:
            facility_names = [facility.get('name', '') for facility in facilities]
            return "🏷️ 편의\n" + ', '.join(facility_names).strip() if facility_names else ""
        except Exception:
            return ""


    def format_business_hours(self, business_hours):
        formatted_hours = []
        try:
            for hour in business_hours:
                day = hour.get('day', '')
                start_time = hour.get('startTime', '')
                end_time = hour.get('endTime', '')
                if day and start_time and end_time:
                    formatted_hours.append(f"{day} {start_time} - {end_time}")
        except Exception:
            return ""
        return "⏰ 영업시간\n" + '\n'.join(formatted_hours).strip() if formatted_hours else ""


    def format_new_business_hours(self, new_business_hours):
        formatted_hours = []
        try:
            if new_business_hours:
                for item in new_business_hours:
                    status_description = item.get('businessStatusDescription', {})
                    status = status_description.get('status', '')
                    description = status_description.get('description', '')

                    if status:
                        formatted_hours.append(status)
                    if description:
                        formatted_hours.append(description)

                    for info in item.get('businessHours', []):
                        day = info.get('day', '')
                        business_hours = info.get('businessHours', {})
                        start_time = business_hours.get('start', '')
                        end_time = business_hours.get('end', '')

                        break_hours = info.get('breakHours', [])
                        break_times = [f"{bh.get('start', '')} - {bh.get('end', '')}" for bh in break_hours]
                        break_times_str = ', '.join(break_times) + ' 브레이크타임' if break_times else ''

                        if day:
                            formatted_hours.append(day)
                        if start_time and end_time:
                            formatted_hours.append(f"{start_time} - {end_time}")
                        if break_times_str:
                            formatted_hours.append(break_times_str)
        except Exception:
            return ""
        return "⏰ 영업시간\n" + '\n'.join(formatted_hours).strip() if formatted_hours else ""


    def extract_information(self, information):
        try:
            return f"ℹ️ {information}".strip() if information else ""
        except Exception:
            return ""