import requests
import json
import time
from bs4 import BeautifulSoup
import openpyxl
from datetime import datetime
import re
import os
import csv

BASE_API = "https://m.cafe.daum.net/api/v1/common-articles"
BASE_VIEW = "https://cafe.daum.net/odin"
GRPID = "1YvZ5"
PAGE_SIZE = 50
STOP_DATE = "23.08.11"  # 발견 시 종료
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}
TODAY_STR = datetime.today().strftime("%y.%m.%d")

# CSV 저장 단위(개)
CSV_CHUNK_SIZE = 100

# ─────────────────────────────────────────────────────────────
# Excel 불법 제어문자 제거 (openpyxl IllegalCharacterError 대응)
# 허용: \t, \n, \r / 제거: 그 외 0x00-0x1F
ILLEGAL_CTRL_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')

def clean_text(value) -> str:
    """엑셀이 허용하지 않는 제어문자 제거"""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return ILLEGAL_CTRL_RE.sub("", value)
# ─────────────────────────────────────────────────────────────

# 공통 헤더
HEADERS_ROW = ["게시판", "작성 날짜", "게시글 제목", "게시글 내용", "url", "id"]

# ----------- API 요청 -----------
def fetch_page(fldid, page_num, after=None):
    params = {
        "grpid": GRPID,
        "fldid": fldid,
        "pageSize": PAGE_SIZE,
        "targetPage": page_num
    }
    if after:
        params["afterBbsDepth"] = after

    r = requests.get(BASE_API, params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

# ----------- 수집 -----------
def collect_articles(fldid):
    all_data = []
    after_cursor = None
    page_num = 1

    while True:
        data = fetch_page(fldid, page_num, after_cursor)
        articles = data.get("articles", [])

        if not articles:
            print(f"📌 [{fldid}] 더 이상 데이터 없음. 종료")
            break

        last_date = articles[-1].get("articleElapsedTime", "N/A")

        for article in articles:
            if article.get("articleElapsedTime") == STOP_DATE:
                print(f"📌 [{fldid}] {STOP_DATE} 발견 → 수집 종료")
                return all_data
            all_data.append(article)

        print(f"[{fldid} | Page {page_num}] {len(articles)}건 수집 / 누적 {len(all_data)}건 / 마지막 날짜 {last_date}")

        after_cursor = articles[-1].get("bbsDepth")
        if not after_cursor:
            print(f"📌 [{fldid}] 다음 커서 없음. 종료")
            break

        page_num += 1
        time.sleep(0.3)

    return all_data

# ----------- HTML 파싱 -----------
def parse_article_content(fldid, dataid):
    url = f"https://m.cafe.daum.net/odin/{fldid}/{dataid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Mobile Safari/537.36",
        "Referer": f"https://m.cafe.daum.net/odin/{fldid}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ [{fldid}] {dataid} 요청 실패: {e}")
        return ""

    soup = BeautifulSoup(res.text, "html.parser")

    # 1) 기본: id="article" 안의 <p> 태그들
    article_div = soup.find("div", id="article", class_="tx-content-container")
    paragraphs = []
    if article_div:
        for p in article_div.find_all("p"):
            for br in p.find_all("br"):
                br.replace_with("\n")
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

    # 2) <p>가 없거나 내용이 비었을 때 → id="protectTable" 안의 text 사용
    if not paragraphs:
        protect_div = soup.find(id="protectTable")
        if protect_div:
            text = protect_div.get_text(strip=True)
            if text:
                paragraphs.append(text)

    return "\n".join(paragraphs)

# ----------- CSV 유틸 -----------
def get_out_paths(board_name: str):
    """현재 작업 폴더 기준으로 JSON/CSV/XLSX 파일 경로 반환"""
    json_path = os.path.abspath(f"odin_{board_name}.json")
    base_dir = os.path.dirname(json_path)
    csv_path  = os.path.join(base_dir, f"odin_{board_name}.csv")
    xlsx_path = os.path.join(base_dir, f"odin_{board_name}.xlsx")
    return json_path, csv_path, xlsx_path

def ensure_csv_header(csv_path: str):
    """CSV 파일이 없으면 헤더 생성"""
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(HEADERS_ROW)
        print(f"🧾 CSV 헤더 생성: {csv_path}")

def append_rows(csv_path: str, rows: list):
    """rows를 CSV에 append (이미 sanitize된 값 사용 권장)"""
    if not rows:
        return
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerows(rows)
    print(f"💾 CSV append 저장: +{len(rows)} rows → {csv_path}")

def row_from_item(board_name: str, fldid: str, item: dict) -> list:
    """API 아이템을 CSV 1행으로 변환 + sanitize"""
    date_str = item.get("articleElapsedTime", "") or ""
    if ("분 전" in date_str) or ("시간 전" in date_str) or ("초 전" in date_str):
        date_str = TODAY_STR

    title   = item.get("title", "") or ""
    content = item.get("content", "") or ""
    dataid  = str(item.get("dataid", "") or "")
    url     = f"{BASE_VIEW}/{fldid}/{dataid}" if dataid else ""

    row = [
        board_name,
        date_str,
        title,
        content,
        url,
        dataid
    ]
    # sanitize
    return [clean_text(v) for v in row]

# ----------- CSV → XLSX 변환 -----------
def csv_to_xlsx(csv_path: str, xlsx_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Articles"

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            # XLSX 쓰기 전에 추가 sanitize
            safe_row = [clean_text(c) for c in row]
            ws.append(safe_row)

    wb.save(xlsx_path)
    print(f"✅ 최종 엑셀 저장 완료 → {xlsx_path}")

# ----------- 메인 실행 -----------
def run_for_board(board_name, fldid):
    print(f"\n===== [{board_name}] 수집 시작 =====")
    json_path, csv_path, xlsx_path = get_out_paths(board_name)

    # 1. JSON 수집 저장
    articles = collect_articles(fldid)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 저장 완료 → {json_path}")

    # 2. CSV 준비(헤더)
    ensure_csv_header(csv_path)

    # 3. 상세 페이지 파싱 + 100개마다 CSV append
    buffer = []
    total = len(articles)
    for idx, art in enumerate(articles, 1):
        dataid = art.get("dataid")
        if not dataid:
            continue

        content = parse_article_content(fldid, dataid)
        art["content"] = content

        buffer.append(row_from_item(board_name, fldid, art))

        # 100개 단위로 저장
        if len(buffer) == CSV_CHUNK_SIZE:
            append_rows(csv_path, buffer)
            buffer = []

        print(f"[{board_name}] detail {idx}/{total} dataid={dataid} ✅")
        time.sleep(0.15)  # 서버 부하 방지

    # 남은 데이터 저장
    if buffer:
        append_rows(csv_path, buffer)

    # 4. CSV → XLSX 변환
    csv_to_xlsx(csv_path, xlsx_path)

    print(f"🎉 [{board_name}] 전체 완료")

if __name__ == "__main__":
    # 자유게시판
    # run_for_board("자유게시판", "D034")

    # 오딘 광장
    run_for_board("오딘광장", "DjO0")
