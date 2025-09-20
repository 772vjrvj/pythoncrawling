# -*- coding: utf-8 -*-
"""
Naviya 파서 최종판
- clip_board_view의 모든 <p> 태그 텍스트를 배열로: SHOP_INTRO_NEW_ONE
  * 공백 p도 ""로 보존
- SHOP_INTRO_NEW_TWO: 위 배열을 <br>로 이어 하나의 문자열로 (빈 요소도 <br> 생성)
- BUSINESS_HOUR: p태그만 기준으로 '영업시간' 이후 시각 토큰을 처음 2개 찾아 'HH:MM ~ HH:MM'
  * (오전|오후|낮|밤|새벽) + 시
  * '24시간 영업' / '24시간' / '24시' / '연중무휴' → 00:00 ~ 24:00
  * '오시는길/공지/공지안내/공지사항' p를 만나면 탐색 중지
- PROGRAM: 한 줄에 '분'과 '만'이 함께 있는 줄만 파싱
  * 제목 없으면 A코스, 시간 없으면 60분, 여러 가격이면 마지막(할인가), 타이틀당 대표 1개
- 결과를 CSV(result.csv)로 저장 (UTF-8-SIG, Excel 호환):
  컬럼: SHOP_ID, BUSINESS_HOUR, CLOSED_DAY, PROGRAM(JSON), SHOP_INTRO_NEW_ONE(JSON), SHOP_INTRO_NEW_TWO
"""

import re
import json
import csv
import time
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# ======================= 설정 =======================
BASE_URL = "https://www.naviya.net/bbs/board.php?bo_table=b49&wr_id={wr_id}"

WR_ID_LIST = [
    "10218", "11314", "11835", "12234", "12500", "13422", "13944",
    # 필요 시 더 추가
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
    "Accept-Language": "ko,en;q=0.8",
    "Referer": "https://www.naviya.net/",
}

REQUEST_TIMEOUT = 12
SLEEP_BETWEEN_REQ = 0.2
PRICE_PICK = "last"  # "last"=할인가 선택, "first"=첫 가격 선택
RESULT_CSV = "result.csv"

# ============== 공통 정규화 유틸 ==============
# 주의: ~ 는 절대 제거하지 않음 (시간 구분자로 사용)
ARROWS_RE   = re.compile(r"[➙➛➝➞➟➠➢➣➤➥➦➧➨➳➵➸→⇒⟶⟹⟿➔➚➘➙➼➽➷➺➻]+")
# []는 [A] 인식에 필요. ~ 도 유지.
DECOR_RE    = re.compile(r"[✿✻❥❖✣✱❉•·｡☾☽_=·\—–│┃▭■◆●▶▷◀◁❖❁❀★☆♡♥◆◇■□〈〉“”\"'`、·…·°•˚•🄌ⓐⓑⓒⓥ•➖╳×]+")
DASHES_RE   = re.compile(r"[|｜\-─━＿_]+")
DUPSPACE_RE = re.compile(r"\s{2,}")

def _unify_tilde(s: str) -> str:
    return s.replace("∼", "~").replace("〜", "~")

def normalize_line(s: str) -> str:
    """프로그램/영업시간 라인 파싱용(장식 제거)"""
    if not s:
        return ""
    t = _unify_tilde(s)
    t = (t.replace("\xa0", " ")
         .replace("\u200b", "")
         .replace("\u200c", "")
         .replace("\u200d", "")
         .replace("\u2060", "")
         .strip())
    # ~ 는 유지
    t = ARROWS_RE.sub(" ", t)
    t = DECOR_RE.sub(" ", t)
    t = DASHES_RE.sub(" ", t)
    # "0 60분" → "060분"
    t = re.sub(r"(\d)\s+(\d)", r"\1\2", t)
    t = DUPSPACE_RE.sub(" ", t).strip()
    return t

def compact(s: str) -> str:
    """공백 제거 비교용"""
    return re.sub(r"\s+", "", s or "")

# ============== HTML ==============
def fetch_html(wr_id: str) -> Optional[str]:
    url = BASE_URL.format(wr_id=wr_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception as e:
        print(f"[warn] 요청 실패 wr_id={wr_id}: {e}")
        return None

def get_clip_root(html: str) -> Optional[BeautifulSoup]:
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one("#clip_board_view")

# ============== SHOP_INTRO (p 배열/문자열) ==============
def p_text_array(root: BeautifulSoup) -> List[str]:
    """
    모든 p 태그의 '보이는 텍스트'를 배열로.
    - strip=True로 양끝 공백 제거 → 공백 p는 ""로 들어감
    - NBSP/제로폭문자는 제거
    - 장식문자/화살표는 제거하지 않음(실제 화면에 보이는 텍스트 최대한 보존)
    """
    arr: List[str] = []
    for p in root.find_all("p"):
        raw = p.get_text(separator=" ", strip=True)
        t = (raw.replace("\xa0", " ")
             .replace("\u200b", "")
             .replace("\u200c", "")
             .replace("\u200d", "")
             .replace("\u2060", ""))
        # 그대로 보존 (빈 p는 "")
        arr.append(t)
    return arr

def intro_two_from_array(intros: List[str]) -> str:
    """
    배열을 HTML 표기처럼 '<br>'로 이어 단일 문자열 생성.
    빈 문자열도 그대로 이어서 빈 줄 유지.
    """
    return "<br>".join(intros)

# ============== 영업시간 (p 전용, 첫 2토큰) ==============
STRICT_TIME_TOKEN_RE = re.compile(r"(오전|오후|낮|밤|새벽)\s*(\d{1,2})(?:\s*[:시]\s*(\d{1,2}))?")

def _fmt_hm(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"

def _kor_time_to_24h(period: Optional[str], hour: int, minute: int = 0) -> Tuple[int, int]:
    """
    한글 시각 → 24시간제
    - 오전: 12→0
    - 오후: 1~11→+12, 12→12
    - 낮 : 1~6→+12, 12→12
    - 밤 : 12→0, 1~6→그대로, 7~11→+12
    - 새벽: 12→0, 1~11→그대로
    """
    p = (period or "").strip()
    h = max(0, min(24, hour))
    m = 0 if minute is None else max(0, min(59, minute))

    if p == "오전":
        if h == 12: h = 0
    elif p == "오후":
        if h != 12: h += 12
    elif p == "낮":
        if h == 12: h = 12
        elif 1 <= h <= 6: h += 12
    elif p == "밤":
        if h == 12: h = 0
        elif 1 <= h <= 6: h = h
        else: h += 12
    elif p == "새벽":
        if h == 12: h = 0
        else: h = h

    return max(0, min(24, h)), m

def is_24h_line(line: str) -> bool:
    """
    '24시간 영업', '24시간', '24시', '연중무휴' 포함 시 24시간으로 간주.
    """
    c = compact(line)
    return ("24시간영업" in c) or ("24시간" in c) or ("24시" in c) or ("연중무휴" in c)

def extract_business_hours_p_only(root: BeautifulSoup) -> Optional[str]:
    """
    p 태그만 보고:
      - '영업시간' 헤더 이후
      - (오전|오후|낮|밤|새벽)+시각 토큰을 가진 p에서 토큰을 순서대로 수집
      - 처음 2개의 토큰으로 'HH:MM ~ HH:MM' 반환
      - '24시간/24시/연중무휴' 만나면 즉시 '00:00 ~ 24:00'
      - '오시는길/공지/공지안내/공지사항' 만나면 탐색 중단
    """
    if not root:
        return None

    seen_hours = False
    times: List[Tuple[int, int]] = []

    for p in root.find_all("p"):
        raw = p.get_text(separator=" ", strip=True)
        if raw is None:
            continue
        # intro용과 달리, 시간 파싱은 normalize를 약하게만 적용
        line = normalize_line(raw)
        c = compact(line)

        if not seen_hours:
            if "영업시간" in c:
                seen_hours = True
            else:
                continue

        if any(key in c for key in ("오시는길", "공지안내", "공지사항", "공지")):
            break

        if is_24h_line(line):
            return "00:00 ~ 24:00"

        for m in STRICT_TIME_TOKEN_RE.finditer(line):
            period = m.group(1)
            hour   = int(m.group(2))
            minute = int(m.group(3) or 0)
            h, mi  = _kor_time_to_24h(period, hour, minute)
            times.append((h, mi))
            if len(times) >= 2:
                return f"{_fmt_hm(*times[0])} ~ {_fmt_hm(*times[1])}"

    return None

# ============== PROGRAM 파싱 (라인 기반) ==============
def extract_prices(line: str) -> List[int]:
    nums = re.findall(r"(\d{1,3})\s*만", line)
    return [int(n) * 10000 for n in nums] if nums else []

def extract_duration(line: str) -> Optional[str]:
    cands = re.findall(r"(\d{1,3})\s*분", line)
    if not cands:
        return None
    return f"{int(cands[-1])}분"  # 마지막 '분'을 시간으로

def ensure_duration(line: str) -> str:
    d = extract_duration(line)
    return d if d else "60분"

def _ensure_kose(name: str) -> str:
    return name if name.endswith("코스") else f"{name}코스"

def extract_title(line: str) -> Optional[str]:
    # VIP / V
    if re.search(r"\bVIP\b", line, re.I) or re.search(r"\bV\b", line):
        return "VIP코스"
    # [A]
    m = re.search(r"\[\s*([A-Da-d])\s*\]", line)
    if m:
        return f"{m.group(1).upper()}코스"
    # A. / A:
    m = re.search(r"\b([A-Da-d])\s*[.:]", line)
    if m:
        return f"{m.group(1).upper()}코스"
    # A-1
    m = re.search(r"\b([A-Da-d])\s*-\s*\d+\b", line)
    if m:
        return f"{m.group(1).upper()}코스"
    # A 코스 / A코스
    m = re.search(r"\b([A-Da-d])\s*코\s*스\b", line)
    if m:
        return f"{m.group(1).upper()}코스"
    # 일반명 코스 (단일코스, 패키지1 등)
    m = re.search(r"([A-Za-z가-힣0-9]+)\s*코\s*스\b", line)
    if m:
        name = m.group(1).strip()
        if len(name) == 1 and name.isalpha():
            return f"{name.upper()}코스"
        return _ensure_kose(name)
    # duration 앞의 텍스트를 제목으로
    d = re.search(r"\d{1,3}\s*분", line)
    if d:
        prefix = line[:d.start()].strip()
        prefix = re.sub(r"^[\(\[]|[\)\]]$", "", prefix).strip()
        if prefix and prefix not in ("주", "야", "상담가능"):
            return _ensure_kose(prefix) if not prefix.endswith("코스") else prefix
    return None

def decide_title(line: str) -> str:
    t = extract_title(line)
    return t if t else "A코스"

def is_price_line(line: str) -> bool:
    return bool(re.search(r"\d{1,3}\s*만", line))

def html_to_lines_for_program(root: BeautifulSoup) -> List[str]:
    """프로그램 파싱용 라인 배열 (#clip_board_view 전체 텍스트를 줄 단위로)"""
    text_block = root.get_text("\n", strip=True)
    raw_lines = text_block.split("\n")
    lines = [normalize_line(ln) for ln in raw_lines if ln is not None]
    return [ln for ln in lines if ln]

def extract_program_items(root: BeautifulSoup) -> List[Dict]:
    lines = html_to_lines_for_program(root)
    results: List[Dict] = []
    taken = set()
    for line in lines:
        if not is_price_line(line):
            continue
        prices = extract_prices(line)
        if not prices:
            continue
        price = prices[-1] if PRICE_PICK == "last" else prices[0]
        title    = decide_title(line)
        duration = ensure_duration(line)
        if title in taken:
            continue
        results.append({
            "title": title,
            "duration": duration,
            "categories": "",
            "original_price": "",
            "discount_price": price,
        })
        taken.add(title)
    return results

# ============== CSV 저장 ==============
def save_to_csv(rows: List[Dict], path: str = RESULT_CSV):
    """
    rows: [{SHOP_ID, BUSINESS_HOUR, CLOSED_DAY, PROGRAM(list), SHOP_INTRO_NEW_ONE(list), SHOP_INTRO_NEW_TWO(str)}, ...]
    PROGRAM / SHOP_INTRO_NEW_ONE 은 JSON 문자열로 직렬화해서 저장
    """
    fieldnames = ["SHOP_ID", "BUSINESS_HOUR", "CLOSED_DAY", "PROGRAM", "SHOP_INTRO_NEW_ONE", "SHOP_INTRO_NEW_TWO"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "SHOP_ID": r.get("SHOP_ID", ""),
                "BUSINESS_HOUR": r.get("BUSINESS_HOUR", ""),
                "CLOSED_DAY": r.get("CLOSED_DAY", ""),
                "PROGRAM": json.dumps(r.get("PROGRAM", []), ensure_ascii=False),
                "SHOP_INTRO_NEW_ONE": json.dumps(r.get("SHOP_INTRO_NEW_ONE", []), ensure_ascii=False),
                "SHOP_INTRO_NEW_TWO": r.get("SHOP_INTRO_NEW_TWO", ""),
            })

# ============== 실행부 ==============
def main():
    out_rows: List[Dict] = []

    for wr_id in WR_ID_LIST:
        html = fetch_html(wr_id)
        if not html:
            # 실패 시에도 빈 구조로 라인 확보
            out_rows.append({
                "SHOP_ID": f"N_{wr_id}",
                "BUSINESS_HOUR": "",
                "CLOSED_DAY": "연중무휴(전화문의)",
                "PROGRAM": [],
                "SHOP_INTRO_NEW_ONE": [],
                "SHOP_INTRO_NEW_TWO": "",
            })
            continue

        root = get_clip_root(html)
        if not root:
            out_rows.append({
                "SHOP_ID": f"N_{wr_id}",
                "BUSINESS_HOUR": "",
                "CLOSED_DAY": "연중무휴(전화문의)",
                "PROGRAM": [],
                "SHOP_INTRO_NEW_ONE": [],
                "SHOP_INTRO_NEW_TWO": "",
            })
            continue

        # SHOP_INTRO
        intro_one = p_text_array(root)                 # 모든 p 텍스트 (빈 p는 "")
        intro_two = intro_two_from_array(intro_one)    # "<br>"로 이어진 문자열

        # BUSINESS_HOUR (p-only)
        business_hour = extract_business_hours_p_only(root) or ""

        # PROGRAM
        programs = extract_program_items(root)

        obj = {
            "SHOP_ID": f"N_{wr_id}",
            "BUSINESS_HOUR": business_hour,
            "CLOSED_DAY": "연중무휴(전화문의)",  # 하드코딩
            "PROGRAM": programs,
            "SHOP_INTRO_NEW_ONE": intro_one,
            "SHOP_INTRO_NEW_TWO": intro_two,
        }
        out_rows.append(obj)

        # (원하면 콘솔 확인)
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        print()
        time.sleep(SLEEP_BETWEEN_REQ)

    save_to_csv(out_rows, RESULT_CSV)
    print(f"[ok] CSV 저장 완료: {RESULT_CSV}")

if __name__ == "__main__":
    main()
