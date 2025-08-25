import os
import re
import time
from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker

# API
class ApiNaverCafeCountOnlySetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://www.onthespot.co.kr/"
        self.url_list = []
        self.running = True  # 실행 상태 플래그 추가
        self.site_name = "naver_cafe"
        self.excel_filename = ""
        self.result_list = []
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)

    # 초기화
    def init(self):

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        return True

    # 메인
    def main(self):
        try:
            self.log_signal_func("크롤링 시작")
            self.url_list = [
                str(row[k]).strip()
                for row in self.excel_data_list
                for k in row.keys()
                if k.lower() == "url" and row.get(k) and str(row[k]).strip()
            ]

            if self.url_list:
                for index, url in enumerate(self.url_list, start=1):
                    if not self.running:  # 실행 상태 확인
                        break
                    obj = self.cafe_detail_api_data(url)
                    self.result_list.append(obj)
                    self.log_signal_func(f"전체 ({index}/{len(self.url_list)}) : {url}")

            excel_filename = self.file_driver.get_excel_filename(self.site_name)
            self.excel_driver.save_obj_list_to_excel(excel_filename, self.result_list, columns=["url", "count"], sheet_name="TX")

            return True
        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False


    def cafe_detail_api_data(self, url):
        """
        네이버 카페 글 URL을 받아 API 요청 → 조회수 가져오기
        """
        # 1) 원본 URL에서 cafeId 부분 추출
        # ex) https://cafe.naver.com/nrdr/404048
        m = re.search(r"cafe\.naver\.com/([^/]+)/(\d+)", url)
        if not m:
            return {"url": url, "count": "URL 형식 오류"}
        cafe_id, article_id = m.group(1), m.group(2)

        # 2) API URL 생성
        api_url = f"https://article.cafe.naver.com/gw/v3/cafes/{cafe_id}/articles/{article_id}?useCafeId=false"

        # 3) 요청 헤더
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "referer": f"https://m.cafe.naver.com/ca-fe/web/cafes/{cafe_id}/articles/{article_id}?useCafeId=false&tc"
        }

        try:
            # 4) 요청 보내기
            json_data = self.api_client.get(api_url, headers=headers)

            # 5) readCount 추출
            count = json_data.get("result", {}).get("article", {}).get("readCount")
            if count is None:
                return {"url": url, "count": "글이 삭제되었습니다"}
            return {"url": url, "count": count}

        except Exception as e:
            self.log_signal_func(f"❌ 조회중 에러: {e}")
            return {"url": url, "count": "글이 삭제되었습니다"}


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



