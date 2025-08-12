# file: parse_cdr_table_to_json.py
import os
import json
import requests
from bs4 import BeautifulSoup

URL = "https://vns.callmember.co.kr:28833/RELF/CdrHist/ifrmlist"
PARAMS = {"destcpid": ""}
VERIFY_TLS = True
TIMEOUT = 10

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/139.0.0.0 Safari/537.36"),
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://vns.callmember.co.kr:28833",
    "Referer": "https://vns.callmember.co.kr:28833/RELF/CdrHist/index.jsp",
    "Cookie": "q1000-gsp=MTc1NDgyNTY2OHxEWDhFQVFMX2dBQUJFQUVRQUFCcV80QUFBZ1p6ZEhKcGJtY01CZ0FFYzNOcFpBWnpkSEpwYm1jTUtnQW9TRkZTWldkeVFqaERWelZSUkZSVFN6Rk1jMmd6UTFNeldIUk5TMGhrU1UxSVRsZ3pkSHByY3daemRISnBibWNNQ1FBSGJHOW5hVzVwWkFaemRISnBibWNNQ1FBSFpHVjJaV3h2Y0E9PXwOrF2Pd_IbpUmRo0bbv3QSwEp-SuXKDtiov-DlaPFqLg==",  # 빈 쿠키로도 호출 가능
}

FORM = {
    "searchitem": "", "CpId": "", "searchstr": "",
    "searchitem2": "", "CpId": "", "searchstr2": "",
    # "fromdt": "2025-08-01", "todt": "2025-08-11",
    "fromdt": "2025-08-10", "todt": "2025-08-10",
    "linesperpage": "70", "CurPageNum": "1", "clmsort": "ascdesc"
}

EXPECTED_HEADERS = [
    "CPID","CP명","구분번호","시작시간","종료시간","통화시간",
    "발신","수신","가상번호","EtcVal1","EtcVal2","결과","녹음듣기"
]

def normalize_cells(tr):
    return [c.get_text(strip=True) for c in tr.find_all(["td","th"])]

def find_data_table(soup):
    """
    헤더 행에 EXPECTED_HEADERS 일부가 있는 테이블을 탐색하여 반환
    (중첩 테이블 대응)
    """
    candidate_tables = soup.find_all("table")
    for tbl in candidate_tables:
        trs = tbl.find_all("tr")
        if not trs:
            continue
        header = normalize_cells(trs[0])
        # 헤더에 핵심 키워드(예: CPID, 구분번호)가 있는지 검사
        hits = sum(1 for h in ["CPID","구분번호","시작시간","가상번호"] if h in header)
        if hits >= 2:  # 최소 2개 이상 맞으면 후보로 인정
            return tbl
    # 그래도 못 찾으면 가장 안쪽(마지막) 테이블 사용
    return candidate_tables[-1] if candidate_tables else None

def parse_html_to_json(html):
    soup = BeautifulSoup(html, "html.parser")
    tbl = find_data_table(soup)
    if not tbl:
        return []

    trs = tbl.find_all("tr")
    if not trs:
        return []

    # 첫 행을 헤더로 가정. 혹시 한글/공백 섞임 대비해서 strip 처리
    header = normalize_cells(trs[0])

    # 헤더가 우리가 기대한 것과 다르면, 기대 헤더로 강제 세팅
    # (실제 HTML은 동일 순서로 보였음)
    if len(header) < len(EXPECTED_HEADERS) or header[0] != "CPID":
        header = EXPECTED_HEADERS

    items = []
    for tr in trs[1:]:
        cols = normalize_cells(tr)
        if not cols:
            continue
        # 컬럼 수가 다르면 테이블 장식 행일 가능성 → 스킵 or 잘라내기
        if len(cols) < len(header):
            continue
        if len(cols) > len(header):
            cols = cols[:len(header)]
        row = dict(zip(header, cols))
        # 데이터 행 필터 (구분번호/시작시간 등이 비어있지 않은 것만)
        if row.get("구분번호") or row.get("시작시간") or row.get("가상번호"):
            items.append(row)

    return items

def fetch_and_parse():
    resp = requests.post(
        URL, params=PARAMS, data=FORM, headers=HEADERS,
        verify=VERIFY_TLS, timeout=TIMEOUT
    )
    print(f"status={resp.status_code}, content-type={resp.headers.get('Content-Type')}")
    items = parse_html_to_json(resp.text)
    print(f"총 {len(items)}건 변환됨")
    # 미리보기
    for it in items:
        print(it)
    # 필요하면 파일로 저장
    with open("cdr_list.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print("[saved] cdr_list.json")

if __name__ == "__main__":
    fetch_and_parse()
