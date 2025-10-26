import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Tuple

NUM_RE = re.compile(r"(\d[\d,]*)")  # 숫자와 쉼표 허용

def _to_int(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = NUM_RE.search(text)
    if not m:
        return None
    return int(m.group(1).replace(",", ""))

def get_gunmalove_counts(wr_id: str) -> Tuple[Optional[int], Optional[int]]:
    """
    https://www.gunmalove.com/bbs/board.php?bo_table=store&wr_id={wr_id}
    - VIEW_COUNT: <th>조회</th> 바로 다음 <td>의 숫자
    - REVIEW_COUNT: 페이지 내 <p>태그에서 '후기'와 '댓글' 문구가 포함된 곳의 숫자 합
      (예: '후기460건', '댓글 109건' -> 460 + 109 = 569)
    """
    url = f"https://www.gunmalove.com/bbs/board.php?bo_table=store&wr_id={wr_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.gunmalove.com/",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # --- VIEW_COUNT: <th>조회</th> -> 다음 <td>
    view_count: Optional[int] = None
    for th in soup.select("table th"):
        if th.get_text(strip=True) == "조회":
            td = th.find_next_sibling("td")
            view_count = _to_int(td.get_text(strip=True) if td else None)
            break

    # --- REVIEW_COUNT: <p>들 중 '후기'와 '댓글' 문구 포함된 숫자 합
    review_total = 0
    found_any = False

    for p in soup.find_all("p"):
        txt = p.get_text(" ", strip=True)
        # '후기' 또는 '댓글' 문구가 포함된 <p>만 대상
        if ("후기" in txt) or ("댓글" in txt):
            n = _to_int(txt)
            if n is not None:
                review_total += n
                found_any = True

    review_count: Optional[int] = review_total if found_any else None

    return view_count, review_count


if __name__ == "__main__":
    v, r = get_gunmalove_counts("47273")
    print("VIEW_COUNT:", v)      # 예: 71023
    print("REVIEW_COUNT:", r)    # 예: 460 + 109 = 569
