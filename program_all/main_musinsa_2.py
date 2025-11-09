#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import time
import random
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

# ========== 설정 ==========
INPUT_CSV = "musinsa_goodsNo.csv"
OUTPUT_CSV = "musinsa_goods_detail.csv"
MAX_WORKERS = 8
TIMEOUT = 15
COOKIE = "_gf=A; tr[vid]=690cd64ba2ced3.89427074; tr[vd]=1762448971; spses.3b08=*; _gcl_au=1.1.162592583.1762448974; _fwb=63Pg2anM5DBoKnDb8C0AZw.1762448973913; _kmpid=km|www.musinsa.com|1762448973916|2e4f8d53-cfdb-449e-96ad-f6bdacb4fbb4; _kmpid=km|musinsa.com|1762448973916|2e4f8d53-cfdb-449e-96ad-f6bdacb4fbb4; _ga=GA1.1.535182222.1762448975; _hjSession_1491926=eyJpZCI6ImZkZTNjN2IwLTg4ODQtNGEzOS1hZjM3LTE3YWQ3MDFmMTAyZSIsImMiOjE3NjI0NDg5NzYzOTQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MX0=; _fbp=fb.1.1762448976432.618507455695182386; _pin_unauth=dWlkPVlUUTNZekppTnpBdFpqSmlNUzAwTkdRMUxXSXpNVGd0T0dZek56azFZbU5qWVRSbA; cart_no=YtaS8zbZ9oVliFzswivpznZ2Jaijonhu8VT8DYcWYac%3D; _hjSessionUser_1491926=eyJpZCI6ImUxNjJlZWU3LWFkYmItNTAxYi1iNGYwLWZkMTQ2NTMyMDc0NCIsImNyZWF0ZWQiOjE3NjI0NDg5NzYzOTMsImV4aXN0aW5nIjp0cnVlfQ==; viewKind=3GridView; _tt_enable_cookie=1; _ttp=01K9D2S0D5J6202FHCSKF737TM_.tt.1; ab.storage.deviceId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%220e9a9b67-86a6-5722-0c44-03081f0bdf2b%22%2C%22c%22%3A1762449457605%2C%22l%22%3A1762449457605%7D; SimilarGoodsTooltipClosed=true; __cf_bm=iCYbpr6z6tF85LcvXCQMxc8WrAsQeUHzfAKhuG8dMvA-1762449885-1.0.1.1-EcLUG0z2RfOTtbX6QU5uXsePnNaOAeE282R_uDE3Ca1CFRpuWlrHBkQfSvQjU7aMcIKzz4fayDnaryKiPCR5gyblcz_gRe8b_T3gWN68qVw; cf_clearance=0l7RdazmyQqCZrhc.eaPn21FUX6M1rl0vhsjGVMQg9Q-1762450135-1.2.1.1-_gB7qGErFAHk4Q6NzSPEfs1AvI4lA6OfulymH.Bynel4cHBZnNgCaaC3_rHCmaREeUXO5nRa2VB6uvIEJbdLtnFhmfF9FKbVrlgkj7Hle9ksyWhFgXPAxEEXCwGX0dq.CyUz36M5QKURmPeC6.jGEj1dk6YWPtY6E0pQg.2IeU93rkj0dP7Ix4VLiw.Ny8VyVN17j33JUx1gFcLCFiJ9tT58yI2.F4Awdmh3xpQJc4U; tr[vt]=1762450204; tr[vc]=2; tr[pv]=2; wcs_bt=s_eacb1da8e76:1762450340; cto_bundle=H3fvPF9Bc0RGZGJ0dDgwbHJXUHMzVTVHRWZmNHdsSzBzNEt4QiUyQkFQVkhNdzd6WndLVG1Kb0llYzFCVWhUWmlCM3FOY1dtaTR3UUtkVm56WFFPd0NDdXp6bE02aEwwQzNqRHcxaUV5eFNUUFF0ZzBOMCUyQnMyZkIzb1RUTXRRWjJYbEx5amY; ab.storage.sessionId.1773491f-ef03-4901-baf8-dbf84e1de25b=%7B%22g%22%3A%22d4ee4610-dab9-613c-a448-9d54191154cf%22%2C%22e%22%3A1762452141771%2C%22c%22%3A1762449457603%2C%22l%22%3A1762450341771%7D; spid.3b08=29bd4078-3bed-4be9-9fc2-7174de021501.1762448974.1.1762450343..4e1fb59f-b4d1-4cd1-85f9-7188f6f8d121..b9d01b02-0ebf-4a70-b546-e937a1f9e377.1762448973650.101; ttcsid=1762449457580::DN4j4MT0LuAAlzyVHEux.1.1762450395718.0; ttcsid_CF2AOI3C77UCCRP8DVQG=1762449457579::LjPRftKPFx-5qHP_Wopu.1.1762450395718.0; _dd_s=rum=0&expire=1762451399973; _ga_8PEGV51YTJ=GS2.1.s1762448975$o1$g1$t1762450506$j60$l0$h0"  # 행님이 직접 넣을 것. 예: "cf_clearance=...; _gf=A; ..."

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.musinsa.com/category/104?gf=A",
    "Sec-CH-UA": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ======================
#  유틸 함수
# ======================
def read_goods_list(csv_path: str) -> List[int]:
    """CSV에서 goodsNo 컬럼을 읽어 리스트로 반환"""
    goods_list = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                gn = int(row.get("goodsNo") or 0)
                if gn:
                    goods_list.append(gn)
            except Exception:
                continue
    logging.info("총 %d개 goodsNo 로드 완료", len(goods_list))
    return goods_list


def fetch_detail(session: requests.Session, goods_no: int) -> Dict:
    """상품 상세 페이지 요청 후 goodsNm, email 추출"""
    url = f"https://www.musinsa.com/products/{goods_no}"
    try:
        res = session.get(url, timeout=TIMEOUT)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script_tag:
            logging.warning(f"goodsNo={goods_no} __NEXT_DATA__ 없음")
            return {}

        j = json.loads(script_tag.string)
        data = (((j or {}).get("props") or {}).get("pageProps") or {}).get("data") or {}
        goodsNm = data.get("goodsNm")
        company = data.get("company") or {}
        email = company.get("email")

        return {
            "goodsNo": goods_no,
            "goodsNm": goodsNm,
            "url": url,
            "email": email,
        }

    except Exception as e:
        logging.warning(f"goodsNo={goods_no} 에러: {e}")
        return {}


def main():
    goods_list = read_goods_list(INPUT_CSV)
    session = requests.Session()
    session.headers.update(HEADERS)
    if COOKIE.strip():
        session.headers["Cookie"] = COOKIE.strip()

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_detail, session, gn): gn for gn in goods_list}
        for fut in as_completed(futures):
            gn = futures[fut]
            try:
                result = fut.result()
                if result:
                    results.append(result)
            except Exception as e:
                logging.warning(f"goodsNo={gn} 예외 발생: {e}")
            time.sleep(random.uniform(0.05, 0.15))  # 서버 부담 완화

    # 결과 저장
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["goodsNo", "goodsNm", "url", "email"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    logging.info("총 %d개 상품 저장 완료 -> %s", len(results), OUTPUT_CSV)


if __name__ == "__main__":
    main()
