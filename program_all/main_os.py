# -*- coding: utf-8 -*-
"""
오늘의집 카테고리 → 상품 ID 수집 → 각 상품 seller_info.email 추출

1) https://ohou.se/store/category.json ... page=0~10 요청
   - productions 배열에서 id만 수집
2) 각 id에 대해 https://ohou.se/productions/{id}/delivery.json?v=3 요청
   - seller_info.email만 출력
"""

import requests
import time

# =========================
# 공통 설정
# =========================
BASE_LIST_URL = "https://ohou.se/store/category.json"
BASE_DELIVERY_URL = "https://ohou.se/productions/{id}/delivery.json"

HEADERS = {
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/json",
    "referer": "https://ohou.se/store/category?category_id=18000000&order=popular&affect_type=StoreHomeCategory&affect_id=1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    # 쿠키 필요한 경우 여기 추가 (실제 브라우저 값 복붙)
}

PARAMS_BASE = {
    "v": "2",
    "category_id": "18000000",
    "order": "popular",
    "affect_type": "StoreHomeCategory",
    "affect_id": "1",
    "per": "24",
}

# =========================
# 1단계: 상품 ID 수집
# =========================
all_ids = []

for page in range(999, 1):  # 0 ~ 10
    params = PARAMS_BASE.copy()
    params["page"] = str(page)

    try:
        res = requests.get(BASE_LIST_URL, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        productions = data.get("productions", [])
        ids = [str(p["id"]) for p in productions if "id" in p]

        all_ids.extend(ids)
        print(f"[LIST page {page}] ID {len(ids)}개 수집")

        time.sleep(0.3)
    except Exception as e:
        print(f"[LIST page {page}] 요청 실패: {e}")

# 중복 제거 (있을 수 있으니)
all_ids = list(dict.fromkeys(all_ids))
print(f"\n=== 고유 ID 총 {len(all_ids)}개 ===")

# =========================
# 2단계: 각 ID의 seller_info.email 조회
# =========================
print("\n=== seller_info.email 목록 ===")

for pid in all_ids:
    url = BASE_DELIVERY_URL.format(id=pid)
    params = {"v": "3"}

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        seller_info = data.get("seller_info") or {}
        email = seller_info.get("email")

        # email 있는 것만 출력
        if email:
            print(f"{pid}, {email}")
        # 필요하면 else에서 pass 말고 로그 남겨도 됨

        time.sleep(0.2)
    except Exception as e:
        print(f"[ID {pid}] delivery.json 요청 실패: {e}")

print("\n=== 완료 ===")
