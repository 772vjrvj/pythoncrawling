import requests
from bs4 import BeautifulSoup
import csv

BASE_URL = "https://www.thewedd.com/review"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Cookie": "PHPSESSID=46d5f9216b213c292158341d7db30c8c; _gid=GA1.2.1905624147.1757604721; _fwb=141xXnf1c2MHz7rCGQRawPX.1757604721126; _fbp=fb.1.1757604721962.652996287401268935; clickonce=MHx8QEB8fDB8fEBAfHwwfHxAQHx8MHx8QEB8fDE%3D; ACEFCID=UID-68C2EB9C76E950140861A6EE; ACEUACS=undefined; AUBH1A41107468946=1757604764454476786%7C2%7C1757604764454476786%7C1%7C17576047648808MEK3S%7C1; ARBH1A41107468946=httpswwwtheweddcommembersignuphtmuniqid68c2eb9fb08a9httpswwwtheweddcommembertargetphpemail772vjrvj40navercomgenderM; ASBH1A41107468946=1757604764454476786%7C1757604770855643596%7C1757604764454476786%7C0%7Chttpswwwtheweddcommembertargetphpemail772vjrvj40navercomgenderM; nil_state=abcdefghijkmnopqrst; wcs_bt=s_40b3036c23a4:1757604894; _ga=GA1.1.1766685362.1757604721; _ga_EQVK25PTM3=GS2.1.s1757604721$o1$g1$t1757604931$j60$l0$h0; _ga_K9G29FVVJX=GS2.1.s1757604721$o1$g1$t1757604931$j60$l0$h0",  # 직접 관리하세요
    "Referer": "https://www.thewedd.com/review?page=1&category=&cate=&event_type=&desc=&desc2=&list_limit=",
    "Upgrade-Insecure-Requests": "1",
}

def crawl_review_links(start=1, end=147):
    all_links = []
    for page in range(start, end + 1):
        url = f"{BASE_URL}?page={page}&category=&cate=&event_type=&desc=&desc2=&list_limit="
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ Page {page} 요청 실패: {res.status_code}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", class_="story_list_tbl")
        if not table:
            print(f"⚠️ Page {page}: story_list_tbl 없음")
            continue

        for a in table.select("tbody tr td.subject a"):
            href = a.get("href")
            if href:
                full_url = f"https://www.thewedd.com{href}"
                all_links.append(full_url)

        print(f"✅ Page {page} 수집 완료 ({len(all_links)}개 누적)")
    return all_links

def save_to_csv(links, filename="review_links.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])  # 헤더
        for link in links:
            writer.writerow([link])
    print(f"💾 {filename} 저장 완료 (총 {len(links)}개)")


def _clean_text(s: str) -> str:
    """여백/nbsp/연속 줄바꿈 정리."""
    s = s.replace("\xa0", " ").replace("\u200b", " ")
    # 연속 공백 정리
    s = re.sub(r"[ \t]+", " ", s)
    # 윈도우/유닉스 개행 통일
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # 3개 이상 연속 개행 -> 2개
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def fetch_review_detail(url: str, headers: dict) -> dict:
    """
    상세 페이지 요청 -> review_view_tbl 안의 thead > th = 제목,
    tbody 전체 텍스트 = 내용. 이미지/스타일 태그는 무시.
    """
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", class_="review_view_tbl")
    if not table:
        # 테이블 못 찾으면 페이지 전체에서 fallback
        title = soup.select_one("thead th")
        body = soup.select_one("tbody")
    else:
        title = table.select_one("thead th")
        body = table.select_one("tbody")

    title_text = _clean_text(title.get_text(separator=" ", strip=True)) if title else ""
    # tbody 내부 모든 텍스트를 줄바꿈 기준으로 수집
    body_text = _clean_text(body.get_text(separator="\n", strip=True)) if body else ""

    return {
        "url": url,
        "제목": title_text,
        "내용": body_text,
    }

def fetch_review_details(urls, headers: dict):
    """여러 URL 한번에 처리."""
    out = []
    for u in urls:
        try:
            out.append(fetch_review_detail(u, headers))
            print(f"✅ ok: {u}")
        except Exception as e:
            print(f"❌ fail: {u} -> {e}")
    return out



if __name__ == "__main__":
    links = crawl_review_links(1, 147)
    save_to_csv(links)


