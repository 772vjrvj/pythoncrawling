# -*- coding: utf-8 -*-
import os
import re
import csv
import json
import time
import html
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor


# =========================================================
# Config
# =========================================================
@dataclass
class PeachhillConfig:
    base_url: str = "https://peachhill.kr"
    list_path: str = "/26/"
    pages: range = range(1, 5)

    out_dir: Path = Path("./out_peachhill_26")
    csv_path: Path = Path("./out_peachhill_26/products.csv")
    detail_root: Path = Path("./out_peachhill_26/detail_images")

    timeout: int = 20
    retries: int = 3
    max_workers: int = 8
    sleep_between_pages: float = 0.4
    sleep_between_items: float = 0.15

    # 다운로드 진행 로그 간격
    log_every_download_done: int = 20

    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/143.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
            }


# =========================================================
# Crawler
# =========================================================
class Peachhill26Crawler:

    # 폴더명(요구사항 반영)
    DIR_LIST_IMAGES = "list_images"
    DIR_THUMBNAILS = "thumbnails"
    DIR_DETAIL_IMAGES = "detail_images"

    def __init__(self, config: Optional[PeachhillConfig] = None):
        self.cfg = config or PeachhillConfig()
        self.cfg.out_dir.mkdir(parents=True, exist_ok=True)
        self.cfg.detail_root.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # utils
    # -------------------------
    def uniq_keep_order(self, seq: List[str]) -> List[str]:
        seen, out = set(), []
        for x in seq:
            x = (x or "").strip()
            if not x:
                continue
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    def guess_ext(self, url: str) -> str:
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        return ext if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"] else ".jpg"

    def build_img_path(self, product_code: str, subdir: str, url: str, prefix: str, seq: int) -> Path:
        h = hashlib.md5(url.encode()).hexdigest()[:10]
        return self.cfg.detail_root / product_code / subdir / f"{prefix}_{seq:03d}_{h}{self.guess_ext(url)}"

    def download_one(self, url: str, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 0:
            return
        with requests.get(url, headers=self.cfg.headers, stream=True, timeout=self.cfg.timeout) as r:
            r.raise_for_status()
            tmp = path.with_suffix(path.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(65536):
                    if chunk:
                        f.write(chunk)
            tmp.replace(path)

    def _safe_json_loads(self, s: str) -> dict:
        try:
            return json.loads(s)
        except Exception:
            return {}

    # =====================================================
    # 1) LIST SCRAPE
    # =====================================================
    def scrape_list(self) -> List[Dict[str, Any]]:
        products, seen_product_codes = [], set()

        with requests.Session() as s:
            for page in self.cfg.pages:
                url = urljoin(self.cfg.base_url, self.cfg.list_path)
                print(f"[LIST] page={page} GET {url}?page={page}")

                r = s.get(url, params={"page": page}, headers=self.cfg.headers, timeout=self.cfg.timeout)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")

                items = soup.select("div.shop-item._shop_item")
                print(f"[LIST] page={page} items={len(items)}")

                for item in items:
                    raw = html.unescape(item.get("data-product-properties", "{}"))
                    props = self._safe_json_loads(raw)

                    product_code = str(props.get("idx") or "").strip()  # === 상품코드 ===
                    if not product_code:
                        continue
                    if product_code in seen_product_codes:
                        continue
                    seen_product_codes.add(product_code)

                    product_name = props.get("name") or ""
                    product_price = props.get("price") or ""

                    # 상세 URL
                    a = item.select_one('a[href*="idx="]')
                    detail_url = urljoin(self.cfg.base_url, a["href"]) if a and a.get("href") else ""
                    if not detail_url:
                        detail_url = urljoin(self.cfg.base_url, f"{self.cfg.list_path}?idx={product_code}")

                    # 목록 이미지 URL 2개를 배열로
                    imgs = []
                    for img in item.select("img"):
                        src = (img.get("src") or "").strip()
                        if src:
                            imgs.append(urljoin(self.cfg.base_url, src))
                        if len(imgs) == 2:
                            break
                    imgs = self.uniq_keep_order(imgs)

                    products.append({
                        # === 컬럼 스키마(요구사항) ===
                        "product_code": product_code,
                        "product_name": product_name,
                        "product_price": product_price,
                        "detail_url": detail_url,

                        "list_image_urls": json.dumps(imgs, ensure_ascii=False),  # 목록 이미지 URL(배열)
                        "list_image_names": "[]",                                # 목록 이미지명(배열) - 다운로드 후 채움

                        "thumbnail_image_urls": "[]",                            # 썸네일 이미지 URL(배열) - HTML에서 채움
                        "thumbnail_image_names": "[]",                           # 썸네일 이미지명(배열)

                        "youtube_url": "",                                       # 유튜브 URL
                        "detail_image_urls": "[]",                               # 상세 이미지 URL(배열) - AJAX에서 채움
                        "detail_image_names": "[]",                              # 상세 이미지명(배열)
                    })

                time.sleep(self.cfg.sleep_between_pages)

        print(f"[LIST] done. total_products={len(products)}")
        return products

    # =====================================================
    # 2) 목록 이미지 다운로드 (list_images)
    #     - list_image_urls: 이미 있음(JSON 배열)
    #     - list_image_names: 파일명 배열로 채움
    # =====================================================
    def download_list_images(self, products: List[Dict[str, Any]]) -> None:
        futures = []

        def _task(url: str, path: Path):
            self.download_one(url, path)

        with ThreadPoolExecutor(self.cfg.max_workers) as ex:
            for p in products:
                product_code = (p.get("product_code") or "").strip()
                if not product_code:
                    p["list_image_names"] = "[]"
                    continue

                urls = self._safe_json_loads(p.get("list_image_urls") or "[]")
                if isinstance(urls, dict):
                    urls = []
                urls = self.uniq_keep_order(urls if isinstance(urls, list) else [])

                names = []
                for i, u in enumerate(urls, start=1):
                    path = self.build_img_path(product_code, self.DIR_LIST_IMAGES, u, "list", i)
                    names.append(path.name)
                    futures.append((ex.submit(_task, u, path), product_code, path.name))

                p["list_image_names"] = json.dumps(names, ensure_ascii=False)

            total = len(futures)
            done = 0
            print(f"[LIST-IMG] download start. total_files={total}")

            for fut, code, fname in futures:
                try:
                    fut.result()
                except Exception as e:
                    print(f"[LIST-IMG][WARN] product_code={code} file={fname} err={str(e)}")

                done += 1
                if done % self.cfg.log_every_download_done == 0 or done == total:
                    print(f"[LIST-IMG] progress {done}/{total}")

            print("[LIST-IMG] download done.")

    # =====================================================
    # 3) AJAX (NO COOKIE) -> content에서
    #     - youtube_url
    #     - detail_image_urls (배열)
    #     - detail_image_names (배열, 파일명)
    #     폴더: detail_images/{product_code}/detail_images/
    # =====================================================
    def ajax_json(self, product_code: str) -> Dict[str, Any]:
        url = urljoin(self.cfg.base_url, "/ajax/oms/OMS_get_product.cm")
        r = requests.get(
            url,
            params={"prod_idx": product_code},
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",  # zstd 제외(안정)
                "Accept-Language": "ko-KR,ko;q=0.9",
                "Referer": f"{self.cfg.base_url}/26/?idx={product_code}",
                "User-Agent": self.cfg.headers["User-Agent"],
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
            cookies={},  # 쿠키 차단
            timeout=self.cfg.timeout
        )
        r.raise_for_status()

        raw = (r.content or b"").lstrip()
        if not raw.startswith(b"{"):
            ct = (r.headers.get("content-type") or "")
            head = (r.text or "")[:200]
            raise RuntimeError(f"AJAX JSON 아님. ct={ct} body_head={head}")

        return r.json()

    def parse_ajax_content(self, content_html: str):
        soup = BeautifulSoup(content_html or "", "html.parser")

        youtube_url = ""
        iframe = soup.select_one('iframe[title*="YouTube"]')
        if iframe and iframe.get("src"):
            m = re.search(r"embed/([^?&/]+)", iframe["src"])
            if m:
                youtube_url = f"https://www.youtube.com/watch?v={m.group(1)}"

        detail_urls = []
        for img in soup.select("img.fr-dib"):
            src = (img.get("src") or "").strip()
            if src:
                detail_urls.append(urljoin(self.cfg.base_url, src))

        detail_urls = self.uniq_keep_order(detail_urls)
        return youtube_url, detail_urls

    def download_detail_images_from_ajax(self, product: Dict[str, Any]) -> None:
        product_code = (product.get("product_code") or "").strip()
        if not product_code:
            product["youtube_url"] = ""
            product["detail_image_urls"] = "[]"
            product["detail_image_names"] = "[]"
            return

        data = self.ajax_json(product_code)
        content = (data.get("data") or {}).get("content", "")

        youtube_url, detail_urls = self.parse_ajax_content(content)

        product["youtube_url"] = youtube_url
        product["detail_image_urls"] = json.dumps(detail_urls, ensure_ascii=False)

        futures = []

        def _task(url: str, path: Path):
            self.download_one(url, path)

        names = []
        with ThreadPoolExecutor(self.cfg.max_workers) as ex:
            for i, u in enumerate(detail_urls, start=1):
                path = self.build_img_path(product_code, self.DIR_DETAIL_IMAGES, u, "detail", i)
                names.append(path.name)
                futures.append((ex.submit(_task, u, path), product_code, path.name))

            total = len(futures)
            done = 0
            if total:
                print(f"[DETAIL-IMG] product_code={product_code} download start. total_files={total}")

            for fut, code, fname in futures:
                try:
                    fut.result()
                except Exception as e:
                    print(f"[DETAIL-IMG][WARN] product_code={code} file={fname} err={str(e)}")

                done += 1
                if total and (done % self.cfg.log_every_download_done == 0 or done == total):
                    print(f"[DETAIL-IMG] product_code={product_code} progress {done}/{total}")

        product["detail_image_names"] = json.dumps(names, ensure_ascii=False)

    # =====================================================
    # 4) 썸네일(shop_goods_img) HTML에서 추출/다운로드
    #     - thumbnail_image_urls: 배열
    #     - thumbnail_image_names: 배열(파일명)
    #     폴더: detail_images/{product_code}/thumbnails/
    # =====================================================
    def download_thumbnail_images(self, product: Dict[str, Any]) -> None:
        product_code = (product.get("product_code") or "").strip()
        detail_url = (product.get("detail_url") or "").strip()

        if not product_code or not detail_url:
            product["thumbnail_image_urls"] = "[]"
            product["thumbnail_image_names"] = "[]"
            return

        r = requests.get(detail_url, headers=self.cfg.headers, timeout=self.cfg.timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        urls = []
        for img in soup.select(".shop_goods_img img"):
            src = (img.get("src") or "").strip()
            if src:
                urls.append(urljoin(self.cfg.base_url, src))

        urls = self.uniq_keep_order(urls)
        product["thumbnail_image_urls"] = json.dumps(urls, ensure_ascii=False)

        futures = []

        def _task(url: str, path: Path):
            self.download_one(url, path)

        names = []
        with ThreadPoolExecutor(self.cfg.max_workers) as ex:
            for i, u in enumerate(urls, start=1):
                path = self.build_img_path(product_code, self.DIR_THUMBNAILS, u, "thumb", i)
                names.append(path.name)
                futures.append((ex.submit(_task, u, path), product_code, path.name))

            total = len(futures)
            done = 0
            if total:
                print(f"[THUMB-IMG] product_code={product_code} download start. total_files={total}")

            for fut, code, fname in futures:
                try:
                    fut.result()
                except Exception as e:
                    print(f"[THUMB-IMG][WARN] product_code={code} file={fname} err={str(e)}")

                done += 1
                if total and (done % self.cfg.log_every_download_done == 0 or done == total):
                    print(f"[THUMB-IMG] product_code={product_code} progress {done}/{total}")

        product["thumbnail_image_names"] = json.dumps(names, ensure_ascii=False)

    # =====================================================
    # CSV (lock fallback)
    # =====================================================
    def save_csv_with_lock_fallback(self, products: List[Dict[str, Any]]) -> Path:
        fields = [
            "product_code",            # 상품코드
            "product_name",            # 상품명
            "product_price",           # 상품가격
            "detail_url",              # 상품 상세 정보 URL

            "list_image_urls",         # 상품 목록 이미지 URL(배열)
            "list_image_names",        # 상품 목록 이미지명(배열)

            "thumbnail_image_urls",    # 썸네일 이미지 URL(배열)
            "thumbnail_image_names",   # 썸네일 이미지명(배열)

            "youtube_url",             # 유튜브 URL

            "detail_image_urls",       # 상품 상세정보 이미지 URL(배열)
            "detail_image_names",      # 상품 상세정보 이미지명(배열)
        ]

        def _write(path: Path):
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for p in products:
                    w.writerow({k: p.get(k, "") for k in fields})

        try:
            _write(self.cfg.csv_path)
            return self.cfg.csv_path
        except PermissionError as e:
            alt = self.cfg.out_dir / f"products_{int(time.time())}.csv"
            _write(alt)
            print(f"[WARN] CSV 잠김: {self.cfg.csv_path} err={str(e)}")
            print(f"[DONE] 대체 CSV 저장: {alt}")
            return alt

    # =====================================================
    # RUN
    # =====================================================
    def run(self) -> Path:
        # 1) 리스트
        products = self.scrape_list()

        # 2) 목록 이미지 다운로드
        print("[PIPE] step=LIST_IMAGES start")
        self.download_list_images(products)
        print("[PIPE] step=LIST_IMAGES done")

        # 3) AJAX 상세 이미지 + 유튜브
        print("[PIPE] step=AJAX_DETAIL start")
        total = len(products)
        for i, p in enumerate(products, 1):
            code = p.get("product_code")
            try:
                self.download_detail_images_from_ajax(p)
                print(f"[AJAX] {i}/{total} product_code={code} OK youtube={'Y' if p.get('youtube_url') else 'N'}")
            except Exception as e:
                print(f"[AJAX][ERR] {i}/{total} product_code={code} err={str(e)}")
                p.setdefault("youtube_url", "")
                p.setdefault("detail_image_urls", "[]")
                p.setdefault("detail_image_names", "[]")
            time.sleep(self.cfg.sleep_between_items)
        print("[PIPE] step=AJAX_DETAIL done")

        # 4) 썸네일(shop_goods_img)
        print("[PIPE] step=THUMBNAILS start")
        for i, p in enumerate(products, 1):
            code = p.get("product_code")
            try:
                self.download_thumbnail_images(p)
                print(f"[THUMB] {i}/{total} product_code={code} OK")
            except Exception as e:
                print(f"[THUMB][ERR] {i}/{total} product_code={code} err={str(e)}")
                p.setdefault("thumbnail_image_urls", "[]")
                p.setdefault("thumbnail_image_names", "[]")
            time.sleep(self.cfg.sleep_between_items)
        print("[PIPE] step=THUMBNAILS done")

        # 5) CSV
        saved = self.save_csv_with_lock_fallback(products)
        print(f"[DONE] CSV saved: {saved}")
        print(f"[DONE] image root: {self.cfg.detail_root.resolve()}")
        return saved


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    Peachhill26Crawler().run()
