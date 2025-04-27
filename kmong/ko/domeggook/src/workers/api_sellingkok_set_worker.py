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
import time
import shutil

from src.utils.time_utils import get_today_date
import math

from src.utils.utils_selenium import SeleniumDriverManager

ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiSellingkokSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    finally_finished_signal = pyqtSignal(str)
    msg_signal = pyqtSignal(str, str)

    # 초기화
    def __init__(self, id_list):
        super().__init__()
        self.baseUrl = "https://sellingkok.com/"
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

                # 파일 경로 설정
                file_name = os.path.join(self.db_folder, f"{id}.csv")
                excel_file_name = os.path.join(self.db_folder, f"{id}.xlsx")

                self.file_name = file_name
                self.excel_file_name = excel_file_name

                old_result_list = []

                # 백업 폴더 준비
                backup_dir = "DB_BAK"
                os.makedirs(backup_dir, exist_ok=True)

                # CSV 파일 백업 및 삭제
                if os.path.exists(file_name):
                    try:
                        df = pd.read_csv(file_name, encoding='utf-8')
                        old_result_list = df.to_dict(orient='records')

                        backup_file_path = os.path.join(backup_dir, os.path.basename(file_name))
                        shutil.copy2(file_name, backup_file_path)
                        self.log_signal.emit(f"CSV 파일 백업 완료: {backup_file_path}")

                        os.remove(file_name)
                        self.log_signal.emit(f"CSV 파일 삭제 완료: {file_name}")

                    except Exception as e:
                        self.log_signal.emit(f"CSV 파일 읽기 또는 백업/삭제 중 오류 발생: {e}")

                # XLSX 파일 백업 및 삭제
                if os.path.exists(excel_file_name):
                    try:
                        backup_excel_path = os.path.join(backup_dir, os.path.basename(excel_file_name))
                        shutil.copy2(excel_file_name, backup_excel_path)
                        self.log_signal.emit(f"엑셀 파일 백업 완료: {backup_excel_path}")

                        os.remove(excel_file_name)
                        self.log_signal.emit(f"엑셀 파일 삭제 완료: {excel_file_name}")

                    except Exception as e:
                        self.log_signal.emit(f"엑셀 파일 백업/삭제 중 오류 발생: {e}")

                # 크롤링 시작
                total_cnt, total_page = self.fetch_item_cnt(id)
                self.log_signal.emit(f'전체 수 : {total_cnt}')
                self.log_signal.emit(f'전체 페이지 : {total_page}')

                all_item_set = self.fetch_item_list(id, total_page)
                all_item_list = list(all_item_set)
                self.log_signal.emit(f'전체 리스트 수: {len(all_item_list)}')

                self.fetch_new_item_list(all_item_list, old_result_list, id)

                self._remain_data_set()

        self.log_signal.emit('크롤링 종료')


    def fetch_item_cnt(self, sw):
        url = f"https://www.sellingkok.com/shop/search.php?&pt_it_cd={sw}&page=1"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.sellingkok.com",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        total_cnt = 0
        total_page = 0
        if response.status_code != 200:
            return total_cnt, total_page

        soup = BeautifulSoup(response.text, "html.parser")

        # class="at-content" 내부의 모든 aside 찾기
        at_content = soup.find("div", class_="at-content")
        if at_content:
            asides = at_content.find_all("aside")
            for aside in asides:
                divs = aside.find_all("div")
                for div in divs:
                    if "검색 결과 상품수 :" in div.get_text():
                        text = div.get_text()
                        match = re.search(r'(\d+)', text)
                        if match:
                            total_cnt = int(match.group(1))
                            total_page = (total_cnt // 30) + (1 if total_cnt % 30 > 0 else 0)
                        return total_cnt, total_page  # 찾으면 바로 return

        return total_cnt, total_page  # 못 찾으면 0, 0 반환


    def fetch_item_ids(self, sw, pg):
        url = f"https://www.sellingkok.com/shop/search.php?&pt_it_cd={sw}&page={pg}"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive",
            "host": "www.sellingkok.com",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.log_signal.emit("페이지를 불러오지 못했습니다.")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        item_list = []

        # form id="frmlist" 찾기
        form = soup.find("form", id="frmlist")
        if not form:
            return item_list

        # form 안의 div class="item-row" 모두 찾기
        item_rows = form.find_all("div", class_="item-row")

        for item in item_rows:
            checkbox = item.find("input", {"type": "checkbox", "class": "chk list_chk"})
            if checkbox and checkbox.has_attr("value"):
                item_list.append(checkbox["value"])

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


    def fetch_new_item_list(self, new_item_list, old_result_list, seller_name):
        now_result_list = []
        for idx, product_id in enumerate(new_item_list, start=1):

            if not self.running:  # 실행 상태 확인
                self.log_signal.emit("크롤링이 중지되었습니다.")
                break

            new_obj = self.fetch_product_details(product_id, seller_name)
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

                # 새로운 날짜의 판매량 추가
                new_sales_col = f'판매량({get_today_date()})'
                new_obj[new_sales_col] = sales_volume

                # new_obj에 추가 정보 설정
                new_obj[f'판매량({get_today_date()})'] = sales_volume

                # new_result_list에 추가
                now_result_list.append(new_obj)

            else:
                # new_obj에 추가 정보 설정
                new_obj[f'판매량({get_today_date()})'] = -1111111111

                # new_result_list에 추가
                now_result_list.append(new_obj)

            self.log_signal.emit(f'상세보기 끝 index : {idx}, 상품정보 : {new_obj}')

            # 100개의 항목마다 임시로 엑셀 저장
            if idx % 10 == 0 and now_result_list:
                self._save_to_csv_append(now_result_list)  # 임시 엑셀 저장 호출
                self.log_signal.emit(f"엑셀 {idx}개 까지 임시저장")
                now_result_list = []  # 저장 후 초기화

            pro_value = (idx / len(new_item_list)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

            time.sleep(random.uniform(2, 3))

        # now_result_list에 없는 old 데이터 찾아서 처리
        existing_product_nos = {self.safe_int(obj['상품번호']) for obj in now_result_list}

        for old_obj in old_result_list:
            old_no = self.safe_int(old_obj['상품번호'])

            if old_no not in existing_product_nos:
                # 오늘 날짜 판매량을 -999로 설정
                missing_sales_col = f'판매량({get_today_date()})'
                old_obj[missing_sales_col] = -9999999999

                # now_result_list에 추가
                now_result_list.append(old_obj)

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


    def fetch_product_details(self, product_id, seller_name):
        url = f"https://www.sellingkok.com/shop/item.php?it_id={product_id}"
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 10)  # 최대 10초 대기
        time.sleep(2)

        product_data = {
            'URL': url,
            '판매자명': seller_name,
            '상품번호': product_id,
            '상품명': '',
            '재고수량': 0,
        }

        # ✅ 상품명 추출
        try:
            # div class="at-body" 찾기
            at_body = self.driver.find_element(By.CLASS_NAME, "at-body")

            # 그 안에 h1 태그 찾기
            h1_tag = at_body.find_element(By.TAG_NAME, "h1")

            # h1 텍스트 가져오기
            product_data["상품명"] = h1_tag.text.strip()
        except Exception:
            self.log_signal.emit(f"⚠️ 상품명을 찾을 수 없습니다.")


        stock_qty = 0  # 결과 저장용

        try:
            # div.sell_info 여러 개 찾기
            sell_infos = self.driver.find_elements(By.CLASS_NAME, "sell_info")

            for sell_info in sell_infos:
                # 각 sell_info 안의 li 모두 찾기
                lis = sell_info.find_elements(By.TAG_NAME, "li")
                for li in lis:
                    spans = li.find_elements(By.TAG_NAME, "span")
                    if len(spans) >= 2:
                        label = spans[0].text.strip()
                        value = spans[1].text.strip()

                        if label == "재고수량":
                            # "4,995개" 같은 텍스트에서 콤마 제거하고 숫자만 추출
                            value_clean = value.replace(',', '')  # 콤마 제거
                            match = re.search(r'\d+', value_clean)
                            if match:
                                stock_qty = int(match.group())
                            break  # 찾으면 루프 종료
                if stock_qty > 0:
                    break  # 이미 찾았으면 더 이상 탐색할 필요 없음

            product_data["재고수량"] = stock_qty
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


    def _remain_data_set_text(self):

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


    def _remain_data_set(self):
        try:
            excel_file_name = self.file_name.replace('.csv', '.xlsx')  # 엑셀 파일 이름으로 변경
            self.log_signal.emit(f"CSV 파일을 엑셀 파일로 변환 시작: {self.file_name} → {excel_file_name}")

            # CSV 파일 읽기
            df = pd.read_csv(self.file_name)

            # 변환할 컬럼 찾기: '재고수량', '상품번호', '판매량'이 들어간 컬럼
            int_columns = [col for col in df.columns if '재고수량' in col or '상품번호' in col or '판매량' in col]

            # 해당 컬럼들 int로 변환 (오류 있으면 NaN -> 0 처리)
            for col in int_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 엑셀 파일로 저장
            df.to_excel(excel_file_name, index=False)

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
            # 기본 컬럼 정의
            required_columns = ['URL', '판매자명', '상품번호', '상품명', '재고수량']

            # 판매량 관련 추가 컬럼 찾기
            sales_columns = set()
            for r in results:
                for k in r.keys():
                    if k.startswith('판매량('):
                        sales_columns.add(k)

            all_columns = required_columns + sorted(sales_columns)

            # uniform한 형태로 변환 (없으면 0, 값이 None이나 ''이어도 0으로 변환)
            uniform_results = []
            for r in results:
                uniform_r = {}
                for col in all_columns:
                    value = r.get(col, 0)
                    uniform_r[col] = value if value not in (None, '') else 0
                uniform_results.append(uniform_r)

            df = pd.DataFrame(uniform_results)

            # 저장
            if not os.path.exists(self.file_name):
                df.to_csv(self.file_name, index=False, encoding='utf-8-sig')
                self.log_signal.emit(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                df.to_csv(self.file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
                self.log_signal.emit(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            self.log_signal.emit(f"CSV 저장 실패: {e}")

    # [공통] 프로그램 중단
    def stop(self):
        self.running = False
