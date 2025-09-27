# -*- coding: utf-8 -*-
"""
Nate 뉴스 검색 크롤러
- 입력: apology_titles_split.csv (열: 날짜[YYYY-MM-DD], 구단)
- 각 항목에 대해:
  q = "{구단} 사과문"
  ps1 = 날짜를 YYYYMMDD 로
  ps2 = ps1 + 14일
  검색 URL: https://news.nate.com/search?...&page={n}
- BeautifulSoup으로 파싱하여 ul.search-list > li 내 a.thumb-wrap의 href 수집
  - href가 http로 시작하지 않으면 "https://news.nate.com" 접두
- 페이지는 결과 없을 때까지 1,2,3... 증가
- 출력: nate_results.csv (열: 날짜, 구단, q, ps1, ps2, page, href)

# === 신규 ===
- 날짜가 없는 행은 아래 분기 범위로 대체 검색하고, 각 범위마다 page=1만 조회
  * 2025 Q3: 2025-07-01 ~ 2025-09-27(현재)
  * 2025 Q1: 2025-01-01 ~ 2025-03-31
  * 2025 Q2: 2025-04-01 ~ 2025-06-30
  * 2024 Q1~Q4 (정규 분기)
  * 2023 Q1~Q4 (정규 분기)
"""

import csv
import time
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
import pandas as pd


BASE_URL = "https://news.nate.com/search"
OUTPUT_CSV = "nate_results.csv"
INPUT_CSV = "apology_titles_split.csv"

# Nate 예시 헤더(쿠키 제외). 일부 브라우저 전용 헤더는 생략/치환.
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/140.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://news.nate.com/search",
    # 필요시 사용자가 직접 쿠키를 추가해 주세요: headers["Cookie"] = "..."
}

SESSION = requests.Session()
SESSION.headers.update(DEFAULT_HEADERS)

# === 신규 === 현재 날짜 고정 (요청 명시: 2025-09-27)
CURRENT_DATE = datetime(2025, 9, 27)


def ymd_dash_to_compact(ymd: str) -> str:
    """YYYY-MM-DD -> YYYYMMDD 변환 (실패 시 원본 반환)"""
    try:
        return datetime.strptime(ymd.strip(), "%Y-%m-%d").strftime("%Y%m%d")
    except Exception:
        return ymd


def add_days_yyyymmdd(yyyymmdd: str, days: int) -> str:
    """YYYYMMDD + days -> YYYYMMDD (실패 시 원본 반환)"""
    try:
        dt = datetime.strptime(yyyymmdd, "%Y%m%d") + timedelta(days=days)
        return dt.strftime("%Y%m%d")
    except Exception:
        return yyyymmdd


def ensure_absolute_url(href: str) -> str:
    """href가 http로 시작하지 않으면 nate 도메인 붙이기"""
    if not href:
        return ""
    href = href.strip()
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://news.nate.com" + href
    # 가끔 'view/2024...'처럼 나오는 경우 대비
    if href.startswith("view/"):
        return "https://news.nate.com/" + href
    # 그 외 상대경로도 최상위에 붙여줌
    return "https://news.nate.com/" + href.lstrip("/")


def build_search_url(q: str, ps1: str, ps2: str, page: int) -> str:
    """
    Nate 검색 URL 생성.
    - 고정 파라미터: f3=1, ps=3, refresh=0, refresh_option1=0, refresh_option2=0
    - page는 1부터
    """
    params = {
        "q": q,
        "f3": "1",
        "ps": "3",
        "ps1": ps1,
        "ps2": ps2,
        "refresh": "0",
        "refresh_option1": "0",
        "refresh_option2": "0",
        "page": str(page),
    }
    return f"{BASE_URL}?{urllib.parse.urlencode(params, doseq=True)}"


def fetch_html(url: str, timeout: int = 15) -> str:
    """요청/응답 처리 (간단 재시도 포함)"""
    for attempt in range(3):
        try:
            resp = SESSION.get(url, timeout=timeout)
            # 200 외에도 일부 3xx/4xx 페이지가 정상 HTML을 주기도 함. 여기서는 200만 허용.
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            _ = str(e)  # 안전 문자열
        time.sleep(1.2)  # 짧은 대기 후 재시도
    return ""


def parse_links_from_html(html: str) -> list[str]:
    """ul.search-list > li 내 a.thumb-wrap 의 href들을 절대 URL로 반환"""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", class_="search-list")
    if not ul:
        return []
    results = []
    for li in ul.find_all("li", recursive=False):
        a = li.find("a", class_="thumb-wrap")
        href = a.get("href").strip() if a and a.has_attr("href") else ""
        if href:
            results.append(ensure_absolute_url(href))
    return results


def read_input_objects(csv_path: Path) -> list[dict]:
    """
    apology_titles_split.csv 읽어 객체 배열 생성
    기대 형식: 열 이름 '날짜', '구단'
    """
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    records = []
    for _, row in df.iterrows():
        records.append({
            "날짜": row.get("날짜", "").strip(),
            "구단": row.get("구단", "").strip(),
        })
    return records


# === 신규 ===
def quarter_ranges_for_missing_date() -> list[tuple[str, str]]:
    """
    날짜가 비어있는 경우 사용할 분기 범위(YYYYMMDD, YYYYMMDD) 목록.
    - 2025 Q3: 2025-07-01 ~ 2025-09-27(현재)
    - 2025 Q1, Q2
    - 2024 Q1~Q4
    - 2023 Q1~Q4
    반환값: [("YYYYMMDD","YYYYMMDD"), ...]
    """
    def comp(s: str) -> str:
        return s.replace("-", "")

    ranges: list[tuple[str, str]] = []

    # 2025 Q3 (끝은 현재일)
    # ranges.append((comp("2025-07-01"), CURRENT_DATE.strftime("%Y%m%d")))
    # 2025 Q1, Q2
    # ranges.append((comp("2025-01-01"), comp("2025-03-31")))
    # ranges.append((comp("2025-04-01"), comp("2025-06-30")))
    # 2024 Q1~Q4
    # ranges.extend([
    #     (comp("2024-01-01"), comp("2024-03-31")),
    #     (comp("2024-04-01"), comp("2024-06-30")),
    #     (comp("2024-07-01"), comp("2024-09-30")),
    #     (comp("2024-10-01"), comp("2024-12-31")),
    # ])
    # 2023 Q1~Q4
    # ranges.extend([
    #     (comp("2023-01-01"), comp("2023-03-31")),
    #     (comp("2023-04-01"), comp("2023-06-30")),
    #     (comp("2023-07-01"), comp("2023-09-30")),
    #     (comp("2023-10-01"), comp("2023-12-31")),
    # ])
    # 2022~Q4
    ranges.extend([
        (comp("2022-01-01"), comp("2022-03-31")),
        (comp("2022-04-01"), comp("2022-06-30")),
        (comp("2022-07-01"), comp("2022-09-30")),
        (comp("2022-10-01"), comp("2022-12-31")),
    ])
    # 2021 Q1~Q4
    ranges.extend([
        (comp("2021-01-01"), comp("2021-03-31")),
        (comp("2021-04-01"), comp("2021-06-30")),
        (comp("2021-07-01"), comp("2021-09-30")),
        (comp("2021-10-01"), comp("2021-12-31")),
    ])
    # 2020 Q1~Q4
    ranges.extend([
        (comp("2020-01-01"), comp("2020-03-31")),
        (comp("2020-04-01"), comp("2020-06-30")),
        (comp("2020-07-01"), comp("2020-09-30")),
        (comp("2020-10-01"), comp("2020-12-31")),
    ])
    return ranges


def crawl_for_item(item: dict) -> list[dict]:
    """
    단일 아이템(날짜, 구단)에 대해 페이지를 돌며 모든 링크 수집
    반환: [{날짜, 구단, q, ps1, ps2, page, href}, ...]
    """
    ymd_dash = item.get("날짜", "")
    club = item.get("구단", "")
    if not club:
        return []

    q = f"{club} 사과문"

    # === 신규 === 날짜가 있는 경우: 기존 로직(2주 범위 + 페이지네이션)
    if ymd_dash:
        ps1 = ymd_dash_to_compact(ymd_dash)
        ps2 = add_days_yyyymmdd(ps1, 14)

        page = 1
        out_rows = []

        while True:
            url = build_search_url(q, ps1, ps2, page)
            print(url)
            html = fetch_html(url)
            links = parse_links_from_html(html)

            if not links:
                break

            for href in links:
                obj = {
                    "날짜": ymd_dash,
                    "구단": club,
                    "q": q,
                    "ps1": ps1,
                    "ps2": ps2,
                    "page": page,
                    "href": href,
                }
                print(f'obj : {obj}')
                out_rows.append(obj)

            time.sleep(0.8)
            page += 1

        return out_rows

    # === 신규 === 날짜가 없는 경우: 지정 분기 범위 목록으로 검색, 각 범위는 page=1만 조회
    out_rows: list[dict] = []
    for ps1, ps2 in quarter_ranges_for_missing_date():
        page = 1
        url = build_search_url(q, ps1, ps2, page)
        print(url)
        html = fetch_html(url)
        links = parse_links_from_html(html)

        # 해당 분기에 결과가 없으면 다음 분기로 패스
        if not links:
            continue

        for href in links:
            obj = {
                "날짜": ymd_dash,  # 원본이 비어있으므로 그대로 둠
                "구단": club,
                "q": q,
                "ps1": ps1,
                "ps2": ps2,
                "page": page,     # 분기 검색은 항상 1페이지
                "href": href,
            }
            print(f'obj : {obj}')
            out_rows.append(obj)

        time.sleep(0.8)

    return out_rows


def write_results_csv(rows: list[dict], out_path: Path) -> None:
    """결과 CSV 저장"""
    if not rows:
        # 빈 결과라도 헤더는 쓰자
        fieldnames = ["날짜", "구단", "q", "ps1", "ps2", "page", "href"]
        with out_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return

    fieldnames = ["날짜", "구단", "q", "ps1", "ps2", "page", "href"]
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> None:
    base_dir = Path(".").resolve()
    input_path = base_dir / INPUT_CSV
    output_path = base_dir / OUTPUT_CSV

    items = read_input_objects(input_path)

    all_rows: list[dict] = []
    for item in items:
        rows = crawl_for_item(item)
        all_rows.extend(rows)

    write_results_csv(all_rows, output_path)
    print(f"✅ 완료: {output_path} ({len(all_rows)}건)")


if __name__ == "__main__":
    main()
