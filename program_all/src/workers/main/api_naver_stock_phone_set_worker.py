import time
import re
import requests
from bs4 import BeautifulSoup

from src.workers.api_base_worker import BaseApiWorker
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils


class ApiNaverStockPhoneSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()

        self.file_driver = None
        self.excel_driver = None

        self.running = True
        self.site_name = "naver_stock_phone"
        self.company_name = "naver_stock_phone"

        self.csv_filename = ""
        self.result_list = []

        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        # === 출력 컬럼 ===
        self.columns = [
            "기업명",
            "시장 구분",
            "종목코드",
            "대표전화",
            "IR전화",
            "홈페이지",
        ]

        # === 요청 헤더 ===
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "connection": "keep-alive",
            "referer": "https://navercomp.wisereport.co.kr/",
        }

    # =========================
    # 초기화
    # =========================
    def init(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        return True

    # =========================
    # 메인
    # =========================
    def main(self):
        try:
            self.log_signal.emit("네이버 기업 전화번호 수집 시작")

            self.total_cnt = len(self.excel_data_list)

            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.csv_filename, self.columns)

            self.call_company_list()

            # CSV → Excel
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)

            return True

        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

    # =========================
    # 기업 목록 처리
    # =========================
    def call_company_list(self):
        for idx, row in enumerate(self.excel_data_list, start=1):
            if not self.running:
                break

            self.current_cnt += 1

            company_nm = str(row.get("기업명", "")).strip()
            market_div = str(row.get("시장 구분", "")).strip()
            cmp_cd = str(row.get("종목코드", "")).strip()

            if not cmp_cd:
                self.log_signal_func(f"[스킵] 종목코드 없음: {company_nm}")
                continue

            contact = self.fetch_contact_info(cmp_cd)

            result = {
                "기업명": company_nm,
                "시장 구분": market_div,
                "종목코드": cmp_cd,
                "대표전화": contact.get("tel_main"),
                "IR전화": contact.get("tel_ir"),
                "홈페이지": contact.get("homepage"),
            }

            self.result_list.append(result)
            self.log_signal.emit(f"({idx}/{self.total_cnt}) {company_nm} 완료")

            if idx % 5 == 0:
                self.excel_driver.append_to_csv(
                    self.csv_filename, self.result_list, self.columns
                )
                self.result_list.clear()

            pro_value = (self.current_cnt / self.total_cnt) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value

            # time.sleep(0.5)

        if self.result_list:
            self.excel_driver.append_to_csv(
                self.csv_filename, self.result_list, self.columns
            )

    # =========================
    # WiseReport 파싱
    # =========================
    def fetch_contact_info(self, cmp_cd: str) -> dict:
        url = "https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx"
        params = {
            "cmp_cd": cmp_cd,
            "cn": ""
        }

        try:
            resp = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")

            homepage = None
            tel_main = None
            tel_ir = None

            # === 홈페이지 ===
            th_home = soup.find("th", string=lambda s: s and "홈페이지" in s)
            if th_home:
                td = th_home.find_next_sibling("td")
                if td:
                    a = td.find("a")
                    if a and a.get("href"):
                        homepage = a["href"].strip()

            # === 대표전화 / IR전화 ===
            th_tel = soup.find("th", string=lambda s: s and "대표전화" in s)
            if th_tel:
                td = th_tel.find_next_sibling("td")
                if td:
                    raw = td.get_text(strip=True)
                    phones = re.findall(r"\d{2,3}-\d{3,4}-\d{4}", raw)
                    if phones:
                        tel_main = phones[0]
                        if len(phones) > 1:
                            tel_ir = phones[1]

            return {
                "homepage": homepage,
                "tel_main": tel_main,
                "tel_ir": tel_ir,
            }

        except Exception as e:
            self.log_signal_func(f"[에러] {cmp_cd} 파싱 실패: {e}")
            return {
                "homepage": None,
                "tel_main": None,
                "tel_ir": None,
            }

    # =========================
    # 종료
    # =========================
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 작업 종료 ===============")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
