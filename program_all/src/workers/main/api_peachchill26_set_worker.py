# -*- coding: utf-8 -*-
import os
import re
import json
import time
import html
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.workers.api_base_worker import BaseApiWorker
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils


class ApiPeachhill26SetLoadWorker(BaseApiWorker):
    """
    peachhill.kr /26 상품 수집 Worker (requests + BeautifulSoup)
    - Selenium/쿠키 불필요
    - page=st_page..ed_page 설정 시 그 범위만
    - 설정 없으면 page=1.. (데이터 없을 때까지, '직전 페이지와 동일'이면 종료)
    - self.columns는 상위에서 체크된 '엑셀 헤더(value)' 리스트로 들어옴
      => row 딕셔너리 key도 "엑셀 헤더 그대로" 사용해야 함
    """

    def __init__(self):
        super().__init__()

        # ===============================
        # 기본 설정
        # ===============================
        self.site_name = "피치힐"
        self.base_url = "https://peachhill.kr"
        self.list_path = "/26/"
        self.ajax_path = "/ajax/oms/OMS_get_product.cm"

        self.out_dir = Path("./peachhill26")
        self.detail_root = self.out_dir / "detail_images"

        self.timeout = 20
        self.retries = 3
        self.max_workers = 8
        self.sleep_between_pages = 0.35
        self.sleep_between_items = 0.10

        self.running = True

        # 진행률
        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        # IO 유틸
        self.excel_driver = None
        self.file_driver = None
        self.csv_filename = ""

        # 공통 headers (HTML)
        self.headers_html = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/143.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
        }

    # =========================================================
    # BaseApiWorker hook
    # =========================================================
    def init(self):
        self.driver_set()

        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.detail_root.mkdir(parents=True, exist_ok=True)

        # CSV 파일명 생성
        try:
            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        except Exception:
            ts = time.strftime("%Y%m%d_%H%M%S")
            self.csv_filename = str(self.out_dir / (self.site_name + "_" + ts + ".csv"))

        if not self.columns:
            raise RuntimeError("self.columns 가 비어있습니다. (설정에서 컬럼 체크 필요)")

        # CSV 초기화
        self.excel_driver.init_csv(self.csv_filename, self.columns)

        self.log_signal_func("✅ peachhill /26 init 완료")
        return True

    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ================================")
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)

    def stop(self):
        self.running = False

    def destroy(self):
        # 진행률 100% 찍고 종료 시그널
        try:
            self.progress_signal.emit(self.before_pro_value, 1000000)
        except Exception:
            pass

        self.log_signal_func("=============== peachhill 크롤링 종료중...")
        time.sleep(0.5)
        self.log_signal_func("=============== peachhill 크롤링 종료")

        try:
            self.progress_end_signal.emit()
        except Exception:
            pass

    # =========================================================
    # 설정: pages
    # =========================================================
    def get_page_range_from_setting(self):
        """
        setting 값 st_page, ed_page 있으면 (int, int)
        없으면 (None, None)
        """
        try:
            st = (self.get_setting_value(self.setting, "st_page") or "").strip()
            ed = (self.get_setting_value(self.setting, "ed_page") or "").strip()

            if not st or not ed:
                return None, None

            st_page = int(st)
            ed_page = int(ed)

            if st_page < 1:
                st_page = 1
            if ed_page < st_page:
                ed_page = st_page

            return st_page, ed_page
        except Exception:
            return None, None

    # =========================================================
    # Main
    # =========================================================
    def main(self):
        try:
            self.log_signal_func("🚀 peachhill /26 크롤링 시작")

            # 0) 페이지 범위 결정
            st_page, ed_page = self.get_page_range_from_setting()
            if st_page and ed_page:
                self.log_signal_func("📌 설정 페이지 범위: %s ~ %s" % (st_page, ed_page))
            else:
                self.log_signal_func("📌 설정 페이지 없음 -> page=1부터 끝까지(동일페이지 반복 감지로 종료)")

            # 1) 목록 전체 수집
            products = self.collect_all_products(st_page, ed_page)

            self.total_cnt = len(products)
            self.current_cnt = 0
            self.before_pro_value = 0

            if self.total_cnt <= 0:
                self.log_signal_func("⚠️ 수집된 상품이 없습니다. 종료")
                return False

            self.log_signal_func("📌 목록 수집 완료. 전체 상품수: %d" % self.total_cnt)

            # 2) 상품별 처리
            idx = 0
            for row in products:
                if not self.running:
                    self.log_signal_func("⛔ 중지 요청 감지. 작업 종료")
                    break

                idx += 1
                self.current_cnt = idx

                now_per = (self.current_cnt / float(self.total_cnt)) * 100.0
                self.log_signal_func("====================================================================================================")
                self.log_signal_func("전체 상품(%d/%d) [%.2f%%]" % (self.current_cnt, self.total_cnt, now_per))
                self.log_signal_func("현재 상품코드: %s" % (row.get("상품코드") or ""))
                self.log_signal_func("----------------------------------------------------------------------------------------------------")

                # (1) 목록 이미지(최대 2장)
                self.process_list_images(row)

                # (2) AJAX 상세(유튜브 + 상세이미지)
                self.process_ajax_detail(row)

                # (3) 상세 HTML 썸네일(.shop_goods_img)
                self.process_thumbnails(row)

                # (4) CSV append
                self.excel_driver.append_to_csv(self.csv_filename, [row], self.columns)

                # progress(0~1,000,000)
                pro_value = (self.current_cnt / float(self.total_cnt)) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal_func("✅ 저장 완료")
                self.log_signal_func("====================================================================================================")

                time.sleep(self.sleep_between_items)

            # 3) CSV -> 엑셀 변환
            try:
                self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
                self.log_signal_func("✅ CSV -> Excel 변환 완료")
            except Exception as e:
                self.log_signal_func("⚠️ CSV -> Excel 변환 실패(무시 가능): " + str(e))

            return True

        except Exception as e:
            self.log_signal_func("❌ 오류: " + str(e))
            return False

    # =========================================================
    # 유틸
    # =========================================================
    def uniq_keep_order(self, seq):
        seen = set()
        out = []
        for x in seq:
            x = (x or "").strip()
            if not x:
                continue
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    def guess_ext(self, url):
        try:
            ext = os.path.splitext(urlparse(url).path)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                return ext
        except Exception:
            pass
        return ".jpg"

    def build_img_path(self, product_code, subdir_ko, url, prefix, seq):
        h = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        filename = "%s_%03d_%s%s" % (prefix, seq, h, self.guess_ext(url))
        return self.detail_root / str(product_code) / subdir_ko / filename

    def download_one(self, url, path):
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists() and path.stat().st_size > 0:
            return

        last_err = None
        for i in range(self.retries):
            try:
                r = requests.get(url, headers=self.headers_html, stream=True, timeout=self.timeout)
                r.raise_for_status()

                tmp = path.with_suffix(path.suffix + ".part")
                f = open(tmp, "wb")
                try:
                    for chunk in r.iter_content(65536):
                        if chunk:
                            f.write(chunk)
                finally:
                    f.close()

                tmp.replace(path)
                return

            except Exception as e:
                last_err = e
                time.sleep(0.6 * (i + 1))

        raise RuntimeError("이미지 다운로드 실패: %s err=%s" % (url, str(last_err)))

    def http_get_text(self, url, params=None, headers=None):
        last_err = None
        for i in range(self.retries):
            try:
                r = requests.get(
                    url,
                    params=params,
                    headers=headers or self.headers_html,
                    timeout=self.timeout
                )
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_err = e
                time.sleep(0.6 * (i + 1))
        raise RuntimeError("GET 실패: %s err=%s" % (url, str(last_err)))

    # =========================================================
    # 1) 목록 수집
    # =========================================================
    def collect_all_products(self, st_page=None, ed_page=None):
        products = []
        seen_product_codes = set()

        list_url = urljoin(self.base_url, self.list_path)

        def parse_items(html_text):
            soup = BeautifulSoup(html_text, "html.parser")
            return soup.select("div.shop-item._shop_item")

        def fingerprint(item_divs):
            ids = []
            for it in item_divs:
                raw = it.get("data-product-properties") or ""
                raw = html.unescape(raw).strip()
                try:
                    props = json.loads(raw) if raw else {}
                except Exception:
                    props = {}
                pid = str(props.get("idx") or "").strip()
                if pid:
                    ids.append(pid)
            return "|".join(ids)

        # 설정 범위가 있으면 범위만
        if st_page and ed_page:
            page = st_page
            while self.running and page <= ed_page:
                self.log_signal_func("[LIST] page=%d 요청(설정)" % page)
                html_text = self.http_get_text(list_url, params={"page": page})
                item_divs = parse_items(html_text)
                self.log_signal_func("[LIST] page=%d items=%d" % (page, len(item_divs)))

                if item_divs:
                    self._append_list_items(item_divs, products, seen_product_codes)

                page += 1
                time.sleep(self.sleep_between_pages)

            return products

        # 설정 없으면 page=1..N, 동일 페이지 반복 감지로 종료
        page = 1
        last_fp = ""
        while self.running:
            self.log_signal_func("[LIST] page=%d 요청" % page)
            html_text = self.http_get_text(list_url, params={"page": page})
            item_divs = parse_items(html_text)
            self.log_signal_func("[LIST] page=%d items=%d" % (page, len(item_divs)))

            if not item_divs:
                self.log_signal_func("[LIST] page=%d 데이터 없음 -> 종료" % page)
                break

            fp = fingerprint(item_divs)
            if fp and fp == last_fp:
                self.log_signal_func("[LIST] page=%d 직전 페이지와 동일 감지 -> 종료" % page)
                break
            last_fp = fp

            self._append_list_items(item_divs, products, seen_product_codes)

            page += 1
            time.sleep(self.sleep_between_pages)

        return products

    def _append_list_items(self, item_divs, products, seen_product_codes):
        for item in item_divs:
            raw = item.get("data-product-properties") or ""
            raw = html.unescape(raw).strip()

            try:
                props = json.loads(raw) if raw else {}
            except Exception:
                props = {}

            product_code = str(props.get("idx") or "").strip()
            if not product_code:
                continue
            if product_code in seen_product_codes:
                continue
            seen_product_codes.add(product_code)

            product_name = props.get("name") or ""
            product_price = props.get("price") or ""

            # detail_url
            a = item.select_one('a[href*="idx="]')
            detail_url = urljoin(self.base_url, a.get("href")) if a and a.get("href") else ""
            if not detail_url:
                detail_url = urljoin(self.base_url, self.list_path + "?idx=" + product_code)

            # 목록 이미지(최대 2)
            imgs = []
            for img in item.select("img"):
                src = (img.get("src") or "").strip()
                if src:
                    imgs.append(urljoin(self.base_url, src))
                if len(imgs) >= 2:
                    break
            imgs = self.uniq_keep_order(imgs)

            # ✅ row key = 엑셀 헤더(value) 그대로
            products.append({
                "상품코드": product_code,
                "상품명": product_name,
                "상품가격": product_price,
                "상품 상세 정보 URL": detail_url,

                "상품 목록 이미지 URL": json.dumps(imgs, ensure_ascii=False),
                "상품 목록 이미지명": "[]",

                "썸네일 이미지 URL": "[]",
                "썸네일 이미지명": "[]",

                "YOUTUBE URL": "",

                "상품 상세정보 이미지 URL": "[]",
                "상품 상세정보 이미지명": "[]",
            })

    # =========================================================
    # 2) 목록 이미지 다운로드
    # =========================================================
    def process_list_images(self, row):
        product_code = (row.get("상품코드") or "").strip()
        if not product_code:
            row["상품 목록 이미지명"] = "[]"
            return

        try:
            urls = json.loads(row.get("상품 목록 이미지 URL") or "[]")
            if not isinstance(urls, list):
                urls = []
        except Exception:
            urls = []

        urls = self.uniq_keep_order(urls)
        if not urls:
            row["상품 목록 이미지명"] = "[]"
            return

        names = []
        futures = []

        self.log_signal_func("[상품목록이미지] 시작 상품코드=%s cnt=%d" % (product_code, len(urls)))

        ex = ThreadPoolExecutor(max_workers=self.max_workers)
        try:
            i = 0
            for u in urls:
                i += 1
                pth = self.build_img_path(product_code, "상품목록이미지", u, "목록", i)
                names.append(pth.name)
                futures.append(ex.submit(self.download_one, u, pth))

            done = 0
            total = len(futures)
            for f in as_completed(futures):
                _ = f.result()
                done += 1
                if done == total or done % 10 == 0:
                    self.log_signal_func("[상품목록이미지] 진행 상품코드=%s %d/%d" % (product_code, done, total))
        finally:
            ex.shutdown(wait=True)

        row["상품 목록 이미지명"] = json.dumps(names, ensure_ascii=False)
        self.log_signal_func("[상품목록이미지] 완료 상품코드=%s" % product_code)

    # =========================================================
    # 3) AJAX 상세 (쿠키 없이)
    # =========================================================
    def build_ajax_headers_no_cookie(self, product_code):
        product_code = str(product_code or "").strip()
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": self.base_url + "/26/?idx=" + product_code,
            "User-Agent": self.headers_html.get("User-Agent", ""),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    def http_get_json_no_cookie(self, product_code):
        url = urljoin(self.base_url, self.ajax_path)
        params = {"prod_idx": str(product_code).strip()}

        last_err = None
        for i in range(self.retries):
            try:
                r = requests.get(
                    url,
                    params=params,
                    headers=self.build_ajax_headers_no_cookie(product_code),
                    cookies={},  # 쿠키 차단
                    timeout=self.timeout,
                    allow_redirects=True
                )
                r.raise_for_status()

                raw = (r.content or b"").lstrip()
                if not raw.startswith(b"{"):
                    head = (r.text or "")[:200]
                    ct = (r.headers.get("content-type") or "")
                    raise RuntimeError("JSON 아님: status=%s ct=%s body_head=%s" % (r.status_code, ct, head))

                return r.json()

            except Exception as e:
                last_err = e
                time.sleep(0.6 * (i + 1))

        raise RuntimeError("AJAX GET(JSON) 실패: prod_idx=%s err=%s" % (product_code, str(last_err)))

    def parse_ajax_content(self, content_html):
        youtube_url = ""
        detail_urls = []

        soup = BeautifulSoup(content_html or "", "html.parser")

        # youtube iframe
        for iframe in soup.select("iframe[src]"):
            src = (iframe.get("src") or "").strip()
            if "youtube.com" not in src:
                continue
            m = re.search(r"youtube\.com/embed/([^?\"'&/]+)", src)
            if m:
                vid = (m.group(1) or "").strip()
                if vid:
                    youtube_url = "https://www.youtube.com/watch?v=" + vid
                break

        # 상세 이미지
        for img in soup.select("img.fr-dib"):
            src = (img.get("src") or img.get("data-src") or img.get("data-original") or "").strip()
            if src:
                detail_urls.append(urljoin(self.base_url, html.unescape(src).strip()))

        detail_urls = self.uniq_keep_order(detail_urls)
        return youtube_url, detail_urls

    def process_ajax_detail(self, row):
        product_code = (row.get("상품코드") or "").strip()
        if not product_code:
            row["YOUTUBE URL"] = ""
            row["상품 상세정보 이미지 URL"] = "[]"
            row["상품 상세정보 이미지명"] = "[]"
            return

        self.log_signal_func("[AJAX] 시작 상품코드=%s" % product_code)

        data = self.http_get_json_no_cookie(product_code)
        content_html = ""
        if isinstance(data, dict):
            content_html = (data.get("data") or {}).get("content") or ""

        youtube_url, detail_urls = self.parse_ajax_content(content_html)

        row["YOUTUBE URL"] = youtube_url
        row["상품 상세정보 이미지 URL"] = json.dumps(detail_urls, ensure_ascii=False)

        if not detail_urls:
            row["상품 상세정보 이미지명"] = "[]"
            self.log_signal_func("[AJAX] 완료 상품코드=%s (상세이미지=0)" % product_code)
            return

        names = []
        futures = []

        self.log_signal_func("[상품상세이미지] 시작 상품코드=%s cnt=%d" % (product_code, len(detail_urls)))

        ex = ThreadPoolExecutor(max_workers=self.max_workers)
        try:
            i = 0
            for u in detail_urls:
                i += 1
                pth = self.build_img_path(product_code, "상품상세이미지", u, "상세", i)
                names.append(pth.name)
                futures.append(ex.submit(self.download_one, u, pth))

            done = 0
            total = len(futures)
            for f in as_completed(futures):
                _ = f.result()
                done += 1
                if done == total or done % 10 == 0:
                    self.log_signal_func("[상품상세이미지] 진행 상품코드=%s %d/%d" % (product_code, done, total))
        finally:
            ex.shutdown(wait=True)

        row["상품 상세정보 이미지명"] = json.dumps(names, ensure_ascii=False)
        self.log_signal_func("[AJAX] 완료 상품코드=%s (상세이미지=%d)" % (product_code, len(detail_urls)))

    # =========================================================
    # 4) 상세 HTML 썸네일(.shop_goods_img)
    # =========================================================
    def process_thumbnails(self, row):
        product_code = (row.get("상품코드") or "").strip()
        detail_url = (row.get("상품 상세 정보 URL") or "").strip()

        if not product_code or not detail_url:
            row["썸네일 이미지 URL"] = "[]"
            row["썸네일 이미지명"] = "[]"
            return

        self.log_signal_func("[썸네일] 시작 상품코드=%s" % product_code)

        html_text = self.http_get_text(detail_url)
        soup = BeautifulSoup(html_text, "html.parser")

        urls = []
        for img in soup.select(".shop_goods_img img"):
            src = (img.get("src") or "").strip()
            if src:
                urls.append(urljoin(self.base_url, src))

        urls = self.uniq_keep_order(urls)
        row["썸네일 이미지 URL"] = json.dumps(urls, ensure_ascii=False)

        if not urls:
            row["썸네일 이미지명"] = "[]"
            self.log_signal_func("[썸네일] 완료 상품코드=%s (0)" % product_code)
            return

        names = []
        futures = []

        self.log_signal_func("[썸네일이미지] 시작 상품코드=%s cnt=%d" % (product_code, len(urls)))

        ex = ThreadPoolExecutor(max_workers=self.max_workers)
        try:
            i = 0
            for u in urls:
                i += 1
                pth = self.build_img_path(product_code, "썸네일이미지", u, "썸네일", i)
                names.append(pth.name)
                futures.append(ex.submit(self.download_one, u, pth))

            done = 0
            total = len(futures)
            for f in as_completed(futures):
                _ = f.result()
                done += 1
                if done == total or done % 10 == 0:
                    self.log_signal_func("[썸네일이미지] 진행 상품코드=%s %d/%d" % (product_code, done, total))
        finally:
            ex.shutdown(wait=True)

        row["썸네일 이미지명"] = json.dumps(names, ensure_ascii=False)
        self.log_signal_func("[썸네일] 완료 상품코드=%s (cnt=%d)" % (product_code, len(urls)))
