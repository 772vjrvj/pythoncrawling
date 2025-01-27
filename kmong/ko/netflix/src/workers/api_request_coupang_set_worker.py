import os
import random
import re
import ssl
import time
import pandas as pd
import requests
from datetime import datetime
from urllib.parse import urlparse
from PyQt5.QtCore import QThread, pyqtSignal

ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiRequestCoupangSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    def __init__(self, url_list):
        super().__init__()
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.director = ''
        self.title = ''
        self.before_pro_value = 0
        self.running = True  # 실행 상태 플래그 추가

        # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        self.file_name = f"쿠팡_{current_time}.xlsx"

        if len(self.url_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')


    def run(self):
        if len(self.url_list) > 0:
            self.log_signal.emit("크롤링 시작")
            result_list = []
            for idx, url in enumerate(self.url_list, start=1):

                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                # 100개의 항목마다 임시로 엑셀 저장
                if (idx - 1) % 10 == 0 and result_list:
                    self._save_to_csv_append(result_list)  # 임시 엑셀 저장 호출
                    self.log_signal.emit(f"엑셀 {idx - 1}개 까지 임시저장")
                    result_list = []  # 저장 후 초기화

                result = {
                    "url": url,
                    "title": "",
                    "episode_synopsis": "",
                    "episode_title": "",
                    "episode_seq": "",
                    "episode_season": "",
                    "year": "",
                    "season": "",
                    "rating": "",
                    "genre": "",
                    "summary": "",
                    "cast": "",
                    "director": "",
                    "success": "X",
                    "message": "",
                    "error": "X"
                }

                self.log_signal.emit(f'번호 : {idx}, 시작')
                self._fetch_place_info(url, result)
                self._error_chk(result)
                self.log_signal.emit(f'번호 : {idx}, 데이터 : {result}')

                pro_value = (idx / len(self.url_list)) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                result_list.append(result)
                time.sleep(random.uniform(0.5, 1))

            # 남은 데이터 저장
            if result_list:
                self._save_to_csv_append(result_list)

            # CSV 파일을 엑셀 파일로 변환
            try:
                csv_file_name = self.file_name  # 기존 CSV 파일 이름
                excel_file_name = csv_file_name.replace('.csv', '.xlsx')  # 엑셀 파일 이름으로 변경

                self.log_signal.emit(f"CSV 파일을 엑셀 파일로 변환 시작: {csv_file_name} → {excel_file_name}")
                df = pd.read_csv(csv_file_name)  # CSV 파일 읽기
                df.to_excel(excel_file_name, index=False)  # 엑셀 파일로 저장

                # 마지막 세팅
                pro_value = 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)


                self.log_signal.emit(f"엑셀 파일 변환 완료: {excel_file_name}")
                self.progress_end_signal.emit()

            except Exception as e:
                self.log_signal.emit(f"엑셀 파일 변환 실패: {e}")

        else:
            self.log_signal.emit("url를 입력하세요.")


    def _error_chk(self, result):
        if result['error'] == 'Y':
            self.log_signal.emit(result['message'])
            return True
        return False

    def _save_to_csv_append(self, results):
        self.log_signal.emit("CSV 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(self.file_name):
                # 파일이 없으면 새로 생성 및 저장
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, index=False)
                self.log_signal.emit(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                # 파일이 있으면 append 모드로 데이터 추가
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, mode='a', header=False, index=False)
                self.log_signal.emit(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.emit(f"CSV 저장 실패: {e}")

    def _extract_id_from_url(self, url):
        # URL을 파싱
        parsed_url = urlparse(url)

        # path에서 play/ 또는 titles/ 다음에 오는 값을 정규식으로 추출
        match = re.search(r'/(play|titles)/([^/]+)', parsed_url.path)

        # 값 반환 (없으면 None)
        return match.group(2) if match else None

    def _fetch_place_info(self, main_url, result):
        base_url = "https://discover.coupangstreaming.com/v1/discover/titles/"
        uuid = self._extract_id_from_url(main_url)
        url = f"{base_url}{uuid}"
        headers = {}

        max_retries = 3  # 최대 재시도 횟수

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                if data.get("error"):
                    result['error'] = 'Y'
                    result['message'] = f"{data['error'].get('status', '')} {data['error'].get('name', '')}"
                    break
                self.director = ''
                self.title = ''
                self._fetch_director_title(data, base_url, headers)
                self._extract_data(data, result, main_url)
                break

            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    result['error'] = 'Y'
                    result['message'] = f"서버 호출 에러, 최대 재시도 횟수를 초과했습니다.: {e}"
                    break
                time.sleep(1)

    def _fetch_director_title(self, data, base_url, headers):
        parent_id = data["data"].get("parent_id")
        if parent_id:
            parent_url = f"{base_url}{parent_id}"
            parent_res = requests.get(parent_url, headers=headers)
            parent_res.raise_for_status()
            parent_data = parent_res.json()
            self.director = ", ".join(
                person["name"] for person in parent_data["data"].get("people", []) if person["role"] == "DIRECTOR"
            )
            self.title = parent_data["data"].get("title", "")


    def _extract_data(self, data, result, main_url):
        result.update({
            "url": main_url,
            "title": self.title or data["data"].get("title", ""),
            "episode_synopsis": data["data"].get("description", "")  if self.title else '',
            "episode_title": data["data"].get("title", "") if self.title else '',
            "episode_seq": str(data["data"].get("episode", "")) if self.title else '',
            "episode_season": str(data["data"].get("season", "")) if self.title else '',
            "year": str(data["data"].get("meta", {}).get("releaseYear", "")),
            "season": str(data["data"].get("season", "")) or str(data["data"].get("seasons", "")),
            "rating": data["data"].get("rating", {}).get("age", ""),
            "genre": ", ".join(
                tag["label"] for tag in data["data"].get("tags", []) if tag.get("meta", {}).get("genre")
            ),
            "summary": data["data"].get("short_description", "") if self.title else data["data"].get("description", ""),
            "cast": ", ".join(
                person["name"] for person in data["data"].get("people", []) if person["role"] == "CAST"
            ),
            "director": self.director or ", ".join(
                person["name"] for person in data["data"].get("people", []) if person["role"] == "DIRECTOR"
            ),


            "success": "O",
            "message": "데이터 추출 성공",
            "error": "X"
        })

    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False
