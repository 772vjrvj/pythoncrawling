# -*- coding: utf-8 -*-
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from datetime import datetime

# ============================
# === 설정값 ===
# ============================
EXCEL_IN = "kipris_match_result2.xlsx"
EXCEL_OUT = "kipris_match_result_filled.xlsx"

URL = "https://kopd.kipo.go.kr:8888/family.do"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://kopd.kipo.go.kr:8888",
    "referer": "https://kopd.kipo.go.kr:8888/index.do",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

print_lock = threading.Lock()


def safe_log(*msg):
    with print_lock:
        print(*msg)


def fetch_family_info(idx: int, ori_number: str, cookies: str):
    """
    ori_number → familyTable → countryCode 목록 추출 후

    - country_list: 전체 국가 코드 리스트 (빈값 제외)
    - all_codes = set(country_list)
    - 패밀리정보 (수) = len(all_codes)      # KR 포함, 중복 제거
    - 국내여부 = all_codes가 KR만 있으면 "국내", 아니면 ""

    return: (rowIndex, family_count, domestic_flag)
    """
    # 예: 1020040090349 → 20040090349 → KR.20040090349.A
    core = ori_number[2:]
    docdb_number = f"KR.{core}.A"

    payload = {
        "numberType1": "original",
        "ori_country": "KR",
        "ori_numberType": "U1301",
        "ori_number": ori_number,
        "docdb_numberType": "U1301",
        "docdb_number": docdb_number,
    }

    headers = HEADERS.copy()
    headers["cookie"] = cookies

    for attempt in range(1, 4):  # retry 3회
        try:
            resp = requests.post(URL, headers=headers, data=payload, timeout=15)

            if resp.status_code != 200:
                safe_log(f"[{idx}] 응답코드 {resp.status_code} (시도 {attempt}/3)")
                time.sleep(1)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", id="familyTable")

            if not table:
                safe_log(f"[{idx}] familyTable 없음 (시도 {attempt}/3)")
                return idx, 0, ""

            inputs = table.find_all("input", {"name": "countryCode"})
            country_list = [
                (inp.get("value") or "").strip()
                for inp in inputs
                if inp.get("value")
            ]

            if not country_list:
                # 국가코드 자체가 없으면 패밀리 없음 취급
                return idx, 0, ""

            # === 중복 제거된 전체 국가 수 (KR 포함) ===
            all_codes = set(country_list)
            family_count = len(all_codes)

            # === 국내여부 판단 ===
            # 전체 국가코드가 KR만 있으면 "국내"
            domestic_flag = "국내" if all_codes and all_codes.issubset({"KR"}) else ""

            return idx, family_count, domestic_flag

        except Exception as e:
            safe_log(f"[{idx}] 예외 발생 (시도 {attempt}/3): {str(e)}")
            time.sleep(1)

    # 3회 실패 시
    return idx, 0, ""


def main():
    safe_log("\n=== 엑셀 로드 ===")
    df = pd.read_excel(EXCEL_IN)

    if "출원번호(일자)" not in df.columns:
        raise Exception("엑셀에 '출원번호(일자)' 컬럼이 없음")

    total = len(df)
    safe_log(f"총 {total}건 처리 예정\n")

    # 실제 사용할 cookie (JSESSIONID 포함해서 최신으로 교체해서 사용)
    cookies = (
        "JSESSIONID=...;"  # TODO: 여기 브라우저에서 복사한 최신 쿠키 문자열로 교체
        " searchHistory=..."
    )

    results = []
    completed = 0
    start_time = datetime.now()

    safe_log(f"\n=== 멀티스레드 시작 (8 workers) ===")
    safe_log(f"시작시간: {start_time}\n")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {}

        for idx, row in df.iterrows():
            ori_number = str(row["출원번호(일자)"]).strip()

            # NaN 또는 빈값 처리
            if not ori_number or ori_number.lower() == "nan":
                fut = executor.submit(lambda i=idx: (i, 0, ""))
                futures[fut] = idx
                continue

            fut = executor.submit(fetch_family_info, idx, ori_number, cookies)
            futures[fut] = idx

        for future in as_completed(futures):
            idx, count, domestic_flag = future.result()
            completed += 1

            progress = (completed / total) * 100
            safe_log(
                f"[{completed}/{total}] ({progress:.2f}%) "
                f"idx={idx} → 패밀리정보 {count}건, 국내여부='{domestic_flag}'"
            )

            results.append((idx, count, domestic_flag))

    safe_log("\n=== 엑셀 업데이트 중 ===")

    # 컬럼이 없으면 새로 만들고, 있으면 덮어씀
    if "패밀리정보 (수)" not in df.columns:
        df["패밀리정보 (수)"] = 0
    if "국내여부" not in df.columns:
        df["국내여부"] = ""

    for idx, count, domestic_flag in results:
        df.at[idx, "패밀리정보 (수)"] = count
        df.at[idx, "국내여부"] = domestic_flag

    df.to_excel(EXCEL_OUT, index=False)

    end_time = datetime.now()
    safe_log("\n=== 완료 ===")
    safe_log("저장:", EXCEL_OUT)
    safe_log(f"종료시간: {end_time}")
    safe_log(f"총 소요시간: {end_time - start_time}")


if __name__ == "__main__":
    main()
