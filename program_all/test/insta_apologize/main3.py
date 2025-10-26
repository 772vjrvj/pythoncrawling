# -*- coding: utf-8 -*-
"""
nate_results.csv → 기사 본문/제목 수집 후 CSV 저장 (멀티스레드 10개, 스포츠/iframe 대응, 링크·광고·스텁 제거 강화)

입력 CSV (예: nate_results.csv) 컬럼 예시:
- 날짜, 구단, q, ps1, ps2, page, href

처리 요약:
- href 중복 제거
- ThreadPoolExecutor(max_workers=10)로 10개씩 동시 요청/파싱
- 본문 처리(.content_view 기준, 없으면 스포츠/기타 폴백 + iframe 추적):
  * id="relnews_list" 통삭제
  * <p> 내에 <a>가 하나라도 있으면 그 <p> 통삭제
  * 모든 <a> 태그 삭제(decompose) — 텍스트도 남기지 않음
  * <script>, <img> 삭제
  * <br> → 개행
  * 빈 래퍼(<p>/<li>/<div>/<span>/<ul>/<ol>/section/aside) 정리
- 텍스트 후처리:
  * 불릿/화살표 스텁('▶','-','•','·','‣','◦') 라인 제거
  * 대괄호 링크 라인: ^\s*\[.*\]\s*$ 제거
  * http/https만 있는 라인 제거
  * '기자 + 이메일' 라인 발견 시 그 라인부터 끝까지 통삭제

출력:
- nate_results_with_content.csv (원본 컬럼 + title, contet)
"""

import re
import csv
from pathlib import Path
from typing import Tuple, Dict, Any, List
import concurrent.futures as cf
import threading

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# ----------------- 설정 -----------------
INPUT_CSV  = "nate_results.csv"
OUTPUT_CSV = "nate_results_with_content.csv"
REQUEST_TIMEOUT = 15

# 동시성
MAX_WORKERS = 10           # 스레드 수
BATCH_SIZE  = 10           # "10개씩" 처리

# 요청 헤더 (Cookie 필요시 직접 추가)
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://news.nate.com/search",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/140.0.0.0 Safari/537.36"),
}
# DEFAULT_HEADERS["Cookie"] = "pcid=...; ..."  # 필요시

# ----------------- 세션 (스레드별) -----------------
_thread_local = threading.local()
def get_session() -> requests.Session:
    sess = getattr(_thread_local, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update(DEFAULT_HEADERS)
        _thread_local.session = sess
    return sess

def fetch_html(url: str) -> str:
    """URL GET → HTML 텍스트 (실패 시 빈 문자열)."""
    try:
        r = get_session().get(url, timeout=REQUEST_TIMEOUT)
        if not r.encoding or r.encoding.lower() in ("iso-8859-1", "ascii"):
            r.encoding = r.apparent_encoding or "utf-8"
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return ""

# ----------------- DOM 유틸 -----------------
def br_to_newline(container):
    """container 내부의 <br>들을 개행으로 치환."""
    for br in container.find_all("br"):
        br.replace_with("\n")

def prune_empty_wrappers(container):
    """비어있는 래퍼 태그 제거."""
    for tag in container.find_all(["p", "li", "div", "span", "ul", "ol", "section", "aside"]):
        if not tag.get_text(strip=True):
            tag.decompose()

def remove_unwanted_in_scope(scope):
    """
    scope(보통 .content_view)에 한정하여 불필요 요소 제거:
    - #relnews_list 통삭제
    - <p> 내에 <a>가 하나라도 있으면 해당 <p> 통삭제
    - 모든 <a>, <script>, <img> 삭제 (a는 텍스트도 남기지 않음)
    - 빈 래퍼 정리 → <br>를 개행으로 치환 → 다시 빈 래퍼 정리
    """
    # relnews_list 제거
    for rel in scope.select("#relnews_list"):
        rel.decompose()

    # a 포함 p → 통삭제
    for p in list(scope.find_all("p")):
        if p.find("a"):
            p.decompose()

    # 남은 a/script/img 제거
    for tag in scope.find_all(["a", "script", "img"]):
        tag.decompose()

    prune_empty_wrappers(scope)
    br_to_newline(scope)
    prune_empty_wrappers(scope)

# ----------------- 스포츠/iframe 대응 -----------------
SPORTS_FALLBACK_SELECTORS: List[str] = [
    # 네이트 스포츠/외부매체에서 자주 보이는 컨테이너 후보
    ".newsEnd", ".newsEndCont", "#newsEndContents", "#artcContents",
    "#articleBody", ".articleBody", "article", ".article",
    "#article", "#content", "#contents", ".news_body",
    ".read", ".art_text", ".article-view", ".news-article"
]

def pick_largest_text_node(soup: BeautifulSoup, selectors: List[str]):
    """여러 셀렉터를 시도해 가장 긴 텍스트 컨테이너를 선택."""
    best = None
    best_len = 0
    for css in selectors:
        for node in soup.select(css):
            txt = node.get_text(strip=True)
            if len(txt) > best_len:
                best = node
                best_len = len(txt)
    return best

def try_follow_iframe(soup: BeautifulSoup, base_url: str) -> str:
    """본문이 iframe에 있을 경우 iframe src를 따라가서 본문을 재파싱."""
    for iframe in soup.find_all("iframe", src=True):
        src = iframe.get("src", "").strip()
        if not src:
            continue
        if src.startswith("//"):
            src = "https:" + src
        src = urljoin(base_url, src)
        html2 = fetch_html(src)
        if not html2:
            continue
        try:
            soup2 = BeautifulSoup(html2, "lxml")
        except Exception:
            soup2 = BeautifulSoup(html2, "html.parser")

        container2 = pick_largest_text_node(soup2, SPORTS_FALLBACK_SELECTORS)
        if container2:
            remove_unwanted_in_scope(container2)
            txt = container2.get_text(separator="\n")
            cleaned = clean_text(txt)
            if cleaned:
                return cleaned
    return ""

# ----------------- 텍스트 후처리 -----------------
_BULLETS = r'\-\–\—·•‣◦▶'  # 제거 대상 불릿/화살표

def drop_bullet_artifacts(text: str) -> str:
    # 단독 불릿/화살표 라인 제거
    text = re.sub(rf'(^|\n)\s*[{_BULLETS}]\s*(?=\n|$)', r'\1', text)
    # 개행 사이 불릿 제거
    text = re.sub(rf'\n\s*[{_BULLETS}]\s*\n', '\n', text)
    return text

def drop_bracket_link_lines(text: str) -> str:
    # [ ... ] 한 줄짜리 링크 홍보 라인 제거
    return re.sub(r'(^|\n)\s*\[.*?\]\s*(?=\n|$)', r'\1', text, flags=re.M)

def drop_http_only_lines(text: str) -> str:
    # http/https만 있는 라인 제거
    return re.sub(r'(^|\n)\s*https?://\S+\s*(?=\n|$)', r'\1', text, flags=re.M)

def drop_trailing_reporter_block(text: str) -> str:
    """
    'XXX 기자 ***@***' 라인 발견 시, 그 라인부터 문서 끝까지 제거.
    (이메일이 같은 줄/다음 줄에 있어도 컷)
    """
    email_re = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
    lines = text.split('\n')
    cut_idx = None
    for i, line in enumerate(lines):
        if '기자' in line:
            if email_re.search(line) or (i + 1 < len(lines) and email_re.search(lines[i + 1])):
                cut_idx = i
                break
    if cut_idx is not None:
        return '\n'.join(lines[:cut_idx]).rstrip()
    return text

def clean_text(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = drop_bullet_artifacts(t)
    t = drop_bracket_link_lines(t)
    t = drop_http_only_lines(t)
    t = re.sub(r"\n{3,}", "\n\n", t)      # 과다 개행 축소
    t = drop_trailing_reporter_block(t)   # 기자 블럭 이후 통삭제
    return t.strip()

# ----------------- 파서 -----------------
def parse_title(soup: BeautifulSoup) -> str:
    node = soup.find(class_="viewTite")
    if node and node.get_text(strip=True):
        return node.get_text(strip=True)
    for name, cls in [
        ("h3","viewTtitle"), ("h3","viewT"),
        ("h3","articleSubject"), ("div","subject"),
        ("h1",None), ("h2",None)
    ]:
        node2 = soup.find(name, class_=cls) if cls else soup.find(name)
        if node2 and node2.get_text(strip=True):
            return node2.get_text(strip=True)
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""

def parse_content(soup: BeautifulSoup, page_url: str = "") -> str:
    """
    본문 추출:
    - 기본: .content_view
    - 실패 시: 스포츠/외부매체 폴백 셀렉터
    - 그래도 없으면 iframe 추적
    """
    # 1) 기본(.content_view)
    container = soup.find(class_="content_view")
    if container:
        remove_unwanted_in_scope(container)
        txt = container.get_text(separator="\n")
        return clean_text(txt)

    # 2) 폴백 셀렉터 시도
    container = pick_largest_text_node(soup, SPORTS_FALLBACK_SELECTORS)
    if container:
        remove_unwanted_in_scope(container)
        txt = container.get_text(separator="\n")
        cleaned = clean_text(txt)
        if cleaned:
            return cleaned

    # 3) iframe 따라가기
    if page_url:
        iframe_txt = try_follow_iframe(soup, page_url)
        if iframe_txt:
            return iframe_txt

    return ""

# ----------------- 멀티스레드 파이프라인 -----------------
def enrich_row(index_and_row: Tuple[int, Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    """
    (index, row) → (index, enriched_row)
    """
    idx, row = index_and_row
    href = (row.get("href") or "").strip()

    if not href:
        row["title"] = ""
        row["contet"] = ""
        return idx, row

    html = fetch_html(href)
    if not html:
        row["title"] = ""
        row["contet"] = ""
        return idx, row

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    row["title"]  = parse_title(soup)
    row["contet"] = parse_content(soup, page_url=href)
    return idx, row

# ----------------- main -----------------
def main() -> None:
    base = Path(".").resolve()
    in_path = base / INPUT_CSV
    out_path = base / OUTPUT_CSV

    # 입력 CSV 로드
    df = pd.read_csv(in_path, dtype=str).fillna("")

    # href 중복 제거
    if "href" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["href"], keep="first")
        after = len(df)
        print(f"[Dedup] href: {before} -> {after}")

    # dict 리스트 변환 + 인덱스 부여(출력 순서 유지)
    items = list(df.to_dict(orient="records"))
    indexed_items = list(enumerate(items, 1))  # (1-based index, row)

    results_by_idx: Dict[int, Dict[str, Any]] = {}

    # 멀티스레드: 10개씩 배치 처리
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for start in range(0, len(indexed_items), BATCH_SIZE):
            batch = indexed_items[start:start + BATCH_SIZE]
            futures = [ex.submit(enrich_row, pair) for pair in batch]

            for fut in cf.as_completed(futures):
                idx, enriched = fut.result()
                results_by_idx[idx] = enriched

            print(f"[Batch] {start + 1} ~ {min(start + BATCH_SIZE, len(indexed_items))} done")

    # 인덱스 순서대로 결과 정렬
    ordered_results = [results_by_idx[i] for i in sorted(results_by_idx.keys())]

    # 결과 저장 (원본 컬럼 + title + contet)
    fieldnames = list(df.columns)
    for new_col in ["title", "contet"]:
        if new_col not in fieldnames:
            fieldnames.append(new_col)

    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in ordered_results:
            writer.writerow(r)

    print(f"✅ 완료: {out_path} (rows={len(ordered_results)})")


if __name__ == "__main__":
    main()
