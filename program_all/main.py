import pandas as pd
import requests
from bs4 import BeautifulSoup
import html
import time

# 1. 엑셀에서 SHOP_ID 읽기 및 중복 제거
df = pd.read_excel("vipinfo_all_user_grp.xlsx")
shop_ids = df["SHOP_ID"].dropna().unique()

# 2. 요청 헤더 (쿠키 제외)
headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://vipgunma.com",
    "priority": "u=0, i",
    "referer": "https://vipgunma.com/bbs/board.php",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

# 3. 최종 결과 리스트
review_list = []

# 4. 전체 SHOP_ID 반복
for shop_index, sid in enumerate(shop_ids, start=1):
    print(f"\n📦 {shop_index}/{len(shop_ids)} | SHOP_ID {sid} 리뷰 수집 시작...")

    page = 1
    prev_html = None

    while True:
        payload = {
            "request": "requestRev",
            "page": str(page),
            "wr_id": str(sid)
        }

        response = requests.post(
            "https://vipgunma.com/bbs/rev.php",
            headers=headers,
            data=payload
        )

        if response.status_code != 200:
            print(f"❌ 요청 실패: SHOP_ID={sid}, page={page}")
            break

        try:
            json_data = response.json()
        except Exception as e:
            print(f"❌ JSON 파싱 실패: {e}")
            break

        raw_html = json_data.get("result_data", {}).get("list", "")
        if not raw_html.strip() or raw_html == prev_html:
            break
        prev_html = raw_html

        # HTML 문자열 파싱
        cleaned_html = html.unescape(raw_html)
        soup = BeautifulSoup(cleaned_html, "html.parser")
        cards = soup.select("div.reviewCard")
        if not cards:
            break

        for review_index, card in enumerate(cards, start=1):
            try:
                user_id = card.get("id", "").replace("c_", "")
                review_nick = card.select_one(".reviewNick").get_text(strip=True)
                review_date = card.select_one(".reviewDate").get_text(strip=True)
                review_content = card.select_one(".reviewCardBody").get_text(separator="\n", strip=True)

                # 날짜 보정
                if len(review_date) == 5 and "-" in review_date:
                    review_date = f"2025-{review_date}"


                obj = {
                    "shop_id": sid,
                    "user_id": user_id,
                    "review_nick": review_nick,
                    "review_date": review_date,
                    "review_content": review_content
                }

                review_list.append(obj)

                # ✅ 진행 상태 출력
                print(f"📍 {shop_index}/{len(shop_ids)} | page : {page} | {review_index}/{len(cards)} | SHOP_ID={sid} | 데이터 : {obj}")


            except Exception as e:
                print(f"⚠️ 파싱 오류: SHOP_ID={sid}, page={page}, index={review_index} | {e}")
                continue

        page += 1
        time.sleep(0.3)

# 5. 결과 엑셀 저장
result_df = pd.DataFrame(review_list)
result_df.to_excel("vip_review_result.xlsx", index=False)
print("\n✅ 모든 리뷰 수집 완료 → vip_review_result.xlsx 저장됨")
