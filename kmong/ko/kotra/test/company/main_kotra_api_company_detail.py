import requests
import os
from bs4 import BeautifulSoup
import csv

def fetch_seller_info(seller_id):
    """
    셀러 정보를 가져오는 함수
    """
    url = f"https://buykorea.org{seller_id}/com/index.do"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "buykorea.org",
        "referer": f"https://buykorea.org{seller_id}",
        "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
        "sec-ch-ua-mobile": "?0",
        "cookie": "ozvid=e2abbd67-24a6-d33f-ea52-a472fcb0d8fc; _pk_id.6,DzGc5mPl.570a=eeb08969fd539d55.1738845101.; JSESSIONID=RMlBjDcM4gdBHhfm_dMUjSuD0B6NFAnMqdGgpr6q.bk-fo-02; dialogSnackbar=Y; bkRcntPrds=3732083%2C3732098%2C3702390%2C3730424%2C3732078%2C3732079; _pk_ses.6,DzGc5mPl.570a=1",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"요청 실패: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 이미지 src 추출 및 URL 수정
    img_tag = soup.select_one(".img-ratio-fix img")
    img_src = img_tag["src"] if img_tag else ""
    if img_src.startswith("/"):
        img_src = f"https://buykorea.org{img_src}"

    # 타이틀 추출
    title = soup.select_one(".shm-info-text .lv-title").text.strip()

    # Favorites, Inquiry, Order, Review 값 추출
    stats = {dt.text.strip(): dd.text.strip() for dt, dd in zip(soup.select(".shm-data dt"), soup.select(".shm-data dd"))}

    # Business Type 및 Main Products 추출
    business_type = soup.select_one(".shm-classification .ellipsis").text.strip() if soup.select_one(".shm-classification .ellipsis") else ""
    main_products = soup.select_one(".shm-classification .cate-path-en").text.strip() if soup.select_one(".shm-classification .cate-path-en") else ""

    # CEO, Address 등 기본 정보 추출
    basic_info = {li.select_one("strong").text.strip(): li.select_one("p").text.strip() for li in soup.select(".shm-basic-box li")}

    # 결과 객체 구성
    obj = {
        "title": title,
        "img": img_src,
        "favorites": stats.get("Favorites", ""),
        "inquiry": stats.get("Inquiry", ""),
        "order": stats.get("Order", ""),
        "review": stats.get("Review", ""),
        "business_type": business_type,
        "main_products": main_products,
        "ceo": basic_info.get("CEO", ""),
        "address": basic_info.get("Address", ""),
        "country_region": basic_info.get("Country / Region", ""),
        "homepage": basic_info.get("Homepage", ""),
        "total_employees": basic_info.get("Total Employees", ""),
        "total_annual_revenue": basic_info.get("Total Annual Revenue", ""),
        "year_established": basic_info.get("Year Established", ""),
        "main_markets": basic_info.get("Main Markets", "")
    }

    return obj

def download_image(img_url, title, save_path="Korean Seller"):
    """
    이미지를 다운로드하는 함수
    """
    if not img_url:
        print("이미지 URL이 없습니다.")
        return

    os.makedirs(save_path, exist_ok=True)  # 폴더 생성

    file_name = f"{title}.jpg"
    file_path = os.path.join(save_path, file_name)

    response = requests.get(img_url, stream=True)

    if response.status_code == 200:
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"이미지 저장 완료: {file_path}")
    else:
        print(f"이미지 다운로드 실패: {response.status_code}")


def read_com_list(csv_path="comList/comList.csv"):
    """
    comList.csv 파일을 읽어 객체 리스트로 변환하는 함수
    """
    com_list = []
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            com_list.append(row)
    return com_list


# 실행 예제
if __name__ == "__main__":
    com_list = read_com_list()  # CSV에서 데이터 읽기

    for company in com_list:
        entpUrl = company.get("entpUrl")
        if entpUrl:
            seller_info = fetch_seller_info(entpUrl)
            if seller_info:
                print(seller_info)
                download_image(seller_info["img"], seller_info["title"])