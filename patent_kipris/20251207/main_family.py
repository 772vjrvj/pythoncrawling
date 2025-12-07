# -*- coding: utf-8 -*-
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from datetime import datetime

EXCEL_IN = "251207_패밀리사이즈의뢰.xlsx"
EXCEL_OUT = "251207_패밀리사이즈의뢰_filled.xlsx"

URL = "https://kopd.kipo.go.kr:8888/family.do"

# ============================
# === 신규: 요청 헤더 ===
# ============================
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


# ============================
# === 신규: 로그 출력 함수 ===
# ============================
def safe_log(*msg):
    with print_lock:
        print(*msg)


# ============================
# === 신규: family 조회 함수 ===
# ============================
def fetch_family_count(idx, ori_number: str, cookies: str) -> (int, int):
    """
    ori_number → familyTable → countryCode 목록을 찾아
    - KR 제거
    - 중복 제거
    후 count 리턴
    return: (rowIndex, count)
    """

    core = ori_number[2:]  # 1020040090349 → 20040090349
    docdb_number = f"KR.{core}.A"

    payload = {
        "numberType1": "original",
        "ori_country": "KR",
        "ori_numberType": "U1301",
        "ori_number": ori_number,
        "docdb_numberType": "U1301",
        "docdb_number": docdb_number
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
                return idx, 0

            # ===== 신규 변경: countryCode input 모두 찾기 =====
            inputs = table.find_all("input", {"name": "countryCode"})
            country_list = [inp.get("value", "").strip() for inp in inputs]

            # KR 제거, 빈값 제거
            filtered = [c for c in country_list if c and c != "KR"]

            # 중복 제거
            unique = set(filtered)

            return idx, len(unique)

        except Exception as e:
            safe_log(f"[{idx}] 예외 발생 (시도 {attempt}/3): {str(e)}")
            time.sleep(1)

    # 실패 시 0
    return idx, 0



# ============================
# ============ MAIN ==========
# ============================
def main():
    safe_log("\n=== 엑셀 로드 ===")
    df = pd.read_excel(EXCEL_IN)

    if "출원번호(일자)" not in df.columns:
        raise Exception("엑셀에 '출원번호(일자)' 컬럼이 없음")

    total = len(df)
    safe_log(f"총 {total}건 처리 예정\n")

    safe_log("JSESSIONID 포함된 cookie 입력:")
    cookies = "JSESSIONID=sCRH3C8kgW78V3qyajTXnPkb1OiesQwkbveYQf0Pex4uvA8HtHor3C7fkwYDPytr.opdcws1_servlet_engine3; searchHistory=2025-11-24%01*33*05^KR^original%#application&^1020040090349^$2025-11-24%01*13*00^KR^original%#application&^1020040090349^$2025-11-24%01*10*25^KR^original%#application&^1020040090349^$2025-11-24%01*10*08^KR^original%#application&^1020040090349^$2025-11-24%01*09*44^KR^original%#application&^1020040090349^$2025-11-24%01*09*30^KR^original%#application&^1020040090349^"

    results = []
    completed = 0
    start_time = datetime.now()

    safe_log(f"\n=== 멀티스레드 시작 (8 workers) ===")
    safe_log(f"시작시간: {start_time}\n")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {}

        for idx, row in df.iterrows():
            ori_number = str(row["출원번호(일자)"]).strip()
            print(f'ori_number : {ori_number}')

            if not ori_number or ori_number.lower() == 'nan':
                futures[executor.submit(lambda: (idx, 0))] = idx
                continue

            futures[executor.submit(fetch_family_count, idx, ori_number, cookies)] = idx

        for future in as_completed(futures):
            idx, count = future.result()
            completed += 1

            progress = (completed / total) * 100
            safe_log(f"[{completed}/{total}] ({progress:.2f}%) idx={idx} → 패밀리정보 {count}건")

            results.append((idx, count))

    safe_log("\n=== 엑셀 업데이트 중 ===")

    df["패밀리정보 (수)"] = 0
    for idx, count in results:
        df.at[idx, "패밀리정보 (수)"] = count

    df.to_excel(EXCEL_OUT, index=False)

    end_time = datetime.now()
    safe_log("\n=== 완료 ===")
    safe_log("저장:", EXCEL_OUT)
    safe_log(f"종료시간: {end_time}")
    safe_log(f"총 소요시간: {end_time - start_time}")


if __name__ == "__main__":
    main()
