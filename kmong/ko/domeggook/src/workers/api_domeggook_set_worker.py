import os
import random
import re
import ssl
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.time_utils import get_today_date
from src.utils.utils_selenium import SeleniumDriverManager
import time
import math

ssl._create_default_https_context = ssl._create_unverified_context

# API
class ApiDomeggookSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    finally_finished_signal = pyqtSignal(str)
    msg_signal = pyqtSignal(str, str)

    # 초기화
    def __init__(self, id_list):
        super().__init__()
        self.baseUrl = "https://domeggook.com/"
        self.result_list = []
        self.before_pro_value = 0
        self.id_list = id_list  # URL을 클래스 속성으로 저장
        self.end_cnt = 0
        self.cookies = None
        self.access_token = None
        self.running = True  # 실행 상태 플래그 추가
        self.request_key = None
        self.driver = None
        self.all_end = 'N'
        self.now_result_list = []
        self.new_result_list = []
        self.old_result_list = []
        self.file_name = ""
        self.excel_file_name = ""
        self.db_folder = "DB"  # 파일이 위치한 DB 폴더
        self.driver = None
        self.driver_manager = None


        if len(self.id_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')

    # 실행
    def run(self):
        if len(self.id_list) > 0:
            self.driver_manager = SeleniumDriverManager(headless=True)
            self.driver = self.driver_manager.start_driver(self.baseUrl, 1200, False)

            for idx, id in enumerate(self.id_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                self.end_cnt = idx

                # 엑셀 파일 id로 읽어서 객체 리스트 old_result_list 담기
                old_result_list = []

                file_name = os.path.join(self.db_folder, f"{id}.csv")  # CSV 파일 경로
                excel_file_name = os.path.join(self.db_folder, f"{id}.xlsx")  # 동일한 이름의 엑셀 파일 경로

                self.file_name = file_name
                self.excel_file_name = excel_file_name

                # CSV 파일이 존재하면 읽어서 old_result_list에 저장 후 삭제
                if os.path.exists(file_name):
                    try:
                        # 파일 읽기
                        df = pd.read_csv(file_name, encoding='utf-8')
                        old_result_list = df.to_dict(orient='records')  # DataFrame을 리스트[dict] 형태로 변환

                        # CSV 파일 삭제
                        os.remove(file_name)
                        self.log_signal.emit(f"CSV 파일 삭제 완료: {file_name}")

                    except Exception as e:
                        self.log_signal.emit(f"CSV 파일 읽기 또는 삭제 중 오류 발생: {e}")

                # 동일한 이름의 엑셀 파일(.xlsx)도 삭제
                if os.path.exists(excel_file_name):
                    try:
                        os.remove(excel_file_name)
                        self.log_signal.emit(f"엑셀 파일 삭제 완료: {excel_file_name}")
                    except Exception as e:
                        self.log_signal.emit(f"엑셀 파일 삭제 중 오류 발생: {e}")


                # total_cnt, total_page = self.fetch_item_cnt(id)
                # self.log_signal.emit(f'전체 수 : {total_cnt}')
                # self.log_signal.emit(f'전체 페이지 : {total_page}')

                # all_item_set = self.fetch_item_list(id, total_page)
                # all_item_list = list(all_item_set)  # 다시 리스트로 변환
                # self.log_signal.emit(f'전체 리스트 수: {len(all_item_list)}')
                all_item_list = [
                                '48423911',
                                '53692016',
                                '46776955',
                                '46677077',
                                '50923002',
                                '53691791',
                                '46484774'
                                ]
                self.fetch_new_item_list(all_item_list, old_result_list)

                self._remain_data_set()

        self.log_signal.emit(f'크롤링 종료')


    def fetch_item_cnt(self, sw):
        url = f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg=1"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "domeggook.com",
            "referer": f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg=0",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        total_cnt = 0
        total_page = 0
        if response.status_code != 200:
            return total_cnt, total_page

        soup = BeautifulSoup(response.text, "html.parser")

        # div id="lCnt" 내부에서 숫자 찾기
        lcnt_div = soup.find("div", id="lCnt")

        if lcnt_div:
            b_tag = lcnt_div.find("b")  # <b> 태그 직접 찾기
            if b_tag:
                total_cnt = int(b_tag.text.replace(",", ""))  # 콤마 제거 후 정수 변환
                total_page = (total_cnt // 52) + (1 if total_cnt % 52 > 0 else 0)  # 페이지 계산

        return total_cnt, total_page


    def fetch_item_ids(self, sw, pg):
        url = f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg={pg}"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "domeggook.com",
            "referer": f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg={pg-1}",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.log_signal.emit("페이지를 불러오지 못했습니다.")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        item_list = []

        # ol 태그 내의 li 요소 찾기
        ol_tags = soup.find_all("ol", class_="lItemList")
        if ol_tags:
            last_ol_tag = ol_tags[-1]  # 마지막 ol 태그 선택
            li_tags = last_ol_tag.find_all("li", recursive=False)

            for li in li_tags:
                # li 내부의 a 태그 class="thumb" 찾기
                a_tag = li.find("a", class_="thumb")
                if a_tag and "href" in a_tag.attrs:
                    href = a_tag["href"]

                    # 정규식을 사용하여 숫자만 추출
                    match = re.search(r"/(\d+)", href)
                    if match:
                        item_list.append(match.group(1))

        return item_list


    def fetch_item_list(self, id, total_page):
        all_item_set = set()  # 기존 리스트를 집합(set)으로 변환
        for i in range(1, total_page + 1):
            if not self.running:  # 실행 상태 확인
                self.log_signal.emit("크롤링이 중지되었습니다.")
                break

            self.log_signal.emit(f'리스트 페이지 index {i}')
            item_list = self.fetch_item_ids(id, i)
            self.log_signal.emit(f'리스트 페이지 item_list : {item_list}')
            all_item_set.update(item_list)  # 중복을 방지하면서 추가
            time.sleep(random.uniform(2, 3))
        return all_item_set


    def safe_int(self,val):
        try:
            f = float(val)
            if math.isnan(f):
                return None
            return int(f)
        except (ValueError, TypeError):
            return None


    def fetch_new_item_list(self, all_item_list, old_result_list):
        now_result_list = []
        for idx, product_id in enumerate(all_item_list, start=1):

            if not self.running:  # 실행 상태 확인
                self.log_signal.emit("크롤링이 중지되었습니다.")
                break

            new_obj = self.fetch_product_details(product_id)
            self.log_signal.emit(f'상세보기 시작 index : {idx}, 상품정보 : {new_obj}')

            # old_result_list에서 같은 상품번호를 가진 객체 찾기
            old_obj = None
            target_no = self.safe_int(new_obj['상품번호'])

            for item in old_result_list:
                item_no = self.safe_int(item['상품번호'])

                if item_no == target_no:
                    old_obj = item
                    break

            if old_obj:

                # old_obj의 재고수량과 obj의 재고수량 차이 계산 (old_obj가 항상 크거나 같음)
                old_stock = int(old_obj['재고수량']) if old_obj['재고수량'] else 0
                current_stock = int(new_obj['재고수량']) if new_obj['재고수량'] else 0
                sales_volume = old_stock - current_stock  # 판매량 계산

                # old_obj에서 모든 '판매량(yyyy/mm/dd)' 컬럼을 찾아 new_obj에 복사
                all_sales_columns = self.get_all_sales_columns(old_obj)

                for col in all_sales_columns:
                    new_obj[col] = old_obj[col]  # 기존 판매량 데이터 유지

                # new_obj에 추가 정보 설정
                new_obj[f'판매량({get_today_date()})'] = sales_volume

                # new_result_list에 추가
                now_result_list.append(new_obj)

            else:
                # new_obj에 추가 정보 설정
                new_obj[f'판매량({get_today_date()})'] = -1

                # new_result_list에 추가
                now_result_list.append(new_obj)

            self.log_signal.emit(f'상세보기 끝 index : {idx}, 상품정보 : {new_obj}')

            # 100개의 항목마다 임시로 엑셀 저장
            if idx % 10 == 0 and now_result_list:
                self._save_to_csv_append(now_result_list)  # 임시 엑셀 저장 호출
                self.log_signal.emit(f"엑셀 {idx}개 까지 임시저장")
                now_result_list = []  # 저장 후 초기화

            pro_value = (idx / len(all_item_list)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

            time.sleep(random.uniform(2, 3))

        if now_result_list:
            self._save_to_csv_append(now_result_list)


    def fetch_product_details_api(self, product_id):
        base_url = "https://domeggook.com/"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "domeggook.com",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

        url = f"{base_url}{product_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.log_signal.emit(f"❌ {product_id} 페이지를 불러오지 못했습니다.")

        soup = BeautifulSoup(response.text, "html.parser")

        product_data = {
            'URL': url,
            '판매자명': '',
            '상품번호': '',
            '재고수량': 0,
        }

        # ✅ 판매자명 추출
        seller_tag = soup.find("button", id="lBtnShowSellerInfo")
        if seller_tag:
            seller_name = seller_tag.find("b").text.strip()
            product_data["판매자명"] = seller_name
        else:
            product_data["판매자명"] = ""

        # ✅ 상품번호 추출
        product_num_tag = soup.find("div", id="lInfoHeader")
        if product_num_tag:
            match = re.search(r"상품번호\s*:\s*(\d+)", product_num_tag.text)
            if match:
                product_data["상품번호"] = match.group(1)
            else:
                product_data["상품번호"] = ""
        else:
            product_data["상품번호"] = ""

        # ✅ 상품명 추출
        product_name_tag = soup.find("h1", id="lInfoItemTitle")
        product_data["상품명"] = product_name_tag.text.strip() if product_name_tag else ""

        # ✅ 재고수량 추출
        stock_row = soup.find("tr", class_="lInfoQty")  # 먼저 <tr class="lInfoQty"> 찾기
        if stock_row:
            stock_tag = stock_row.find("td", class_="lInfoItemContent")  # 그 안에서 <td class="lInfoItemContent"> 찾기
            if stock_tag:
                match = re.search(r"([\d,]+)", stock_tag.text)
                if match:
                    product_data["재고수량"] = int(match.group(1).replace(",", ""))
                else:
                    product_data["재고수량"] = 0
            else:
                product_data["재고수량"] = 0
        else:
            product_data["재고수량"] = 0



        return product_data


    def fetch_product_details(self, product_id):
        url = f"https://domeggook.com/{product_id}"
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 10)  # 최대 10초 대기
        time.sleep(2)

        product_data = {
            'URL': url,
            '판매자명': '',
            '상품번호': '',
            '상품명': '',
            '재고수량': 0,
        }

        # ✅ 판매자명 추출
        try:
            seller_button = wait.until(EC.presence_of_element_located((By.ID, "lBtnShowSellerInfo")))
            seller_name = seller_button.find_element(By.TAG_NAME, "b").text.strip()
            product_data["판매자명"] = seller_name
        except Exception:
            self.log_signal.emit(f"⚠️ 판매자명 정보를 찾을 수 없습니다.")

        # ✅ 상품번호 추출
        try:
            info_header = wait.until(EC.presence_of_element_located((By.ID, "lInfoHeader")))
            match = re.search(r"상품번호\s*:\s*(\d+)", info_header.text)
            if match:
                product_data["상품번호"] = match.group(1)
        except Exception:
            self.log_signal.emit(f"⚠️ 상품번호 정보를 찾을 수 없습니다.")

        # ✅ 상품명 추출
        try:
            product_name_tag = wait.until(EC.presence_of_element_located((By.ID, "lInfoItemTitle")))
            product_data["상품명"] = product_name_tag.text.strip()
        except Exception:
            self.log_signal.emit(f"⚠️ 상품명을 찾을 수 없습니다.")

        # ✅ 재고수량 추출
        try:
            stock_tr = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.lInfoQty")))
            stock_td = stock_tr.find_element(By.CLASS_NAME, "lInfoItemContent")
            match = re.search(r"([\d,]+)", stock_td.text)
            if match:
                product_data["재고수량"] = int(match.group(1).replace(",", ""))
        except Exception:
            self.log_signal.emit(f"⚠️ 재고수량 정보를 찾을 수 없습니다.")

        return product_data


    def get_all_sales_columns(self, old_obj):
        """ old_obj에서 모든 '판매량(yyyy/mm/dd)' 컬럼을 찾아 정렬 후 반환 """
        sales_pattern = re.compile(r"판매량\(\d{4}/\d{2}/\d{2}\)")  # 날짜 패턴
        sales_columns = [col for col in old_obj.keys() if sales_pattern.match(col)]

        # 날짜 기준으로 정렬 (오름차순)
        sales_columns.sort(key=lambda x: x[-10:])  # "판매량(yyyy/mm/dd)"에서 날짜 부분만 비교
        return sales_columns


    def _remain_data_set(self):

        # CSV 파일을 엑셀 파일로 변환
        try:
            excel_file_name = self.file_name.replace('.csv', '.xlsx')  # 엑셀 파일 이름으로 변경
            self.log_signal.emit(f"CSV 파일을 엑셀 파일로 변환 시작: {self.file_name} → {excel_file_name}")
            df = pd.read_csv(self.file_name)  # CSV 파일 읽기
            df.to_excel(excel_file_name, index=False)  # 엑셀 파일로 저장

            # 마지막 세팅
            pro_value = 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)

            self.log_signal.emit(f"엑셀 파일 변환 완료: {excel_file_name}")

            self.log_signal.emit(f'종료 수 : {self.end_cnt}')

            if self.end_cnt == len(self.id_list):
                self.progress_end_signal.emit()
            else:
                self.log_signal.emit(f'다음 작업 준비중입니다. 잠시만 기다려주세요...')

        except Exception as e:
            self.log_signal.emit(f"엑셀 파일 변환 실패: {e}")

    # [공통] csv 데이터 추가
    def _save_to_csv_append(self, results):
        self.log_signal.emit("CSV 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(self.file_name):
                # 파일이 없으면 새로 생성 및 저장
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, index=False, encoding='utf-8-sig')

                self.log_signal.emit(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                # 파일이 있으면 append 모드로 데이터 추가
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
                self.log_signal.emit(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.emit(f"CSV 저장 실패: {e}")

    # [공통] 프로그램 중단
    def stop(self):
        self.running = False
