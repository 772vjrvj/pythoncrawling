# -*- coding: utf-8 -*-
"""
457deep.com Next.js RSC (text/x-component) 응답 수집 스크립트
- 요청 헤더: 사용자 제공 값 전부 포함 (쿠키 제외)
- HTTP/2 사용
- Brotli(br) 자동/수동 디코딩 대응
- RSC 원문 파일 저장
"""

import httpx
import brotli
from pathlib import Path


URL = "https://457deep.com/community/success-story?page=2&_rsc=1c892"

# =========================================================
# 요청 헤더 (쿠키 제외, 제공된 값 전부 포함)
# =========================================================
HEADERS = {
    # --- HTTP/2 pseudo-header (실제 전송은 스택이 처리, 기록용으로 유지) ---
    "authority": "457deep.com",
    "method": "GET",
    "path": "/community/success-story?page=2&_rsc=1c892",
    "scheme": "https",

    # --- 일반 헤더 ---
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",

    "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22community%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22success-story%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fcommunity%2Fsuccess-story%22%2C%22refresh%22%5D%7D%5D%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
    "next-url": "/community/success-story",

    "priority": "u=1, i",
    "referer": "https://457deep.com/community/success-story",
    "rsc": "1",
    "cookie": """_ga=GA1.1.57483619.1769702274; ch-veil-id=23319582-beeb-4afb-b912-1d0bdd10cb44; __Host-authjs.csrf-token=4bf6bc026817bd1bf1bf665a67a7046523273cf97950cb71b645f3d562f61856%7Cd1d421faab99163aff9219f988f1e418885b5843d9155ce2e99a299080bda410; __Secure-authjs.callback-url=https%3A%2F%2F457deep.com%2Fstart%3Fnext%3D%2Fcommunity%2Fsuccess-story; _ga_679PGEM9W0=GS2.1.s1770097920$o3$g1$t1770099051$j59$l0$h0; __Secure-authjs.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwia2lkIjoiZDJWYjVkNWhsZ3BLNVdNUWgzLXNDNjhRNjVKWFd2V0NJQkRrVDY1TlNiazh4TWNGb3NKQzZYNllrZF92bXJ4YVg2Q0duSUhiZTJ6WU1qNDdYWlB2WFEifQ..g0qigR24o7cLk0o-gyqNsQ.yMpaT13XOhU4XcDl-HvMucEAAwxMb-aGc0XMXe5Cb2hv7MVRbqVKjAbnvnY7i4gYQKqcr4zvYjZpg62J_0yvH4FnO89ukDvIn_fiM7gO758O7tRhX-wfbMBUimVairetZuyxIKJ3MeMZWMM-vfXqYONTdU5JC29RuDY5R-zbQkyWPNf2d5PSu95-O3FxWAPZJYHMV2ha0WbHU03N5FbHIuTIAdbDQ2YuDV7bPuNDkPHQgNYKk1VjiyCxkPkOkYz9Szv6gF84ML3N5KWQKCBJDcFqMfnQPSlXRk_7igi95fMRKQ2D-YtckqX2oMhpX3mY.ZWjqOwtRnjzbsigg3NLmnSWEin8D4-2lSICI7fmh1SQ; ch-session-175174=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzZXMiLCJleHAiOjE3NzI2OTEwNTEsImlhdCI6MTc3MDA5OTA1MSwia2V5IjoiMTc1MTc0LTY5N2I4MzgyNDcwMGRkYTJmYjU0In0.R5GMqqsTmkv3VIEqtWnVQF1LGn5Ka9gSqzHtA5DlUaU; ph_phc_Roj6ArViyDfuDQaomjdr6yJgaA0KmsqXBKdQmEfuPd7_posthog=%7B%22%24device_id%22%3A%22019c0a79-b201-7eeb-9060-983fddd933dd%22%2C%22distinct_id%22%3A%22cmkyuhems0000dh205qm8ht0n%22%2C%22%24sesid%22%3A%5B1770099056342%2C%22019c220e-cba4-7313-9eb6-26bb4c2c55e1%22%2C1770097920920%5D%2C%22%24epp%22%3Atrue%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22%24direct%22%2C%22u%22%3A%22https%3A%2F%2F457deep.com%2F%22%7D%7D""",

    "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",

    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",

    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
}


# =========================================================
# 메인 로직
# =========================================================
def fetch_rsc(url: str) -> str:
    """
    RSC(text/x-component) 응답을 받아 문자열로 반환
    - httpx HTTP/2 사용
    - br 인코딩 수동 대응
    """
    with httpx.Client(
            http2=True,
            headers=HEADERS,
            timeout=30.0,
            follow_redirects=True
    ) as client:

        resp = client.get(url)

        print("status            :", resp.status_code)
        print("content-type      :", resp.headers.get("content-type"))
        print("content-encoding  :", resp.headers.get("content-encoding"))
        print("x-matched-path    :", resp.headers.get("x-matched-path"))
        print("x-vercel-cache    :", resp.headers.get("x-vercel-cache"))
        print("response length   :", len(resp.content))

        resp.raise_for_status()

        # === 대부분 여기서 바로 text로 풀림 ===
        try:
            return resp.text
        except Exception:
            pass

        # === 신규 === 수동 brotli 디코딩 (혹시 모를 대비)
        enc = (resp.headers.get("content-encoding") or "").lower()
        raw = resp.content

        if "br" in enc:
            raw = brotli.decompress(raw)

        return raw.decode("utf-8", errors="replace")


def save_text(path: str, text: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# =========================================================
# 실행
# =========================================================
if __name__ == "__main__":
    text = fetch_rsc(URL)

    print("\n========== RSC RESPONSE PREVIEW (first 800 chars) ==========")
    print(text)

    out_path = "out/457deep_success_story_page2.rsc.txt"
    save_text(out_path, text)

    print(f"\nSaved → {out_path}")
