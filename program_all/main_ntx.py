# -*- coding: utf-8 -*-
import json
import time
import requests


URL = "https://www.nextrade.co.kr/brdinfoTime/brdinfoTimeList.do"
REFERER = "https://www.nextrade.co.kr/menu/transactionStatusMain/menuList.do"


def pretty_print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main():
    # =========================
    # 1) Payload (Form Data)
    # =========================
    payload = {
        "_search": "false",
        "nd": str(int(time.time() * 1000)),  # 밀리초 타임스탬프
        "pageUnit": "20",
        "pageIndex": "1",
        "sidx": "",
        "sord": "asc",
        "scAggDd": "20251226",
        "scMktId": "",
        "searchKeyword": "",
    }

    # =========================
    # 2) Headers (쿠키 없음)
    # =========================
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.nextrade.co.kr",
        "referer": REFERER,
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/143.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
    }

    # =========================
    # 3) Session 생성
    # =========================
    session = requests.Session()
    session.headers.update(headers)

    # =========================
    # 4) 세션 워밍업 (중요)
    #    → 여기서 JSESSIONID / cf 쿠키 자동 발급
    # =========================
    session.get("https://www.nextrade.co.kr", timeout=15)

    # =========================
    # 5) POST 요청
    # =========================
    response = session.post(URL, data=payload, timeout=15)
    response.raise_for_status()

    # =========================
    # 6) JSON 출력
    # =========================
    try:
        data = response.json()
    except Exception:
        data = json.loads(response.text)

    pretty_print(data)

    # =========================
    # 7) 파일 저장 (선택)
    # =========================
    with open("nextrade_brdinfoTimeList_20251226.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
