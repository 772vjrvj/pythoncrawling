import requests
import json
import time

BASE_URL = "https://m.cafe.daum.net/api/v1/common-articles"
GRPID = "1YvZ5"
FLDID = "D034"
PAGE_SIZE = 50
OUTPUT_FILE = "odin.json"
STOP_DATE = "23.08.11"  # 발견 시 종료

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

def fetch_page(page_num, after=None):
    params = {
        "grpid": GRPID,
        "fldid": FLDID,
        "pageSize": PAGE_SIZE,
        "targetPage": page_num
    }
    if after:
        params["afterBbsDepth"] = after

    r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    all_data = []
    after_cursor = None
    page_num = 1

    while True:
        data = fetch_page(page_num, after_cursor)
        articles = data.get("articles", [])

        if not articles:
            print("📌 더 이상 데이터 없음. 종료")
            break

        last_date = articles[-1].get("articleElapsedTime", "N/A")

        for article in articles:
            if article.get("articleElapsedTime") == STOP_DATE:
                print(f"📌 {STOP_DATE} 발견 → 수집 종료")
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=2)
                print(f"✅ {len(all_data)}건 저장 완료 → {OUTPUT_FILE}")
                return
            all_data.append(article)

        print(f"[Page {page_num}] {len(articles)}건 수집 / 누적 {len(all_data)}건 / 마지막 날짜 {last_date}")

        after_cursor = articles[-1].get("bbsDepth")
        if not after_cursor:
            print("📌 다음 커서 없음. 종료")
            break

        page_num += 1  # targetPage 증가
        time.sleep(0.3)  # 서버 부하 방지

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(all_data)}건 저장 완료 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
