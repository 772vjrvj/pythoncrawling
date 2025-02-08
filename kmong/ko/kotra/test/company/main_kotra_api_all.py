import time

import requests
import os
from bs4 import BeautifulSoup
import csv
import chardet

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
    main_products = "\n".join([f"• {div.text.strip()}" for div in soup.select(".shm-classification .cate-path-en")])

    # CEO, Address 등 기본 정보 추출
    basic_info = {li.select_one("strong").text.strip(): li.select_one("p").text.strip() for li in soup.select(".shm-basic-box li")}

    # 결과 객체 구성
    obj = {
        "url": url,
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

def detect_encoding(csv_path):
    """
    파일의 인코딩을 자동 감지하는 함수
    """
    if not os.path.exists(csv_path):  # 파일 존재 여부 확인
        print(f"❌ 파일이 존재하지 않습니다: {csv_path}")
        return None

    with open(csv_path, "rb") as file:
        raw_data = file.read(100000)  # 파일의 일부를 읽어 감지
        encoding = chardet.detect(raw_data)["encoding"]
        print(f"✅ 감지된 인코딩: {encoding}")
        return encoding if encoding else "utf-8"  # 감지 실패 시 기본 utf-8 사용


def read_com_list(csv_path="comList/comList.csv"):
    """
    comList.csv 파일을 읽어 객체 리스트로 변환하는 함수
    """
    if not os.path.exists(csv_path):
        print(f"❌ 파일을 찾을 수 없습니다: {csv_path}")
        return []

    com_list = []

    try:
        # 파일 열기 시도 (utf-8-sig 사용)
        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                print(f"⚠️ CSV 파일의 헤더가 없습니다: {csv_path}")
                return []

            for row in reader:
                com_list.append(row)

    except UnicodeDecodeError as e:
        print(f"❌ 인코딩 문제 발생: {e}")
        return []
    except Exception as e:
        print(f"❌ 알 수 없는 오류 발생: {e}")
        return []

    print(f"✅ CSV 파일 읽기 완료: {len(com_list)} 개 항목")
    return com_list


def save_seller_info_to_csv(seller_info_list, filename="Korean Seller/seller_info.csv"):
    """
    수집된 seller_info 데이터를 CSV 파일로 저장하는 함수
    """
    if not seller_info_list:
        print("저장할 데이터가 없습니다.")
        return

    os.makedirs("Korean Seller", exist_ok=True)  # 저장 폴더 생성

    keys = seller_info_list[0].keys()
    file_path = os.path.join("Korean Seller", filename)

    with open(file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(seller_info_list)

    print(f"{file_path} 파일로 저장 완료.")
    print(f"총 수집된 셀러 개수: {len(seller_info_list)}")


def update_com_list_csv(com_list, filename="comList/comList.csv"):
    """
    기존 comList.csv 파일을 UTF-8-SIG로 업데이트하는 함수
    """
    if not com_list:
        print("업데이트할 데이터가 없습니다.")
        return

    keys = com_list[0].keys()  # 기존 CSV의 필드 가져오기

    with open(filename, mode="w", newline="", encoding="utf-8-sig", errors="replace") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(com_list)

    print(f"{filename} 파일 업데이트 완료. 총 개수: {len(com_list)}")


def main(start_index=0, end_index=None):
    com_list = read_com_list()  # 기존 CSV에서 데이터 읽기

    # 특정 인덱스 범위만 처리
    for company in com_list[start_index:] if end_index is None else com_list[start_index:end_index]:
        entpUrl = company.get("entpUrl")
        if entpUrl:
            seller_info = fetch_seller_info(entpUrl)
            if seller_info:
                # 기존 company 데이터에 seller_info 정보 추가
                company.update(seller_info)
                download_image(seller_info["img"], seller_info["title"])
        time.sleep(1)

    # 업데이트된 com_list를 다시 CSV로 저장
    update_com_list_csv(com_list)

if __name__ == "__main__":
    main(10, 101)  # 예제: 0번부터 9번까지 처리하고 업데이트