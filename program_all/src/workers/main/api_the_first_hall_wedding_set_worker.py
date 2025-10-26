import os
import ssl
import time
import re
import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup

from src.utils.BeautifulSoup_utils import bs_txt

from src.utils.number_utils import calculate_divmod, divide_and_truncate_per
from src.utils.selenium_utils import SeleniumUtils
from src.utils.str_utils import get_query_params, str_norm
from src.workers.api_base_worker import BaseApiWorker
from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from urllib.parse import urlparse, parse_qs, urljoin



# API
class ApiThefirsthallweddingDetailSetLoadWorker(BaseApiWorker):


    def __init__(self):
        super().__init__()
        self.file_driver = None
        self.excel_driver = None
        self.url_obj_list = []
        self.site_url = "https://www.thewedd.com"
        self.site_review_url = "https://www.thewedd.com/review"
        self.driver = None
        self.running = True  # 실행 상태 플래그 추가
        self.site_name = "THE FIRST HALL"
        self.csv_filename = ""
        self.product_obj_list = []
        self.total_cnt = 0
        self.page = 0
        self.current_cnt = 0
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }


    # 초기화
    def init(self):
        self.driver_set(True)
        self.driver.get(self.site_url)
        return True

    # 메인
    def main(self):
        try:
            self.log_signal.emit("크롤링 시작")

            self.set_cookies()

            # csv파일 만들기
            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)


            self.excel_driver.init_csv(self.csv_filename, self.columns)

            # url 가져오기
            self.api_url_obj_list()

            # 상세 데이터
            self.api_detail_data()

            # CSV -> 엑셀 변환
            self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)

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

        self.driver = self.selenium_driver.start_driver(1200)


    # 쿠키세팅
    def set_cookies(self):
        self.log_signal_func("📢 쿠키 세팅 시작")
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)
        self.log_signal_func("📢 쿠키 세팅 완료")
        time.sleep(2)

    def api_url_obj_list(self):
        items, seen = [], set()
        self.page = 1
        while True:
            if not self.running:  # 실행 상태 확인
                break

            url = f"{self.site_review_url}?page={self.page}&category=&cate=&event_type=&desc=&desc2=&list_limit="

            try:
                resp = self.api_client.get(url, headers=self.headers)
                soup = BeautifulSoup(resp, "html.parser")
                table = soup.find("table", class_="story_list_tbl")
                rows = table.select("tbody tr") if table else []

                if not rows:
                    self.log_signal_func(f"📢 PAGE : {self.page} 데이터 없어 종료")
                    break

                got = 0
                for i, tr in enumerate(rows, start=1):
                    tds = tr.find_all("td")
                    no_text = bs_txt(tds[0]) if tds else ""
                    a = tr.select_one("td.subject a[href]")
                    if not a:
                        continue
                    href = (a.get("href") or "").strip()
                    full = href if href.startswith("http") else urljoin(self.site_url, href)

                    # 날짜: 보통 마지막 td가 등록일
                    reg_dt = bs_txt(tds[-1]) if len(tds) >= 3 else bs_txt(tr.select_one("td.date"))

                    if full in seen:
                        continue
                    seen.add(full)
                    items.append({
                        "No": no_text,
                        "등록일": reg_dt,
                        "url": full,
                    })
                    got += 1

                    self.log_signal_func(f"📢 PAGE:{self.page} / ROW:{i}/{len(rows)} => No={no_text}, 등록일={reg_dt}, url={full}")

                self.log_signal_func(f"✅ PAGE:{self.page} 완료 (+{got}, 누적 {len(items)}개)")
                self.page += 1
                time.sleep(.5)

            except Exception as e:
                self.log_signal_func(f"❌ PAGE:{self.page} 에러: {e}")
                # 다음 페이지 시도 (원하면 여기서 break 처리로 바꿀 수 있음)
                self.page += 1
                time.sleep(1)

        self.url_obj_list = items



    # 기존 clean_text 유지하되 NBSP도 같이 정돈되도록 살짝 보강
    def clean_text(self, s):
        if s is None:
            return ""
        s = s.replace("\xa0", " ").replace("\u200b", " ")
        s = re.sub(r"[ \t]+", " ", s)
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()


    # 본문 컨테이너에서 이미지/미디어 제거, <a>는 텍스트만 남김
    def _strip_media_and_unwrap_links(self, container):
        if not container:
            return
        # 이미지/미디어 태그 제거
        for t in container.find_all(["img", "figure", "picture", "source", "iframe", "video", "svg", "noscript"]):
            t.decompose()
        # 링크는 텍스트만 남기기 (배너/광고 링크 텍스트가 없으면 자연스럽게 사라짐)
        for a in container.find_all("a"):
            a.unwrap()


    # <p>만 중심으로 문단을 재구성. <p>&nbsp;</p>는 빈 줄로.
    def _reconstruct_paragraphs(self, container):
        if not container:
            return ""

        # 우선 미디어 제거/링크 정리
        self._strip_media_and_unwrap_links(container)

        paragraphs = container.find_all("p")
        lines = []

        if paragraphs:
            for p in paragraphs:
                txt = p.get_text(" ", strip=True) #<p>Hello<b>World</b></p>  "Hello World"
                txt = str_norm(txt)
                # <p>&nbsp;</p> 같은 빈 문단 → 빈 줄
                if txt == "":
                    lines.append("")  # 빈 줄
                else:
                    lines.append(txt)
        else:
            # <p>가 없으면 전체 텍스트를 줄바꿈 기준으로 회수

            # <div class="container">
            # 안녕하세요&nbsp;세계
            # <p>첫 번째 문단</p>
            # <p>두 번째 문단</p>
            # 세 번째&nbsp;라인
            # </div>

            raw = container.get_text("\n", strip=True) #"안녕하세요 세계\n첫 번째 문단\n두 번째 문단\n세 번째 라인"
            raw = str_norm(raw) #"안녕하세요 세계\n첫 번째 문단\n두 번째 문단\n세 번째 라인"
            lines = raw.split("\n") # # ["안녕하세요 세계", "첫 번째 문단", "두 번째 문단", "세 번째 라인"]

        # 연속 빈 줄 1개로 압축
        out = []
        prev_blank = False
        # 직전 줄이 빈 줄이었는지" 기록
        # 중복 방지
        for ln in lines:
            if str_norm(ln) == "":
                if not prev_blank:
                    out.append("")
                prev_blank = True
            else:
                out.append(ln)
                prev_blank = False

        text = "\n".join(out).strip()
        return self.clean_text(text)


    def api_detail_data(self):
        # url_obj_list 길이 기준으로 로그
        self.log_signal_func(f"📌 총 {len(self.url_obj_list)}개 링크")
        self.total_cnt = len(self.url_obj_list)
        buffer_list = []

        for i, obj in enumerate(self.url_obj_list, start=1):
            if not self.running:  # 실행 상태 확인
                break
            url = obj.get("url")
            self.current_cnt += 1
            if not url:
                self.log_signal_func(f"[{i}] URL 없음, 스킵")
                continue

            try:
                resp = self.api_client.get(url, headers=self.headers)
                soup = BeautifulSoup(resp, "html.parser")

                # 타이틀 후보
                title_el = soup.select_one("table.review_view_tbl thead th")
                title_text = self.clean_text(str_norm(title_el.get_text(" ", strip=True))) if title_el else ""

                # 본문 컨테이너 후보: 테이블 구조 우선, 없으면 일반 컨테이너
                body_container = soup.select_one("table.review_view_tbl tbody")
                body_text = self._reconstruct_paragraphs(body_container) if body_container else ""

                obj["제목"] = title_text
                obj["내용"] = body_text

                buffer_list.append(obj)

                if i % 5 == 0:
                    self.excel_driver.append_to_csv(self.csv_filename, buffer_list, self.columns)

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal_func(f"[{self.current_cnt} / {self.total_cnt}] Data: {obj}")

                time.sleep(.5)

            except Exception as e:
                self.log_signal_func(f"[{i}] ❌ 에러: {e} / URL={url}")


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




