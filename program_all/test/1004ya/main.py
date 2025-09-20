# -*- coding: utf-8 -*-
"""
Naviya 페이지 파서 (영업시간 + 프로그램) - FIX: ~ 제거하지 않도록 수정
- #clip_board_view 전체 텍스트를 줄 단위로 스캔(br/span 혼합 대응)
- 영업시간: HH:MM ~ HH:MM 으로 정규화, 24시간 → 00:00 ~ 24:00
- '영업시간' 이후 '오시는길/공지/공지안내/공지사항' 나오면 전체 파싱 중지
- 프로그램: 한 줄에 '분'+'만'이 동시에 있는 줄만 파싱
  * 제목 없으면 A코스, 시간 없으면 60분, 가격 여러 개면 마지막(할인) 사용
"""
import re
import json
import time
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# ======================= 설정 =======================
BASE_URL = "https://www.naviya.net/bbs/board.php?bo_table=b49&wr_id={wr_id}"

WR_ID_LIST = [
    "10218", "11314", "11835", "12234", "12500", "13422", "13944",
    # 필요 시 wr_id 추가
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
    "Accept-Language": "ko,en;q=0.8",
    "Referer": "https://www.naviya.net/",
}

REQUEST_TIMEOUT = 12
SLEEP_BETWEEN_REQ = 0.2
PRICE_PICK = "last"  # "last"=할인가 선호, "first"=첫 가격 사용

# ============== 정규화 유틸 (장식/화살표/대시 제거) ==============
# 주의: ~ 는 절대 제거하지 않음. (시간 파싱에서 구분자로 사용)
ARROWS_RE   = re.compile(r"[➙➛➝➞➟➠➢➣➤➥➦➧➨➳➵➸→⇒⟶⟹⟿➔➚➘➙➼➽➷➺➻]+")
# 주의: [] 는 타이틀 [A] 인식에 필요하므로 제거하지 않음
DECOR_RE    = re.compile(r"[✿✻❥❖✣✱❉•·｡☾☽~_=·\—–│┃▭■◆●▶▷◀◁❖❁❀★☆♡♥◆◇■□〈〉“”\"'`、·…·°•˚•🄌ⓐⓑⓒⓥ•➖╳×]+")
# 대시/수평선 류만 제거 (틀(~)은 제외)
DASHES_RE   = re.compile(r"[|｜\-─━＿_]+")
DUPSPACE_RE = re.compile(r"\s{2,}")

def _unify_tilde(s: str) -> str:
    """유사 틸드들을 표준 '~'로 통일."""
    return s.replace("∼", "~").replace("〜", "~")

def normalize_line(s: str) -> str:
    if not s:
        return ""
    t = _unify_tilde(s)
    t = (t.replace("\xa0", " ").replace("\u200b", "")
         .replace("\u200c", "").replace("\u200d", "")
         .replace("\u2060", "").strip())
    # 화살표류/장식 제거(단, ~ 는 남김)
    t = ARROWS_RE.sub(" ", t)
    t = DECOR_RE.sub(" ", t)
    t = DASHES_RE.sub(" ", t)
    # "0 60분" → "060분"
    t = re.sub(r"(\d)\s+(\d)", r"\1\2", t)
    t = DUPSPACE_RE.sub(" ", t).strip()
    return t

def compact(s: str) -> str:
    return re.sub(r"\s+", "", s or "")

# ==================== 영업시간 파싱 ====================
TIME_TOKEN_RE = re.compile(r"(오전|오후|낮|밤|새벽)?\s*(\d{1,2})(?:\s*[:시]\s*(\d{1,2}))?")

def _fmt_hm(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"

def _kor_time_to_24h(period: Optional[str], hour: int, minute: int = 0) -> Tuple[int, int]:
    """
    한글 시각 → 24시간제
    - 오전: 12→0, 그 외 그대로
    - 오후: 12→12, 1~11→+12
    - 낮:  12→12, 1~6→+12, 7~11→그대로
    - 밤:  12→0,  1~6→그대로(01~06), 7~11→+12(19~23)
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
        else: h = h
    elif p == "밤":
        if h == 12: h = 0
        elif 1 <= h <= 6: h = h
        else: h += 12
    elif p == "새벽":
        if h == 12: h = 0
        else: h = h
    else:
        h = h

    return max(0, min(24, h)), m

def parse_time_range_from_text(line: str) -> Optional[str]:
    """
    예:
      '영업시간 낮 1시 ~ 새벽 2시' → 13:00 ~ 02:00
      '오전 11시 ~ 밤 12시'         → 11:00 ~ 00:00
      '24시간 영업'                 → 00:00 ~ 24:00
    """
    t = normalize_line(line)
    if not t:
        return None

    # 24시간
    if re.search(r"24\s*시간", t):
        return "00:00 ~ 24:00"

    # "~" 기준 파싱 (같은 줄에 '영업시간' 포함돼도 OK)
    if "~" in t:
        L, R = t.split("~", 1)
        mL = TIME_TOKEN_RE.search(L)
        mR = TIME_TOKEN_RE.search(R)
        if mL and mR:
            pL, hL, mLmin = mL.group(1), int(mL.group(2)), int(mL.group(3) or 0)
            pR, hR, mRmin = mR.group(1), int(mR.group(2)), int(mR.group(3) or 0)
            hL24, mL24 = _kor_time_to_24h(pL, hL, mLmin)
            hR24, mR24 = _kor_time_to_24h(pR, hR, mRmin)
            return f"{_fmt_hm(hL24, mL24)} ~ {_fmt_hm(hR24, mR24)}"
    return None

def extract_business_hours(lines: List[str]) -> Optional[str]:
    """
    '영업시간' 발견 후:
      1) 같은 줄에서 먼저 시간 파싱 시도
      2) 실패 시 다음 줄들에서 찾기
      3) '오시는길/공지/공지안내/공지사항' 등장 시 중단
    """
    seen_hours = False
    for ln in lines:
        c = compact(ln)
        if not seen_hours:
            if "영업시간" in c:
                got = parse_time_range_from_text(ln)
                if got:
                    return got
                seen_hours = True
            continue

        if any(key in c for key in ("오시는길", "공지안내", "공지사항", "공지")):
            break

        # 안내문은 스킵
        if any(k in c for k in ("응답없을시", "랜덤휴무", "연중무휴", "주말에도영업", "폰OFF", "예약", "카운팅")):
            continue

        got = parse_time_range_from_text(ln)
        if got:
            return got
    return None

def cut_after_hours_section(lines: List[str]) -> List[str]:
    """
    '영업시간' 이후에 '오시는길/공지/공지안내/공지사항' 등장 시 그 지점부터 전체 파싱 중지.
    """
    seen_hours = False
    for i, ln in enumerate(lines):
        c = compact(ln)
        if not seen_hours:
            if "영업시간" in c:
                seen_hours = True
            continue
        if any(key in c for key in ("오시는길", "공지안내", "공지사항", "공지")):
            return lines[:i]
    return lines

# ==================== 프로그램 파싱 ====================
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

    # duration 앞의 텍스트를 제목으로 (예: '단일코스 120분 20만➜ 15만')
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

# ==================== HTML 처리 ====================
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

def html_to_lines(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("#clip_board_view")
    if not root:
        return []
    text_block = root.get_text("\n", strip=True)  # <br> 포함 개행 처리
    raw_lines = [ln for ln in text_block.split("\n") if ln is not None]
    lines = [normalize_line(ln) for ln in raw_lines]
    return [ln for ln in lines if ln]

# ==================== 메인 파서 ====================
def extract_items_and_hours(lines: List[str]):
    # 1) 영업시간
    business_hours = extract_business_hours(lines)

    # 2) 영업시간 이후 '오시는길/공지/공지안내/공지사항'이 나오면 그 지점까지로 절단
    scoped = cut_after_hours_section(lines)

    # 3) 프로그램
    results: List[Dict] = []
    taken = set()

    for line in scoped:
        if not is_price_line(line):
            continue

        prices = extract_prices(line)
        if not prices:
            continue
        price = prices[-1] if PRICE_PICK == "last" else prices[0]

        title    = decide_title(line)
        duration = ensure_duration(line)

        if title in taken:
            continue  # 대표 1개만
        results.append({
            "title": title,
            "duration": duration,
            "categories": "",
            "original_price": "",
            "discount_price": price
        })
        taken.add(title)

    return results, business_hours

# ==================== 실행부 ====================
def main():
    for wr_id in WR_ID_LIST:
        html  = fetch_html(wr_id)
        lines = html_to_lines(html) if html else []
        items, biz_hours = extract_items_and_hours(lines) if lines else ([], None)

        print(f"id : N_{wr_id}")
        print(f"business_hours : {biz_hours or ''}")
        print("array :")
        print(json.dumps(items, ensure_ascii=False, indent=4))
        print()
        time.sleep(SLEEP_BETWEEN_REQ)

if __name__ == "__main__":
    main()
