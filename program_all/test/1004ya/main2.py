# -*- coding: utf-8 -*-
"""
Naviya 파서 (p-태그 기반 영업시간 + 프로그램)
- 영업시간: p 태그에서 (오전|오후|낮|밤|새벽)+시각 토큰만 모아 '첫 2개'로 HH:MM ~ HH:MM 출력
- '영업시간' 헤더 이후부터 수집, '오시는길/공지/공지안내/공지사항' 나오면 중지
- 24시간 → 00:00 ~ 24:00
- 프로그램: 한 줄에 '분'+'만' 동시 포함된 줄만 파싱 (제목 없으면 A코스, 시간 없으면 60분, 여러 가격이면 마지막, 타이틀당 대표 1개)
"""
import re
import json
import time
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# ======================= 설정 =======================
BASE_URL = "https://www.naviya.net/bbs/board.php?bo_table=b49&wr_id={wr_id}"

WR_ID_LIST = ["10218",
              "11314",
              "11835",
              "12234",
              "12500",
              "13422",
              "13944",
              "14043",
              "14053",
              "14653",
              "14754",
              "14871",
              "15130",
              "15213",
              "15427",
              "15585",
              "16602",
              "16780",
              "17128",
              "17681",
              "18301",
              "18358",
              "18441",
              "18462",
              "18675",
              "18744",
              "18943",
              "19071",
              "19369",
              "19550",
              "19648",
              "19802",
              "20029",
              "20074",
              "20092",
              "20139",
              "20520",
              "20765",
              "20865",
              "21008",
              "21023",
              "21228",
              "21231",
              "21324",
              "21442",
              "21523",
              "21610",
              "21678",
              "21689",
              "21907",
              "21915",
              "22012",
              "22054",
              "22147",
              "22218",
              "22249",
              "22278",
              "22361",
              "22396",
              "22538",
              "22653",
              "22707",
              "22710",
              "22719",
              "22735",
              "22873",
              "22966",
              "23101",
              "23232",
              "23259",
              "23273",
              "23328",
              "23341",
              "23423",
              "23440",
              "23557",
              "23593",
              "23674",
              "23748",
              "23841",
              "23885",
              "23980",
              "23981",
              "24050",
              "24110",
              "24158",
              "24242",
              "24252",
              "24327",
              "24383",
              "24390",
              "24419",
              "24434",
              "24468",
              "24483",
              "24498",
              "24530",
              "24553",
              "24576",
              "24578",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
    "Accept-Language": "ko,en;q=0.8",
    "Referer": "https://www.naviya.net/",
}

REQUEST_TIMEOUT = 12
SLEEP_BETWEEN_REQ = 0.2
PRICE_PICK = "last"  # "last"=할인가 선호, "first"=첫 가격 사용

# ============== 정규화 유틸 ==============
# 주의: ~ 는 유지(시간 파서가 쓸 수도 있음)
ARROWS_RE   = re.compile(r"[➙➛➝➞➟➠➢➣➤➥➦➧➨➳➵➸→⇒⟶⟹⟿➔➚➘➙➼➽➷➺➻]+")
# []는 [A] 인식, ~ 는 시간 분리용 → 제거하지 않음
DECOR_RE    = re.compile(r"[✿✻❥❖✣✱❉•·｡☾☽_=·\—–│┃▭■◆●▶▷◀◁❖❁❀★☆♡♥◆◇■□〈〉“”\"'`、·…·°•˚•🄌ⓐⓑⓒⓥ•➖╳×]+")
DASHES_RE   = re.compile(r"[|｜\-─━＿_]+")
DUPSPACE_RE = re.compile(r"\s{2,}")

def _unify_tilde(s: str) -> str:
    return s.replace("∼", "~").replace("〜", "~")

def normalize_line(s: str) -> str:
    if not s:
        return ""
    t = _unify_tilde(s)
    t = (t.replace("\xa0", " ").replace("\u200b", "")
         .replace("\u200c", "").replace("\u200d", "")
         .replace("\u2060", "").strip())
    # 화살표/장식 제거(단, ~ 및 []는 유지)
    t = ARROWS_RE.sub(" ", t)
    t = DECOR_RE.sub(" ", t)
    t = DASHES_RE.sub(" ", t)
    # "0 60분" → "060분"
    t = re.sub(r"(\d)\s+(\d)", r"\1\2", t)
    t = DUPSPACE_RE.sub(" ", t).strip()
    return t

def compact(s: str) -> str:
    return re.sub(r"\s+", "", s or "")

# ==================== 영업시간(p-태그 전용) ====================
# '오전/오후/낮/밤/새벽'이 반드시 포함된 토큰만 인정
STRICT_TIME_TOKEN_RE = re.compile(r"(오전|오후|낮|밤|새벽)\s*(\d{1,2})(?:\s*[:시]\s*(\d{1,2}))?")

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
    elif p == "밤":
        if h == 12: h = 0
        elif 1 <= h <= 6: h = h
        else: h += 12
    elif p == "새벽":
        if h == 12: h = 0
        else: h = h

    return max(0, min(24, h)), m


# ==================== 프로그램 파싱 ====================
def extract_prices(line: str) -> List[int]:
    nums = re.findall(r"(\d{1,3})\s*만", line)
    return [int(n) * 10000 for n in nums] if nums else []

def extract_duration(line: str) -> Optional[str]:
    cands = re.findall(r"(\d{1,3})\s*분", line)
    if not cands:
        return None
    return f"{int(cands[-1])}분"

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
    text_block = root.get_text("\n", strip=True)  # <br> 포함 개행
    raw_lines = [ln for ln in text_block.split("\n") if ln is not None]
    lines = [normalize_line(ln) for ln in raw_lines]
    return [ln for ln in lines if ln]

# ==================== 메인 파서 ====================
def extract_items_from_lines(lines: List[str]) -> List[Dict]:
    """프로그램 파싱 (영업시간 절단과 무관하게 라인 기반 처리)"""
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
            continue  # 대표 1개만
        results.append({
            "title": title,
            "duration": duration,
            "categories": "",
            "original_price": "",
            "discount_price": price
        })
        taken.add(title)

    return results

def extract_business_hours_from_html(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("#clip_board_view")
    return _pcollect_first_two_times(root) if root else None


# --- 유틸: 24시간 문구 판별 ---
def is_24h_line(line: str) -> bool:
    """
    '24시간 영업', '24시간', '24시', '연중무휴' 가 들어있으면 24시간으로 간주.
    (공백/장식 제거한 compact 문자열 기준)
    """
    c = compact(line)
    return ("24시간영업" in c) or ("24시간" in c) or ("24시" in c) or ("연중무휴" in c)


# --- p태그 기반: 영업시간 첫 2개 토큰 수집 / 24시간 처리 ---
def _pcollect_first_two_times(root: BeautifulSoup) -> Optional[str]:
    """
    #clip_board_view 내부 p 태그만 보고:
      - '영업시간' 헤더 등장 이후에
      - p 텍스트에 (오전|오후|낮|밤|새벽)+시각 토큰이 있는 p만 수집
      - 토큰을 문서 순서대로 모아 '최초 2개'를 24시간제로 변환하여 'HH:MM ~ HH:MM'
      - '오시는길/공지/공지안내/공지사항' p를 만나면 중지
      - '24시간 영업' / '24시간' / '24시' / '연중무휴' 를 만나면 즉시 '00:00 ~ 24:00' 리턴
    """
    if not root:
        return None

    seen_hours = False
    times: List[Tuple[int,int]] = []

    for p in root.find_all("p"):
        raw = p.get_text(separator=" ", strip=True)
        if not raw:
            continue
        line = normalize_line(raw)
        c = compact(line)

        # '영업시간' 헤더 찾기 (장식/공백 섞여도 인식)
        if not seen_hours:
            if "영업시간" in c:
                seen_hours = True
            else:
                continue  # 헤더 전은 무시

        # 헤더 이후: 종료 키워드 만나면 중지
        if any(key in c for key in ("오시는길", "공지안내", "공지사항", "공지")):
            break

        # ⬇️ 24시간 문구 즉시 처리
        if is_24h_line(line):
            return "00:00 ~ 24:00"

        # (오전|오후|낮|밤|새벽) + 시각 토큰 수집
        for m in STRICT_TIME_TOKEN_RE.finditer(line):
            period = m.group(1)
            hour   = int(m.group(2))
            minute = int(m.group(3) or 0)
            h, mi  = _kor_time_to_24h(period, hour, minute)
            times.append((h, mi))
            if len(times) >= 2:
                start = _fmt_hm(*times[0])
                end   = _fmt_hm(*times[1])
                return f"{start} ~ {end}"

    # 2개 미만이면 실패
    return None

# ==================== 실행부 ====================
def main():
    for wr_id in WR_ID_LIST:
        html  = fetch_html(wr_id)

        # 영업시간: p-태그 기반
        biz_hours = extract_business_hours_from_html(html) if html else None

        # 프로그램: 라인 기반(필요 시 p-기반으로도 바꿀 수 있음)
        lines = html_to_lines(html) if html else []
        items = extract_items_from_lines(lines) if lines else []

        print(f"id : N_{wr_id}")
        print(f"business_hours : {biz_hours or ''}")   # 예: '13:00 ~ 02:00'
        print("array :")
        print(json.dumps(items, ensure_ascii=False, indent=4))
        print()
        time.sleep(SLEEP_BETWEEN_REQ)

if __name__ == "__main__":
    main()
