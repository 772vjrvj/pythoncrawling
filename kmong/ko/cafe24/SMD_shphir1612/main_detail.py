import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures

# 엑셀 파일 읽기
df = pd.read_excel("product_data.xlsx")

# 기본 URL 및 헤더 설정 (쿠키 제외)
BASE_URL = "https://saphir1612.cafe24.com"
HEADERS = {
    "authority": "saphir1612.cafe24.com",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "cookie": "_fwb=40hz6iQBGce3ITf0SVRGcJ.1740328311559; _fbp=fb.1.1740328311778.145355876906639091; _gcl_au=1.1.613501043.1740328312; _hjSessionUser_2368957=eyJpZCI6IjRiZjUwMTc5LTg3YWEtNWVkOC1iM2NiLTgwMGQ5NDhjZmM0NSIsImNyZWF0ZWQiOjE3NDAzMjgzMTIwNjUsImV4aXN0aW5nIjp0cnVlfQ==; _ga_12RF674XCD=GS1.1.1740336113.2.0.1740336113.60.0.0; _clck=1ieqng%7C2%7Cftu%7C0%7C1880; _ga=GA1.1.1928481410.1740328313; PHPSESSID=c7feaea5ce0e14602280146ed65f2cc1; ECSESSID=2a8f552ac7df6cf82473a30beadfcbc6; is_pcver=T; is_mobile_admin=false; FROM_DCAFE=echosting; PHPSESSVERIFY=7c7b49a575dec3f5951b9cef310513d2; iscache=F; ec_mem_level=999999999; checkedImportantNotification=false; checkedFixedNotification=false; is_new_pro_mode=T; is_mode=false; ytshops_frame=; _ga_Z6CSBGDNRT=GS1.1.1740822219.3.1.1740822634.0.0.0; _ga_ZTM1Z99BLE=GS1.1.1740822220.2.1.1740822635.55.0.0; _ga_JC3MGH4M4T=GS1.1.1740822220.3.1.1740822635.0.0.0; _ga_TW9JR58492=GS1.1.1740822446.1.1.1740822658.37.0.0; cafe_user_name=saphir1612%2C%EC%83%81%ED%92%88%EA%B4%80%EB%A6%AC%2Cue1359.echosting.cafe24.com; PRODUCTMANAGE_LimitCnt=100; is_new_pro_mode_lnb_fold=T; _clsk=1c9h4hh%7C1740830342189%7C5%7C1%7Cx.clarity.ms%2Fcollect; _ga_EGNE1592YF=GS1.1.1740828852.3.1.1740830584.60.0.0",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

def fetch_memo_data(product):
    """각 product_no를 이용해 웹페이지에서 메모 데이터를 가져오는 함수"""
    product_no = product["product_no"]
    url = f"{BASE_URL}/disp/admin/shop1/product/ProductRegister?product_no={product_no}"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch product_no {product_no}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # QA_register12 안의 MemoAddList 찾기
    qa_register = soup.find(id="QA_register12")
    if not qa_register:
        return []

    memo_list = qa_register.find(id="MemoAddList")
    if not memo_list:
        return []

    # 모든 tr 태그 찾기
    rows = memo_list.find_all("tr", class_="center eMemoList")

    result = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 4:
            continue  # 데이터가 부족하면 건너뜀

        memo_data = product.copy()  # 기존 데이터 복사
        memo_data["memo_no"] = tds[0].text.strip()  # 1번째 td 값
        memo_data["memo_regdate"] = tds[1].text.strip()  # 2번째 td 값
        memo_data["memo_author"] = tds[2].text.strip()  # 3번째 td 값
        memo_data["memo_content"] = tds[3].text.strip()  # 4번째 td 값

        result.append(memo_data)
    print(result)

    return result

def scrape_memo_data():
    """멀티쓰레드로 모든 product_no에 대해 메모 데이터를 가져옴"""
    products = df.to_dict(orient="records")  # DataFrame을 객체 리스트로 변환
    all_memo_data = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_memo_data, products))

    for result in results:
        all_memo_data.extend(result)

    return all_memo_data

if __name__ == "__main__":
    memo_data_list = scrape_memo_data()

    # 리스트를 DataFrame으로 변환 후 엑셀로 저장
    memo_df = pd.DataFrame(memo_data_list)
    memo_df.to_excel("memo_data.xlsx", index=False)


    print("Excel file 'memo_data.xlsx' has been saved.")
