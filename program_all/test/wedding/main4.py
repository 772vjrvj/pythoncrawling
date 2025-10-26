# -*- coding: utf-8 -*-
import requests, csv, time, re
from bs4 import BeautifulSoup

BASE_LIST = "https://www.thewedd.com/review"
BASE_HOST = "https://www.thewedd.com"
START_PAGE = 1
END_PAGE = 147  # 필요시 조절

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    # ⚠️ 쿠키는 본인 환경에 맞게 유지/교체하세요
    "Cookie": "PHPSESSID=46d5f9216b213c292158341d7db30c8c; _gid=GA1.2.1905624147.1757604721; _fwb=141xXnf1c2MHz7rCGQRawPX.1757604721126; _fbp=fb.1.1757604721962.652996287401268935; clickonce=MHx8QEB8fDB8fEBAfHwwfHxAQHx8MHx8QEB8fDE%3D; ACEFCID=UID-68C2EB9C76E950140861A6EE; ACEUACS=undefined; AUBH1A41107468946=1757604764454476786%7C2%7C1757604764454476786%7C1%7C17576047648808MEK3S%7C1; ARBH1A41107468946=httpswwwtheweddcommembersignuphtmuniqid68c2eb9fb08a9httpswwwtheweddcommembertargetphpemail772vjrvj40navercomgenderM; ASBH1A41107468946=1757604764454476786%7C1757604770855643596%7C1757604764454476786%7C0%7Chttpswwwtheweddcommembertargetphpemail772vjrvj40navercomgenderM; nil_state=abcdefghijkmnopqrst; wcs_bt=s_40b3036c23a4:1757604894; _ga=GA1.1.1766685362.1757604721; _ga_EQVK25PTM3=GS2.1.s1757604721$o1$g1$t1757604931$j60$l0$h0; _ga_K9G29FVVJX=GS2.1.s1757604721$o1$g1$t1757604931$j60$l0$h0",
}

def clean_text(s):
    s = s.replace("\xa0", " ").replace("\u200b", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def crawl_links(session, start=1, pause=0.2, stop_after_empty_pages=1):
    """
    목록 페이지를 1부터 시작해, 더 이상 새 링크가 나오지 않을 때까지 수집.
    - 중복 즉시 제거(등장 순서 유지)
    - 해당 페이지에서 새로 얻은 링크 수가 0이면 empty_streak 증가 → 임계치 도달 시 종료
    """
    links, seen = [], set()
    page = start
    empty_streak = 0

    while True:
        url = f"{BASE_LIST}?page={page}&category=&cate=&event_type=&desc=&desc2=&list_limit="
        try:
            res = session.get(url, timeout=30, allow_redirects=True)
            if res.status_code != 200:
                print(f"❌ Page {page} 실패: {res.status_code}")
                empty_streak += 1
                if empty_streak >= stop_after_empty_pages:
                    print(f"🛑 더 이상 데이터가 없어 종료 (page={page}, status)")
                    break
                page += 1
                continue

            soup = BeautifulSoup(res.content, "html.parser")
            table = soup.find("table", class_="story_list_tbl")
            anchors = table.select("tbody tr td.subject a[href]") if table else []

            new_cnt = 0
            for a in anchors:
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                full = href if href.startswith("http") else (BASE_HOST + href)
                if full not in seen:
                    seen.add(full)
                    links.append(full)
                    new_cnt += 1

            if new_cnt == 0:
                empty_streak += 1
                print(f"⚠️ Page {page} 새 링크 0개 (연속 {empty_streak})")
            else:
                empty_streak = 0
                print(f"✅ Page {page} 완료 (+{new_cnt}, 누적 {len(links)}개)")

            if empty_streak >= stop_after_empty_pages:
                print(f"🛑 더 이상 데이터가 없어 종료 (page={page})")
                break

            page += 1
            time.sleep(pause)

        except Exception as e:
            print(f"❌ Page {page} 에러: {e}")
            empty_streak += 1
            if empty_streak >= stop_after_empty_pages:
                print(f"🛑 연속 오류/빈 페이지로 종료 (page={page})")
                break
            page += 1
            time.sleep(pause)

    return links


def fetch_detail(session, url):
    res = session.get(url, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, "html.parser")
    table = soup.find("table", class_="review_view_tbl")
    if table:
        title = table.select_one("thead th")
        body = table.select_one("tbody")
    else:
        title = soup.select_one("thead th")
        body = soup.select_one("tbody")
    title_text = clean_text(title.get_text(" ", strip=True)) if title else ""
    body_text  = clean_text(body.get_text("\n", strip=True)) if body else ""
    return {"url": url, "제목": title_text, "내용": body_text}

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"🔎 목록 수집: {START_PAGE} ~ {END_PAGE} 페이지")
    urls = crawl_links(session, START_PAGE, END_PAGE)
    print(f"📌 총 {len(urls)}개 링크")

    rows = []
    for i, u in enumerate(urls, 1):
        try:
            row = fetch_detail(session, u)
            rows.append(row)
            print(f"({i}/{len(urls)}) ✅ {u}")
        except Exception as e:
            print(f"({i}/{len(urls)}) ❌ {u} -> {e}")
        time.sleep(0.2)

    out = "review_details.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["url", "제목", "내용"])
        w.writeheader()
        for r in rows:
            # 혹시 모를 깨짐 방지용 안전 변환
            r["제목"] = r.get("제목", "").encode("utf-8", "ignore").decode("utf-8")
            r["내용"] = r.get("내용", "").encode("utf-8", "ignore").decode("utf-8")
            w.writerow({"url": r.get("url",""), "제목": r["제목"], "내용": r["내용"]})
    print(f"💾 저장 완료: {out} (총 {len(rows)}건)")

if __name__ == "__main__":
    main()
