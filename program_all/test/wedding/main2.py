import csv
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.thewedd.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Cookie": "PHPSESSID=46d5f9216b213c292158341d7db30c8c; _gid=GA1.2.1905624147.1757604721; _fwb=141xXnf1c2MHz7rCGQRawPX.1757604721126; _fbp=fb.1.1757604721962.652996287401268935; clickonce=MHx8QEB8fDB8fEBAfHwwfHxAQHx8MHx8QEB8fDE%3D; ACEFCID=UID-68C2EB9C76E950140861A6EE; ACEUACS=undefined; AUBH1A41107468946=1757604764454476786%7C2%7C1757604764454476786%7C1%7C17576047648808MEK3S%7C1; ARBH1A41107468946=httpswwwtheweddcommembersignuphtmuniqid68c2eb9fb08a9httpswwwtheweddcommembertargetphpemail772vjrvj40navercomgenderM; ASBH1A41107468946=1757604764454476786%7C1757604770855643596%7C1757604764454476786%7C0%7Chttpswwwtheweddcommembertargetphpemail772vjrvj40navercomgenderM; nil_state=abcdefghijkmnopqrst; wcs_bt=s_40b3036c23a4:1757604894; _ga=GA1.1.1766685362.1757604721; _ga_EQVK25PTM3=GS2.1.s1757604721$o1$g1$t1757604931$j60$l0$h0; _ga_K9G29FVVJX=GS2.1.s1757604721$o1$g1$t1757604931$j60$l0$h0",
}

# --- 유틸: 텍스트 정리 ---
def _clean_text(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\u200b", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

# --- 상세 페이지 파싱 ---
def fetch_review_detail(url: str, headers: dict) -> dict:
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    res.encoding = "euc-kr"   # 혹은 "euc-kr" (만약 utf-8로도 깨지면 이걸로 시도)

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", class_="review_view_tbl")

    if table:
        title = table.select_one("thead th")
        body = table.select_one("tbody")
    else:  # fallback
        title = soup.select_one("thead th")
        body = soup.select_one("tbody")

    title_text = _clean_text(title.get_text(separator=" ", strip=True)) if title else ""
    body_text = _clean_text(body.get_text(separator="\n", strip=True)) if body else ""

    return {
        "url": url,
        "제목": title_text,
        "내용": body_text,
    }

# --- CSV 읽기 ---
def load_links_from_csv(filename="review_links.csv") -> list:
    urls = []
    with open(filename, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url")
            if url:
                urls.append(url.strip())
    return urls

# --- CSV 저장 ---
def save_details_to_csv(data: list, filename="review_details.csv"):
    # 파일은 그냥 UTF-8-SIG로 연다 (Excel 호환)
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "제목", "내용"])
        writer.writeheader()
        for row in data:
            safe_row = {
                "url": str(row.get("url", "")),
                "제목": row["제목"].encode("utf-8", errors="ignore").decode("utf-8"),
                "내용": row["내용"].encode("utf-8", errors="ignore").decode("utf-8"),
            }
            writer.writerow(safe_row)
    print(f"💾 {filename} 저장 완료 ({len(data)}개)")

if __name__ == "__main__":
    urls = load_links_from_csv("review_links.csv")
    print(f"총 {len(urls)}개 링크 로드 완료")

    results = []
    for u in urls:
        try:
            obj = fetch_review_detail(u, HEADERS)
            results.append(obj)
            print(f"✅ {u}")
        except Exception as e:
            print(f"❌ {u} -> {e}")

    save_details_to_csv(results, "review_details.csv")
