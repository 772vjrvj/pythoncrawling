import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Tuple

NUM_RE = re.compile(r"\d+")

def _digits_or_none(val) -> Optional[str]:
    """숫자만 추출해서 문자열로 반환 (없으면 None). 예: '296,414' -> '296414'"""
    if val is None:
        return None
    s = "".join(NUM_RE.findall(str(val)))
    return s if s else None

def get_view_and_review(wr_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    VIEW_COUNT: 상세 페이지의 <div class="extra"> 안 첫 번째 <span>
    REVIEW_COUNT: rev.php AJAX(JSON)의 result_data.total
    반환값은 '296414' 같은 숫자문자열(쉼표 제거) 또는 None
    """
    base_detail = f"https://vipgunma.com/bbs/board.php?bo_table=gm_1&wr_id={wr_id}"
    ajax_url = "https://vipgunma.com/bbs/rev.php"

    # 공통 세션 & 헤더 (최소)
    s = requests.Session()
    common_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    # 1) VIEW_COUNT: 상세 페이지에서 파싱
    view_count: Optional[str] = None
    resp = s.get(base_detail, headers=common_headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    spans = soup.select("div.extra span")
    if len(spans) >= 1:
        view_count = _digits_or_none(spans[0].get_text(strip=True))

    # 2) REVIEW_COUNT: rev.php AJAX JSON에서 total
    review_count: Optional[str] = None
    payload = {
        "request": "requestRev",
        "page": "1",
        "wr_id": str(wr_id),
    }
    ajax_headers = {
        **common_headers,
        "Referer": base_detail,
        "Origin": "https://vipgunma.com",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    r = s.post(ajax_url, headers=ajax_headers, data=payload, timeout=15)
    # 사이트가 JSON을 반환함 (result_code / result_data.total)
    try:
        data = r.json()
        if data.get("result_code") == "success":
            total = (data.get("result_data") or {}).get("total")
            review_count = _digits_or_none(total)
    except ValueError:
        # JSON이 아닐 경우(변경 대비) None 유지
        pass

    return view_count, review_count


if __name__ == "__main__":
    v, r = get_view_and_review("48971")
    print("VIEW_COUNT:", v)
    print("REVIEW_COUNT:", r)
