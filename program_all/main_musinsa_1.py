#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
무신사 PLP(goods) API에서 goodsNo만 추출하여 CSV로 저장하는 스크립트
- 멀티스레드: ThreadPoolExecutor(max_workers=8)
- 헤더: 사용자가 제공한 헤더(쿠키 제외)를 기본으로 설정
- 쿠키: COOKIE 변수에 직접 넣어서 사용하세요
"""

import csv
import math
import time
import random
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# === 설정 ===
BASE = "https://api.musinsa.com/api2/dp/v1/plp/goods"
CATEGORY = "104"
GF = "A"
SIZE = 60
SORT = "POPULAR"
CALLER = "CATEGORY"
MAX_WORKERS = 8
CSV_PATH = "musinsa_goodsNo.csv"
TIMEOUT = 15
# === 사용자 쿠키: 여기에 본인 쿠키 문자열을 넣으세요 (쿠키는 본인이 제공) ===
COOKIE: str = "_gf=A; cf_clearance=EmVVS03YmlPQJ3nj3hKCTZvdoJK6rycv44KUsxa7HOo-1762448971-1.2.1.1-FakmOzUVUtbEs1EGI33Dw4GAGbqDy4bH3u4VSM_8vuLAHsn3XIZ4aU3STf09_8y_mOXkTDpGCteyFVBcBvhwIAkRD4qqcUZW_fJTUZsQZNvD0gGl7K7zSgCGPrwEIPl5Sjf4n00EXrd9FMgcf__i3xpl8IZPF9kdDoxvcjnGII.8kqh51lUJGK75vg._0iFjtNrgFajo6bJ7gtUuoZgSiBQHXvXghElWSobo7cCS9Fo; tr[vid]=690cd64ba2ced3.89427074; tr[vd]=1762448971; tr[vt]=1762448971; tr[vc]=1; spses.3b08=*; _gcl_au=1.1.162592583.1762448974; _fwb=63Pg2anM5DBoKnDb8C0AZw.1762448973913; _kmpid=km|musinsa.com|1762448973916|2e4f8d53-cfdb-449e-96ad-f6bdacb4fbb4; _ga=GA1.1.535182222.1762448975; _hjSession_1491926=eyJpZCI6ImZkZTNjN2IwLTg4ODQtNGEzOS1hZjM3LTE3YWQ3MDFmMTAyZSIsImMiOjE3NjI0NDg5NzYzOTQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MX0=; _fbp=fb.1.1762448976432.618507455695182386; _pin_unauth=dWlkPVlUUTNZekppTnpBdFpqSmlNUzAwTkdRMUxXSXpNVGd0T0dZek56azFZbU5qWVRSbA; cart_no=YtaS8zbZ9oVliFzswivpznZ2Jaijonhu8VT8DYcWYac%3D; _hjSessionUser_1491926=eyJpZCI6ImUxNjJlZWU3LWFkYmItNTAxYi1iNGYwLWZkMTQ2NTMyMDc0NCIsImNyZWF0ZWQiOjE3NjI0NDg5NzYzOTMsImV4aXN0aW5nIjp0cnVlfQ==; viewKind=3GridView; tr[pv]=12; cto_bundle=2GENt19Bc0RGZGJ0dDgwbHJXUHMzVTVHRWZmZThjZU5yMGIyNGtrYlk1N2pVMnh4MnZFb0R4MnBST3FxZDZoQXVOeE5Md3dwZW0wWmhPa3lNN0xBMFNjNCUyQnhwMnZTeVJhRjQyMmxXNTFYZFJrUllsZlJnbDdhNDRWNXB0bVRQY1JtZDVa; spid.3b08=29bd4078-3bed-4be9-9fc2-7174de021501.1762448974.1.1762449457..4e1fb59f-b4d1-4cd1-85f9-7188f6f8d121..b9d01b02-0ebf-4a70-b546-e937a1f9e377.1762448973650.89; _tt_enable_cookie=1; _ttp=01K9D2S0D5J6202FHCSKF737TM_.tt.1; ab.storage.deviceId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%220e9a9b67-86a6-5722-0c44-03081f0bdf2b%22%2C%22c%22%3A1762449457605%2C%22l%22%3A1762449457605%7D; ab.storage.sessionId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%22d4ee4610-dab9-613c-a448-9d54191154cf%22%2C%22e%22%3A1762451257620%2C%22c%22%3A1762449457603%2C%22l%22%3A1762449457620%7D; SimilarGoodsTooltipClosed=true; ttcsid=1762449457580::DN4j4MT0LuAAlzyVHEux.1.1762449472381.0; ttcsid_CF2AOI3C77UCCRP8DVQG=1762449457579::LjPRftKPFx-5qHP_Wopu.1.1762449472381.0; __cf_bm=iCYbpr6z6tF85LcvXCQMxc8WrAsQeUHzfAKhuG8dMvA-1762449885-1.0.1.1-EcLUG0z2RfOTtbX6QU5uXsePnNaOAeE282R_uDE3Ca1CFRpuWlrHBkQfSvQjU7aMcIKzz4fayDnaryKiPCR5gyblcz_gRe8b_T3gWN68qVw; _ga_8PEGV51YTJ=GS2.1.s1762448975$o1$g1$t1762449901$j59$l0$h0"  # 예: "cf_clearance=...; _gf=A; ..." (빈 문자열이면 헤더에 추가 안함)

# === 요청 헤더 (제공하신 값 기반, Cookie 제외) ===
HEADERS = {
    # pseudo/mandatory pseudo-headers are not used by requests but shown here for clarity (not included)
    # normal headers below:
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.musinsa.com",
    "Referer": "https://www.musinsa.com/",
    "Sec-CH-UA": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    # priority / :method / :scheme etc are not set as HTTP headers for requests library
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def build_params(page: int) -> Dict[str, Any]:
    """page -> 쿼리 파라미터(특히 seen 계산) 반환"""
    if page == 1:
        seen = 0
    else:
        # 사용자가 제시한 규칙: page 1 -> seen 0, 이후는 61,121,... => (page-1)*SIZE + 1
        seen = (page - 1) * SIZE + 1
    return {
        "gf": GF,
        "sortCode": SORT,
        "category": CATEGORY,
        "size": str(SIZE),
        "testGroup": "",
        "caller": CALLER,
        "page": str(page),
        "seen": str(seen),
        "seenAds": "",
    }


def fetch_page(session: requests.Session, page: int, retries: int = 3) -> List[int]:
    """
    단일 페이지 요청 후 goodsNo 리스트 반환.
    간단한 재시도(backoff + jitter) 포함.
    """
    params = build_params(page)
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(BASE, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            j = resp.json()
            lst = (((j or {}).get("data") or {}).get("list")) or []
            goods_nos: List[int] = []
            for it in lst:
                # 안전하게 파싱
                try:
                    gn = int(it.get("goodsNo"))
                except Exception:
                    continue
                goods_nos.append(gn)

            logging.info("page=%d fetched items=%d", page, len(goods_nos))
            # 짧은 랜덤 지연(서버 부담 완화)
            time.sleep(random.uniform(0.05, 0.18))
            return goods_nos

        except Exception as e:
            wait = (attempt * 0.7) + random.uniform(0, 0.3)
            logging.warning("page=%d attempt=%d error=%s -> retry in %.2fs", page, attempt, str(e), wait)
            time.sleep(wait)

    logging.error("page=%d failed after %d retries", page, retries)
    return []


def discover_total_pages(session: requests.Session) -> (int, List[int]):
    """
    첫 페이지 조회로 totalPages를 찾고, 첫 페이지의 goodsNo를 함께 반환.
    """
    resp = session.get(BASE, params=build_params(1), timeout=TIMEOUT)
    resp.raise_for_status()
    j = resp.json()
    data = (j or {}).get("data") or {}
    pg = data.get("pagination") or {}
    total_pages = int(pg.get("totalPages") or 0)
    size = int(pg.get("size") or SIZE)

    # 방어적 계산: totalPages가 없을 때 totalCount로 계산
    if total_pages == 0 and pg.get("totalCount") is not None:
        total = int(pg.get("totalCount"))
        total_pages = math.ceil(total / size) if size > 0 else 0

    # 첫 페이지 리스트 수집
    first_list = (((j or {}).get("data") or {}).get("list")) or []
    first_goods = []
    for it in first_list:
        try:
            gn = int(it.get("goodsNo"))
            first_goods.append(gn)
        except Exception:
            continue

    return total_pages, first_goods


def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    if COOKIE and COOKIE.strip():
        # 사용자가 COOKIE 문자열을 직접 넣을 경우에만 추가
        session.headers.update({"Cookie": COOKIE.strip()})

    logging.info("discovering total pages from first page...")
    try:
        total_pages, first_goods = discover_total_pages(session)
    except Exception as e:
        logging.exception("첫 페이지에서 totalPages 정보를 가져오지 못했습니다: %s", str(e))
        return

    if total_pages <= 0:
        logging.error("totalPages가 0이거나 찾을 수 없습니다. 응답 구조가 변경되었을 수 있습니다.")
        return

    logging.info("total_pages=%d", total_pages)

    # 결과 집합(중복 제거용)
    goods_set = set(first_goods)


    # 남은 페이지(2..total_pages)를 병렬 호출
    pages_to_fetch = list(range(2, total_pages + 1))  # 1은 이미 수집
    logging.info("fetching %d pages (2..%d) with %d workers", len(pages_to_fetch), total_pages, MAX_WORKERS)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_page, session, p): p for p in pages_to_fetch}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                logging.exception("page %d 처리 중 예외: %s", p, str(e))
                result = []
            for gn in result:
                goods_set.add(gn)

    goods_sorted = sorted(goods_set)
    logging.info("total unique goodsNo collected: %d", len(goods_sorted))

    # CSV 쓰기
    try:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(["goodsNo"])
            for gn in goods_sorted:
                writer.writerow([gn])
        logging.info("CSV saved: %s", CSV_PATH)
    except Exception as e:
        logging.exception("CSV 저장 중 오류: %s", str(e))


if __name__ == "__main__":
    main()
