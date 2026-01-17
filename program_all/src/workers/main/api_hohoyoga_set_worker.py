import re
import time
import random
import urllib.parse
import pandas as pd

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.api_utils import APIClient
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
from pathlib import Path

class ApiHohoyogaSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()

        # === 신규 === 페이지 범위
        self.start_page = None
        self.end_page = None

        self.local_name = None
        self.local_code = None

        self.site_name = "hohoyoga_seoul_"
        self.running = True

        self.total_pages = 0
        self.current_page = 0
        self.before_pro_value = 0

        self.login_id = ""
        self.login_pw = ""

        self.driver = None
        self.file_driver = None
        self.excel_driver = None
        self.selenium_driver = None

        self.notice_list = []
        self.seen_srls = set()

        self.excel_filename = None

        self.api_client = APIClient(use_cache=False)

        self.login_url = "https://www.hohoyoga.com/index.php?mid=job_pilates_seoul&act=dispMemberLoginForm"
        self.list_url = "https://www.hohoyoga.com/index.php"
        self.mid = "job_pilates_seoul"

    # =========================
    # === 신규 === 유틸
    # =========================
    def _to_int(self, v, default=None):
        try:
            if v is None:
                return default
            s = str(v).strip()
            if s == "":
                return default
            return int(s)
        except Exception:
            return default

    def _build_qs_url(self, base, params):
        try:
            return base + "?" + urllib.parse.urlencode(params, doseq=True)
        except Exception:
            return base

    def _base_headers(self):
        # NOTE:
        # - ':authority', ':method', ':path', ':scheme' 같은 HTTP/2 pseudo header는 requests에서 못 씀
        # - Accept-Encoding은 일단 빼서(=requests 기본) 안정화 추천
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Sec-CH-UA": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

    def _list_params(self, page):
        return {
            "mid": self.mid,
            "page": str(page),
        }

    def _detail_params(self, page, srl):
        return {
            "mid": self.mid,
            "page": str(page),
            "document_srl": str(srl),
        }

    def _list_headers(self, page):
        h = self._base_headers()
        h["Referer"] = self._build_qs_url(self.list_url, self._list_params(page))
        return h

    def _detail_headers(self, page, srl):
        h = self._base_headers()
        # 상세도 referer는 “해당 목록 page”가 맞음
        h["Referer"] = self._build_qs_url(self.list_url, self._list_params(page))
        return h

    def _debug_html_hint(self, html):
        try:
            soup = BeautifulSoup(html, "html.parser")
            title = (soup.title.get_text(strip=True) if soup.title else "")
            has_uid = bool(soup.select_one("#uid"))
            has_upw = bool(soup.select_one("#upw"))
            return f"title={title}, has_uid={has_uid}, has_upw={has_upw}"
        except Exception:
            return "hint_parse_fail"

    # =========================
    # init / main
    # =========================
    def init(self):
        try:
            self.driver_set(False)

            self.login_id = self.get_setting_value(self.setting, "id")
            self.login_pw = self.get_setting_value(self.setting, "password")

            # === 신규 === 페이지 범위 파라미터 (default: 1 ~ 끝까지)
            raw_start = self.get_setting_value(self.setting, "start_page")
            raw_end = self.get_setting_value(self.setting, "end_page")

            self.start_page = self._to_int(raw_start, default=1)
            self.end_page = self._to_int(raw_end, default=None)

            if self.start_page is None or self.start_page < 1:
                self.start_page = 1
            if self.end_page is not None and self.end_page < 1:
                self.end_page = None

            self.local_name = self.get_setting_value(self.setting, "local_name")
            self.local_code = self.get_setting_value(self.setting, "local_code")
            self.mid = self.local_code
            self.log_signal_func(
                f"📄 페이지 범위 설정: start={self.start_page}, end={self.end_page or '∞'}"
            )

            return True

        except Exception as e:
            self.log_signal_func(f"초기화 처리중 오류 발생: {e}")
            return False

    def main(self):
        try:
            if not self.login():
                return False

            self.set_cookies()

            self.excel_filename = self.file_driver.get_csv_filename(self.site_name)
            self.excel_driver.init_csv(self.excel_filename, self.columns)

            self.crawl_pages_and_save()

            # CSV -> XLSX (원본)
            self.excel_driver.convert_csv_to_excel_and_delete(self.excel_filename)

            # =========================
            # === 신규 === 중복 제거본 XLSX 추가 생성
            # =========================
            origin_xlsx = self.excel_filename.replace(".csv", ".xlsx")
            dedup_xlsx = origin_xlsx.replace(".xlsx", "_dedup.xlsx")
            self._remove_duplicate_by_contact(
                input_filename=origin_xlsx,
                output_filename=dedup_xlsx,
                contact_col="연락처"
            )

            return True

        except Exception as e:
            self.log_signal_func(f"메인 처리중 오류 발생: {e}")
            return False

    # =========================
    # login / cookies
    # =========================
    def login(self):
        try:
            self.driver.get(self.login_url)
            time.sleep(2)
            self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")

            id_input = self.selenium_driver.wait_element(By.ID, "uid", timeout=5)
            id_input.clear()
            id_input.send_keys(self.login_id)
            time.sleep(0.5)

            pw_input = self.selenium_driver.wait_element(By.ID, "upw", timeout=5)
            pw_input.clear()
            pw_input.send_keys(self.login_pw)
            time.sleep(0.5)

            login_btn = self.selenium_driver.wait_element(By.CSS_SELECTOR, "input.xet_btn", timeout=5)
            login_btn.click()
            time.sleep(1.0)
            return True

        except Exception as e:
            self.log_signal_func(f"로그인 처리중 오류 발생: {e}")
            return False

    def set_cookies(self):
        self.log_signal_func("📢 쿠키 세팅 시작")
        cookies = {c["name"]: c["value"] for c in self.driver.get_cookies()}
        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)
        self.log_signal_func("📢 쿠키 세팅 완료")
        time.sleep(0.5)

    # =========================
    # crawl
    # =========================
    def crawl_pages_and_save(self):
        page = self.start_page or 1

        # === 신규 === srls 0 연속 카운터
        zero_srl_streak = 0

        while True:
            if not self.running:
                self.log_signal_func("⛔ 사용자 중단")
                break

            # === 신규 === end_page 체크
            if self.end_page is not None and page > self.end_page:
                self.log_signal_func("🛑 end_page 도달 → 크롤링 종료")
                break

            self.log_signal_func(f"📄 페이지 조회 시작: page={page}")

            srls, dup_found = self._fetch_srls_of_page(page)

            # === 신규 === srls=0 연속 10회면 중지
            if not srls:
                zero_srl_streak += 1
                self.log_signal_func(f"⚠️ page={page} srls=0 (streak={zero_srl_streak}/10)")
                if zero_srl_streak >= 10:
                    self.log_signal_func("🛑 srls=0 이 10번 연속 발생 → 크롤링 종료")
                    break
            else:
                zero_srl_streak = 0

            self.log_signal_func(
                f"📦 page={page} 수집된 srl 수: {len(srls)}, dup_found={dup_found}"
            )

            if dup_found:
                self.log_signal_func("🛑 중복 srl 발견 → 크롤링 종료")
                break

            results = []
            for srl in srls:
                if not self.running:
                    break

                self.log_signal_func(f"🔎 상세 조회 시작: srl={srl}")

                item = self._fetch_detail(page, srl, max_retry=3)

                if item:
                    results.append(item)
                    self.log_signal_func(f"✅ 상세 성공: srl={srl}")
                else:
                    self.log_signal_func(f"❌ 상세 실패: srl={srl}")

                # === 신규 === 과도한 연타 방지
                time.sleep(0.2 + random.random() * 0.4)

            if results:
                self.log_signal_func(f"💾 CSV 저장: page={page}, rows={len(results)}")
                self.excel_driver.append_to_csv(self.excel_filename, results, self.columns)

            page += 1
            time.sleep(0.5)


    def _fetch_srls_of_page(self, page):
        headers = self._list_headers(page)
        params = self._list_params(page)

        html = self.api_client.get(self.list_url, headers=headers, params=params)

        self.log_signal_func(
            f"[LIST] page={page} html_type={type(html)}, length={len(html) if isinstance(html, str) else 'N/A'}"
        )

        if not isinstance(html, str) or not html:
            self.log_signal_func("⚠️ LIST HTML 비어있음")
            return [], False

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.bd_lst")

        if not table:
            hint = self._debug_html_hint(html)
            self.log_signal_func(f"⚠️ table.bd_lst 없음 (page={page}) ({hint})")
            return [], False

        srls = []
        dup_found = False

        for tr in table.select("tr"):
            st = tr.select_one("td.m_no span")
            if not st:
                continue

            # 진행중 텍스트 변형 대비 (진행 중, 진행중 등)
            status = st.get_text(strip=True).replace(" ", "")
            if "진행중" not in status and "진행" not in status:
                continue

            a = tr.select_one("td.title a[href*='document_srl=']")
            if not a:
                continue

            srl = self._extract_srl(a.get("href", ""))
            if not srl:
                continue

            if srl in self.seen_srls:
                dup_found = True
                self.log_signal_func(f"🔁 중복 발견 srl={srl}")
                break

            self.seen_srls.add(srl)
            srls.append(srl)

        return srls, dup_found

    def _fetch_detail(self, page, srl, max_retry=3):
        headers = self._detail_headers(page, srl)
        params = self._detail_params(page, srl)

        for attempt in range(1, max_retry + 1):
            html = self.api_client.get(self.list_url, headers=headers, params=params)

            self.log_signal_func(
                f"[DETAIL] srl={srl} attempt={attempt} html_type={type(html)}, length={len(html) if isinstance(html, str) else 'N/A'}"
            )

            if not isinstance(html, str) or not html:
                time.sleep(0.5 * attempt)
                continue

            soup = BeautifulSoup(html, "html.parser")
            table = soup.select_one("table.et_vars")

            if not table:
                hint = self._debug_html_hint(html)
                self.log_signal_func(f"⚠️ et_vars 테이블 없음: srl={srl} ({hint})")

                # 세션/차단성 실패 → backoff 후 재시도
                time.sleep((0.7 + random.random() * 0.6) * attempt)
                continue

            row = {col: "" for col in self.columns}

            for tr in table.select("tr"):
                th = tr.select_one("th")
                td = tr.select_one("td")
                if not th or not td:
                    continue

                key = th.get_text(strip=True)
                val = td.get_text(" ", strip=True)

                if key in row:
                    row[key] = val

            self.log_signal_func(f"[DETAIL] srl={srl} keys={row}")
            return row

        return None

    # =========================
    # parse helpers
    # =========================
    def _extract_srl(self, href):
        try:
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            if "document_srl" in qs and qs["document_srl"]:
                return str(qs["document_srl"][0]).strip()
        except Exception:
            pass

        m = re.search(r"document_srl=(\d+)", href)
        return m.group(1) if m else ""

    # =========================
    # === 신규 === 최종 엑셀 중복 제거 (pandas)
    # =========================
    def _remove_duplicate_by_contact(
            self,
            input_filename: str,
            output_filename: str,
            contact_col: str = "연락처"
    ):


        base_dir = Path.cwd()

        input_path = base_dir / input_filename
        output_path = base_dir / output_filename

        if not input_path.exists():
            self.log_signal_func(f"❌ 중복제거 실패: 엑셀 파일이 없습니다: {input_path}")
            return

        # 엑셀 읽기
        df = pd.read_excel(input_path)

        if contact_col not in df.columns:
            self.log_signal_func(f"❌ 중복제거 실패: '{contact_col}' 컬럼이 존재하지 않습니다")
            return

        before = len(df)

        # === 핵심 === 연락처 기준 중복 제거 (첫 번째 row 유지)
        dedup_df = df.drop_duplicates(
            subset=[contact_col],
            keep="first"
        )

        after = len(dedup_df)

        # 엑셀로 저장
        dedup_df.to_excel(output_path, index=False)

        self.log_signal_func("처리 완료")
        self.log_signal_func(f"- 원본 행 수: {before}")
        self.log_signal_func(f"- 중복 제거 후 행 수: {after}")
        self.log_signal_func(f"- 저장 경로: {output_path}")

    # -------------------------
    # 드라이버 세팅
    # -------------------------
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)

        # 드라이버 세팅
        self.driver = self.selenium_driver.start_driver(1200)

    # -------------------------
    # 마무리
    # -------------------------
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # -------------------------
    # 프로그램 중단
    # -------------------------
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
