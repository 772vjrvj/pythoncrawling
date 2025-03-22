import os
import random
import ssl
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs



# API
class ApiOliveyoungSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    finally_finished_signal = pyqtSignal(str)
    msg_signal = pyqtSignal(str, str)

    # 초기화
    def __init__(self, url_list):
        super().__init__()
        self.baseUrl = "https://www.oliveyoung.co.kr"
        self.result_list = []
        self.current_url = ""
        self.before_pro_value = 0
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.end_cnt = 0
        self.file_name = ""
        self.cookies = None
        self.access_token = None
        self.running = True  # 실행 상태 플래그 추가
        self.request_key = None
        self.driver = None
        self.all_end = 'N'

        if len(self.url_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')


    # 실행
    def run(self):
        if len(self.url_list) > 0:
            for idx, url in enumerate(self.url_list, start=1):
                self.current_url = url
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break
                self.end_cnt = idx

                self.log_signal.emit(f'url 번호 : {idx}, 시작')


                self.log_signal.emit("크롤링 시작")
                raw_reviews = self._get_reviews(url)
                self.result_list = self._setting_reviews(raw_reviews)
                self._save_to_excel(self.result_list)

                pro_value = (idx / len(self.url_list)) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                self.log_signal.emit(f'url 번호 : {idx}, 끝')
                time.sleep(random.uniform(2, 3))
                self.result_list = []
        else:
            self.log_signal.emit("USER를 입력하세요.")

        pro_value = 1000000
        self.progress_signal.emit(self.before_pro_value, pro_value)
        time.sleep(3)
        self.log_signal.emit(f'종료 수 : {self.end_cnt}')
        self.progress_end_signal.emit()
        self.log_signal.emit(f'크롤링 종료')


    def _extract_goods_no(self, url):
        """URL에서 goodsNo 값(A000000182989)만 추출하는 함수"""
        query_params = parse_qs(urlparse(url).query)  # URL의 쿼리 파라미터를 딕셔너리로 변환
        return query_params.get("goodsNo", [None])[0]  # 'goodsNo' 값 반환 (없으면 None)


    def _api_reviews(self, goods_no, page_idx):
        """Olive Young 상품 리뷰를 가져오는 함수"""
        url = "https://www.oliveyoung.co.kr/store/goods/getGdasNewListJson.do"
        headers = {
            "authority": "www.oliveyoung.co.kr",
            "method": "GET",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }

        params = {
            "goodsNo": goods_no,
            "gdasSort": "05",
            "itemNo": "all_search",
            "pageIdx": str(page_idx),
            "colData": "",
            "keywordGdasSeqs": "",
            "type": "",
            "point": "",
            "hashTag": "",
            "optionValue": "",
            "cTypeLength": "0"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: 요청 실패")
            return None


    def _get_reviews(self, url):
        """상품 리뷰를 가져오는 함수 (모든 페이지 크롤링)"""
        goods_no = self._extract_goods_no(url)

        if not goods_no:
            self.log_signal.emit("Error: goodsNo를 찾을 수 없습니다.")
            return []

        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_name = f"올리브영_{goods_no}_{current_time}"

        reviews = []  # 모든 리뷰 데이터를 저장할 리스트
        page_idx = 1  # 페이지 인덱스를 1부터 시작

        while True:
            data = self._api_reviews(goods_no, page_idx)

            self.log_signal.emit(f"페이지 {page_idx}) : 요청시작")

            # 데이터가 빈 객체 `{}` 이면 중단
            if not data or data == {} or "gdasList" not in data or not data["gdasList"]:
                self.log_signal.emit(f"리뷰 요청 종료 (마지막 페이지: {page_idx})")
                break  # 반복 종료

            # 리뷰 데이터를 리스트에 추가
            reviews.extend(data["gdasList"])

            self.log_signal.emit(f"페이지 {page_idx}) : 데이터 수 {len(data["gdasList"])}")
            self.log_signal.emit(f"페이지 {page_idx}) : 요청성공")

            # 다음 페이지 요청을 위해 증가
            page_idx += 1

            time.sleep(random.uniform(2, 3))

        return reviews  # 모든 리뷰 반환


    def _setting_reviews(self, reviews):

        result_list = []

        """리뷰 리스트를 출력하는 함수"""
        if not reviews:
            print("리뷰 데이터가 없습니다.")
            return

        for idx, review in enumerate(reviews, start=1):
            add_info_list = []
            # 'addInfoNm'이 있고, 리스트 형태이면 'mrkNm' 값 최대 4개 추출
            if review.get("addInfoNm"):  # addInfoNm이 None이 아닌 경우만 실행
                add_info_list = [info["mrkNm"] for info in review["addInfoNm"] if isinstance(info, dict) and "mrkNm" in info][:4]
            # gdasSeq 값 (짝수) -> 평점 변환 (0~5 범위)
            score = min(5, max(0, review["gdasSeq"] // 2))
            review_content = review['gdasCont'].replace("<br/>", "\n")
            obj = {
                'URL': self.current_url,
                '리뷰 ID': review['gdasSeq'],
                '상품 번호': review['goodsNo'],
                '회원 닉네임': review['mbrNickNm'],
                '평점': score,  # 정수값 (0~5 범위)
                '리뷰 내용': review_content,
                '리뷰 등록 날짜': review['dispRegDate'],
                '추가정보': add_info_list  # 최대 4개 리스트
            }
            result_list.append(obj)

        return result_list


    def _save_to_excel(self, results):
        self.log_signal.emit("엑셀 저장 시작")

        try:
            # 파일 이름 끝에 "_엑셀.xlsx" 추가
            excel_file = f"{self.file_name}.xlsx"

            # DataFrame 생성 후 엑셀 저장
            df = pd.DataFrame(results)
            df.to_excel(excel_file, index=False, engine='openpyxl')  # encoding 제거

            self.log_signal.emit(f"엑셀 파일 저장 완료: {excel_file}")

        except Exception as e:
            self.log_signal.emit(f"엑셀 저장 실패: {e}")

    # [공통] 프로그램 중단
    def stop(self):
        self.running = False
