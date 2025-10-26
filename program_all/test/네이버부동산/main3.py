# pip install selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

HTML_URL = "https://fin.land.naver.com/complexes/7965?tab=article"
API_URL  = "https://fin.land.naver.com/front-api/v1/complex/article/list"

payload = {
    "complexNumber": "7965",
    "tradeTypes": [],
    "pyeongTypes": [],
    "dongNumbers": [],
    "userChannelType": "PC",
    "articleSortType": "RANKING_DESC",
    "seed": "",
    "lastInfo": [],
    "size": 100,
}

def call_article_list():
    opts = Options()
    # opts.add_argument("--headless=new")  # 필요 시 헤드리스
    driver = webdriver.Chrome(options=opts)
    try:
        # 1) 같은 오리진 페이지 먼저 로드 (쿠키/세션/토큰 세팅)
        driver.get(HTML_URL)

        # 2) 같은 컨텍스트에서 fetch(POST) 실행
        # execute_async_script로 Promise 완료를 기다립니다.
        js = r"""
        const url = arguments[0];
        const body = arguments[1];
        const done = arguments[2];

        fetch(url, {
            method: "POST",
            credentials: "include",  // 현재 페이지의 쿠키/세션 포함
            headers: {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        })
        .then(r => r.json())
        .then(data => done({ ok: true, data }))
        .catch(err => done({ ok: false, error: String(err) }));
        """
        result = driver.execute_async_script(js, API_URL, payload)

        if not result.get("ok"):
            raise RuntimeError(f"fetch error: {result.get('error')}")

        data = result.get("data", {})
        # 필요 시 원하는 필드만 골라 출력
        print("=== raw data ===")
        import json
        print(json.dumps(data, ensure_ascii=False, indent=2))

        # 예: 성공/카운트/리스트 요약 출력 (스키마에 따라 없을 수도 있음)
        if data.get("isSuccess") is True:
            res = data.get("result") or {}
            total = res.get("totalCount")
            lst = res.get("list") or res.get("articles") or []
            print("\n=== summary ===")
            print("isSuccess:", True)
            if total is not None:
                print("totalCount:", total)
            print("items:", len(lst))
        else:
            print("\nAPI 실패:", data.get("detailCode"), data.get("message"))

    finally:
        driver.quit()

if __name__ == "__main__":
    call_article_list()
