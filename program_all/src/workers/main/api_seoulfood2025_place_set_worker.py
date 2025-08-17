import math
import random
import time
import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import requests
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiSeoulfood2025PlaceSetLoadWorker(BaseApiWorker):


    # 초기화
    def __init__(self):
        super().__init__()
        self.cookies = None
        self.keyword = None
        self.base_main_url   = "https://seoulfood.kotra.biz/fairDash.do?hl=KOR"
        self.site_name = "SEOUL FOOD 2025"

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

        self.driver_set(True)

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.base_main_url)


    # 프로그램 실행
    def main(self):
        try:
            result_list = []
            self.set_cookies()

            self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
            self.log_signal_func("전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
            self.total_cnt_cal(1)
            self.log_signal_func(f"전체 업체수 {self.total_cnt} 개")
            self.log_signal_func(f"전체 페이지수 {self.total_pages} 개")

            excel_filename = self.file_driver.get_excel_filename(self.site_name)

            columns = ["NO", "업체명", "홈페이지", "국가 및 지역", "전시품목", "PAGE"]
            df = pd.DataFrame(columns=columns)
            df.to_excel(excel_filename, index=False)

            for page in range(1, self.total_pages + 1):
                try:
                    response = self.fetch_search_results(page)
                    if response and isinstance(response, dict):
                        prodList = response.get("prodList", [])

                        for item in prodList:
                            self.current_cnt += 1

                            company_name = item.get("cfair_name_kor") or item.get("cfair_name_eng", "")
                            country = item.get("country")
                            if not country:
                                country_json = item.get("cfair_country_json", {})
                                country = country_json.get("n", "")

                            obj = {
                                "NO": self.current_cnt,
                                "업체명": company_name,
                                "홈페이지": item.get("cfair_homepage", ""),
                                "국가 및 지역": country,
                                "전시품목": ", ".join(filter(None, item.get("ex_item_cate", []))) if item.get("ex_item_cate") else "",
                                "PAGE": page
                            }
                            result_list.append(obj)

                        if result_list:
                            self.log_signal_func(f"대표 데이터 {result_list[-1]}")
                except Exception as e:
                    self.log_signal_func(f"❌ 페이지 {page} 처리 중 예외 발생: {e}")
                    return False

                if page % 5 == 0:
                    try:
                        self.excel_driver.append_to_excel(excel_filename, result_list, columns)
                    except Exception as e:
                        self.log_signal_func(f"❌ 엑셀 저장 중 오류 발생 (5페이지 단위): {e}")
                        return False

                pro_value = (page / self.total_pages) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal_func(f"현재 페이지 {page}/{self.total_pages} : {self.current_cnt}/{self.total_cnt}")
                time.sleep(random.uniform(1, 1.2))

            if result_list:
                try:
                    self.excel_driver.append_to_excel(excel_filename, result_list, columns)
                except Exception as e:
                    self.log_signal_func(f"❌ 최종 엑셀 저장 중 오류 발생: {e}")
                    return False

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

        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)


    # 로그인 확인
    def set_cookies(self):
        self.log_signal_func("📢 쿠키 세팅 시작")
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)
        self.log_signal_func("📢 쿠키 세팅 완료")
        time.sleep(2)  # 예제용


    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()


    # 전체 갯수 조회
    def total_cnt_cal(self, page):
        try:
            response = self.fetch_search_results(page)

            if response and isinstance(response, dict):
                pages_json = response.get("pagesJson", {})
                total_rows = pages_json.get("totalRows")
                num_of_rows = pages_json.get("numOfRows")

                if total_rows is not None and num_of_rows is not None: # 0일수 있으므로 None으로 확인
                    self.total_cnt = int(total_rows)
                    self.total_pages = math.ceil(int(total_rows) / int(num_of_rows))
                else:
                    self.log_signal_func("⚠️ totalRows 또는 numOfRows 값이 누락되었습니다.")
            else:
                self.log_signal_func("❌ 유효하지 않은 응답 형식입니다.")
        except Exception as e:
            self.log_signal_func(f"❌ Error calculating total count: {e}")


    # 목록조회
    def fetch_search_results(self, page):
        try:
            url = f"https://seoulfood.kotra.biz/fairOnline.do"

            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "connection": "keep-alive",
                "content-length": "65",  # 보통은 requests에서 자동 처리됨 → 제거해도 무방
                "content-type": "application/json;charset=UTF-8",
                "host": "seoulfood.kotra.biz",  # requests가 자동 설정함 → 생략 가능
                "origin": "https://seoulfood.kotra.biz",
                "referer": "https://seoulfood.kotra.biz/fairOnline.do?hl=KOR&selAction=single_page&SYSTEM_IDX=71",
                "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            }

            payload = {
                "SYSTEM_IDX": "71",
                "selOrder": "cfair_nm_replace",
                "selPageNo": str(page)
            }

            response = self.api_client.post(url=url, headers=headers, json=payload)
            return response
        except requests.exceptions.RequestException as e:
            self.log_signal_func(f"❌ 요청 실패: {e}")
            return None

    
    # 중지
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
