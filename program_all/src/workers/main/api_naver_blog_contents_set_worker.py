import re
import time
import random

import pandas as pd
from bs4 import BeautifulSoup

from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiNaverBlogContentsSetLoadWorker(BaseApiWorker):


    # 초기화
    def __init__(self, setting):
        super().__init__()
        self.blog_id = None
        self.setting = setting
        self.category_list = None
        self.cookies = None
        self.keyword = None
        self.base_main_url   = "https://m.blog.naver.com"
        self.site_name = "네이버 블로그 글조회"

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.running = True
        self.driver = None
        self.base_url = None
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

        self.driver_set(True)
        self.set_cookies()

    # 초기화
    def init(self):
        self.log_signal_func(f"초기화 실행 setting : {self.setting}")


    # 프로그램 실행
    def main(self):
        try:
            st_page = int(self.get_setting_value(self.setting, "st_page"))
            ed_page = int(self.get_setting_value(self.setting, "ed_page"))
            category_no = int(self.get_setting_value(self.setting, "url_select"))

            self.total_pages = ed_page - st_page + 1
            self.total_cnt = self.total_pages * 24

            self.log_signal_func(f"요청 페이지 수 {self.total_pages} 개")
            self.log_signal_func(f"요청 포스트 수 {self.total_cnt} 개")

            excel_filename = self.file_driver.get_excel_filename(self.site_name)

            columns = ["제목", "내용", "URL"]
            df = pd.DataFrame(columns=columns)
            df.to_excel(excel_filename, index=False)

            for page in range(1, self.total_pages + 1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break
                pg = st_page + page - 1
                items = self.fetch_search_results(pg, category_no)
                self.fetch_search_detail_results(items, excel_filename, columns)
            return True
        except Exception as e:
            self.log_signal_func(f"🚨 예외 발생: {e}")
            return False


    def fetch_search_detail_results(self, items, excel_filename, columns):
        result_list = []

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"https://m.blog.naver.com/{self.blog_id}",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }

        for index, item in enumerate(items):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            url = item["URL"]
            res = self.api_client.get(url=url, headers=headers)

            if res:
                soup = BeautifulSoup(res, "html.parser")
                content_area = soup.find("div", class_="se-main-container")
                if content_area:
                    # ❌ id가 'ad-'로 시작하는 모든 하위 요소 제거
                    for ad_div in content_area.find_all(id=lambda x: x and x.startswith("ad-")):
                        ad_div.decompose()

                    text = content_area.get_text(separator="\n", strip=True)
                    item["내용"] = text
                else:
                    item["내용"] = ""

                self.log_signal_func(f"item : {item}")

                result_list.append(item)

            if (index + 1) % 5 == 0:
                self.excel_driver.append_to_excel(excel_filename, result_list, columns)

            time.sleep(random.uniform(1, 1.5))

            self.current_cnt = self.current_cnt + 1
            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

        if result_list:
            self.excel_driver.append_to_excel(excel_filename, result_list, columns)


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

    # 목록조회
    def fetch_search_results(self, page, category_no):
        result_list = []

        url = f"https://m.blog.naver.com/api/blogs/{self.blog_id}/post-list"

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"https://m.blog.naver.com/{self.blog_id}?categoryNo={category_no}&tab=1",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }

        params = {
            "categoryNo": category_no,
            "itemCount": "24",
            "page": page
        }

        res = self.api_client.get(url=url, headers=headers, params=params)

        if res and res.get("isSuccess"):
            items = res.get("result", {}).get("items", [])

            for item in items:
                log_no = item.get("logNo")
                title = item.get("titleWithInspectMessage", "")
                if log_no:
                    result_list.append({
                        "no": log_no,
                        "제목": title,
                        "내용": "",
                        "URL": f"https://m.blog.naver.com/PostView.naver?blogId={self.blog_id}&logNo={log_no}&navType=by"
                    })

        return result_list

    # 카테고리 목록 조회
    def get_list(self, blog_url):
        try:
            match = re.match(r"https?://blog\.naver\.com/([^/?#]+)", blog_url)
            if not match:
                raise ValueError("블로그 URL 형식이 잘못되었습니다.")
            self.blog_id = match.group(1)

            url = f"https://m.blog.naver.com/api/blogs/{self.blog_id}/category-list"

            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "referer": f"https://m.blog.naver.com/{self.blog_id}?tab=1",
                "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            }

            res = self.api_client.get(url=url, headers=headers)
            if res and res.get("isSuccess") is True:
                self.category_list = res.get("result", {}).get("mylogCategoryList", [])
                return [
                    {"key": c["categoryName"], "value": c["categoryNo"]}
                    for c in self.category_list
                    if c.get("categoryName") != "구분선"
                ]
            return []

        except Exception as e:
            self.log_signal_func(f"블로그 목록 조회 중 에러: {e}")
            return []

    # 중지
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
