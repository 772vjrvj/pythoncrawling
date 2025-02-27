import requests
from bs4 import BeautifulSoup
import pandas as pd

# 요청 헤더 설정
HEADERS = {
    "authority": "chsjjj.shop.blogpay.co.kr",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "cookie": "ch-veil-id=84ceba26-7f6d-43b9-bae9-7dd55bec1412; bHideResizeNotice=1; PHPSESSID=di6o0nppojeln93elraldjro3b; device=pro; user_agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36; ch-session-44713=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzZXMiLCJrZXkiOiI0NDcxMy02MDUzMDY3NjQxZWExOWJhNmRlMiIsImlhdCI6MTc0MDU3MzIwMywiZXhwIjoxNzQzMTY1MjAzfQ.CIYLhFq5f7JSRF38ZhUQRrgKgh9ebb0m82SQjUAuqvs; _gid=GA1.3.657263305.1740573205; bannerType=2; blogpay_session=eyJpdiI6IkRLSFdJOHQ2MzVnUkR5aUpWMnBmRXc9PSIsInZhbHVlIjoiOUFoQ2xxRDQyY2VmU2VrWjVqQzRndjNQdmtCT05QUzd4YUZzYktvNFdiUk9ESlVhcU9qMnBUa2huMHNPeW1JMDZyS1phZUxIZ0JibnFIWlE3elh1dUE9PSIsIm1hYyI6Ijk1N2E2ZDc2OWFmYzM2ZmM3MmM0NDQwMjM5NGFjYzZmZGRjZDgyNWRkYzM2ZTc4MzIyNDMzMDgyOThlNzFlYTQifQ%3D%3D; _gat_gtag_UA_110063325_1=1; _ga_VQPYCBY0KG=GS1.1.1740573204.4.1.1740574227.59.0.0; _ga=GA1.1.773170237.1740329654"
}

# URL 템플릿
BASE_URL = "https://chsjjj.shop.blogpay.co.kr/controller/shop/board/blist"

# 페이지 크롤링 함수
def crawl_page(page):
    params = {
        "sDateType": "writeDate",
        "sDateS": "2024-11-26",
        "sDateE": "2025-02-26",
        "sDateTO": "2025-02-26",
        "sDateAll": "2000-01-01",
        "sDateT": "2025-02-23",
        "sDateW": "2025-02-19",
        "sDateM": "2025-01-26",
        "sDate2M": "2024-12-26",
        "sDate3M": "2024-11-26",
        "sDate6M": "2024-08-26",
        "sDate1Y": "2024-02-26",
        "bbsid": "BBS:GoodRate",
        "sPageSize": "1000",
        "state": "",
        "srchType": "title",
        "srchKey": "",
        "sBestReview": "",
        "title": "",
        "pageType": "",
        "page": str(page)
    }

    # GET 요청 보내기
    response = requests.get(BASE_URL, headers=HEADERS, params=params)

    # 요청 실패 시 예외 처리
    if response.status_code != 200:
        print(f"페이지 {page} 요청 실패: {response.status_code}")
        return []

    # HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # "listpage" 내부에서 "table.table-bordered" 찾기
    listpage = soup.find("div", id="listpage")
    if not listpage:
        print(f"페이지 {page}: listpage 없음")
        return []

    tables = listpage.find_all("table", class_="table table-bordered")
    if len(tables) < 2:
        print(f"페이지 {page}: 2번째 table 없음")
        return []

    table = tables[1]  # 두 번째 테이블 선택

    tbody = table.find("tbody")
    if not tbody:
        print(f"페이지 {page}: tbody 없음")
        return []

    # 결과 저장할 리스트
    results = []

    # tbody 내부의 tr 태그 순회
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")

        # 0번째 td의 input 태그에서 value 가져오기
        input_tag = tds[0].find("input", {"type": "checkbox", "name": "bbsidx[]"})
        if not input_tag or "value" not in input_tag.attrs:
            continue
        product_bbsidx = input_tag["value"]

        # 1번째 td의 텍스트 가져오기
        product_no = tds[1].text.strip()

        # 2번째 td에서 a 태그 찾기
        a_tag = tds[2].find("a")
        product_name = a_tag.text.strip() if a_tag else ""  # a 태그가 없으면 공백 처리

        # 객체로 저장
        results.append({
            "product_bbsidx": product_bbsidx,
            "product_no": product_no,
            "product_name": product_name
        })

    return results

# 엑셀 저장 함수
def save_to_excel(data, filename="output.xlsx"):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"엑셀 저장 완료: {filename}")

# 실행 메인 함수
def main():
    all_results = []

    # 페이지 1~2 크롤링
    for page in range(1, 2):
        print(f"페이지 {page} 크롤링 중...")
        results = crawl_page(page)
        all_results.extend(results)

    # 크롤링 결과를 엑셀로 저장
    print(all_results)
    save_to_excel(all_results)

if __name__ == "__main__":
    main()
