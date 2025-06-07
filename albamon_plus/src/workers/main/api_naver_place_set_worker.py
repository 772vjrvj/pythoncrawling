import json
import random
import re
import threading
import time
from urllib.parse import urlparse, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from bs4 import BeautifulSoup

from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiNaverPlaceSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self, setting):
        super().__init__()
        self.cookies = None
        self.keyword = None
        self.base_login_url = "https://nid.naver.com/nidlogin.login"
        self.base_main_url   = "https://map.naver.com"
        self.site_name = "네이버플레이스"

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.sess = None
        self.running = True
        self.driver = None
        self.base_url = None
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

    # 초기화
    def init(self):

        self.driver_set()

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.base_login_url)


    # 프로그램 실행
    def main(self):
        result_list = []
        self.wait_for_user_confirmation()
        self.wait_for_select_confirmation()

        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        all_ids_list = self.total_cnt_cal()
        self.log_signal_func(f"전체 업체수 {self.total_cnt} 개")
        self.log_signal_func(f"전체 페이지수 {self.total_pages} 개")

        csv_filename = self.file_driver.get_csv_filename(self.site_name)

        columns = ["업체명", "주소(지번)", "주소(도로명)", "전화번호", "가상전화번호", "검색어"]

        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")


        for index, place_id in enumerate(all_ids_list, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            obj = self.fetch_place_info(place_id)
            result_list.append(obj)
            if index % 5 == 0:
                self.excel_driver.append_to_csv(csv_filename, result_list, columns)

            self.current_cnt = self.current_cnt + 1

            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

            self.log_signal_func(f"현재 페이지 {self.current_cnt}/{self.total_cnt} : {obj}")
            time.sleep(random.uniform(2, 3))


        if result_list:
            self.excel_driver.append_to_csv(csv_filename, result_list, columns)

    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless=False)


        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)


    # 로그인 확인
    def wait_for_user_confirmation(self):
        self.log_signal_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")

        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal_func("로그인 후  후 OK를 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        # 쿠키 중 NID_AUT 또는 NID_SES 쿠키가 있는지 확인 (네이버 로그인 성공 시 생성되는 쿠키)
        if 'NID_AUT' in cookies and 'NID_SES' in cookies:
            for name, value in cookies.items():
                self.api_client.cookie_set(name, value)

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        self.driver.get(self.base_main_url)

        time.sleep(2)  # 예제용

        self.log_signal_func("🚀 작업 완료!")

    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 검색어 확인
    def wait_for_select_confirmation(self):
        """사용자가 확인(alert) 창에서 OK를 누를 때까지 대기"""
        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal_func("검색창에 키워드로 검색후에 OK를 눌러주세요(아래 목록이 나오는걸 확인하세요)", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        current_url = self.driver.current_url
        parsed = urlparse(current_url)
        path = parsed.path  # 예: /p/search/%EB%A7%9D%ED%8F%AC%EC%97%AD%20%EA%B0%88%EB%B9%84
        keyword_encoded = path.split("/p/search/")[-1]  # 인코딩된 키워드 추출
        self.keyword = unquote(keyword_encoded)  # 디코딩

        self.log_signal_func(f"🔍 키워드: {self.keyword}")

        time.sleep(2)  # 예제용

        self.log_signal_func("🚀 작업 완료!")

    # 전체 갯수 조회
    def total_cnt_cal(self):
        try:
            page = 1
            all_ids = set()

            # 키워드에 매핑되는 아이디 수집
            while True:
                time.sleep(random.uniform(1, 2))

                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                result = self.fetch_search_results(page)
                if not result:
                    break

                place_list = result.get("result", {}).get("place", {}).get("list", [])
                ids_this_page = [place.get("id") for place in place_list if place.get("id")]

                self.log_signal_func(f"페이지: {page}, 목록: {ids_this_page}")

                if not ids_this_page:
                    break

                all_ids.update(ids_this_page)
                page += 1

            all_ids_list = list(all_ids)
            self.total_cnt = len(all_ids_list)
            self.total_pages = page
            return all_ids_list

        except Exception as e:
            print(f"Error calculating total count: {e}")
            return None

    # 목록조회
    def fetch_search_results(self, page):
        try:
            url = f"https://map.naver.com/p/api/search/allSearch?query={self.keyword}&type=all&searchCoord=&boundary=&page={page}"
            headers = {
                'Referer': 'https://map.naver.com/',  # ✅ 반드시 필요
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
            response = self.api_client.get(url=url, headers=headers)
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 실패: {e}")
            return None

    # 상세조회
    def fetch_place_info(self, place_id):
        result = {
            "업체명": "",
            "주소(지번)": "",
            "주소(도로명)": "",
            "전화번호": "",
            "가상전화번호": "",
            "검색어": "",
        }

        try:
            url = f"https://m.place.naver.com/place/{place_id}"
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }

            res = self.api_client.get(url=url, headers=headers)

            if res:
                soup = BeautifulSoup(res, 'html.parser')
                script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))

                if script_tag:
                    json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
                    if json_text:
                        data = json.loads(json_text.group(1))
                        name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")
                        address = data.get(f"PlaceDetailBase:{place_id}", {}).get("address", "")
                        roadAddress = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")
                        phone = data.get(f"PlaceDetailBase:{place_id}", {}).get("phone", "")
                        virtualPhone = data.get(f"PlaceDetailBase:{place_id}", {}).get("virtualPhone", "")

                        result["업체명"] = name
                        result["주소(지번)"] = address
                        result["주소(도로명)"] = roadAddress
                        result["전화번호"] = phone
                        result["가상전화번호"] = virtualPhone
                        result["검색어"] = self.keyword
        except Exception as e:
            self.log_signal_func(f"Error processing data for Place ID: {place_id}: {e}")
        finally:
            return result


    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
