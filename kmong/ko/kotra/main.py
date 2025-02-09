import csv
import os
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin


def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def fetch_product_details(goods_sn):
    url = f"https://buykorea.org/ec/prd/selectGoodsDetail.do?goodsSn={goods_sn}"
    driver = setup_driver()
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    list_location = " > ".join([li.text.strip() for li in soup.select(".list-location li a")])

    title = soup.select_one(".detail-right .goods-info .bk-title .title-sub")
    price = soup.select_one(".detail-right .goods-info .goods-price")
    goods_overview = soup.select_one(".detail-right .goods-info .goods-overview-area")
    quantity = soup.select_one(".detail-right .goods-info .quantity-area dd")
    company_name = soup.select_one(".goods-companyName .text")
    detail_product = soup.select_one("#tab-detail-product .product-detail")

    title = title.get_text(strip=True) if title else ""
    price = price.get_text(strip=True) if price else ""
    name = f"{title}\n{price}"
    goods_overview = goods_overview.get_text(strip=True) if goods_overview else ""
    quantity = quantity.get_text(strip=True) if quantity else ""
    company_name = company_name.get_text(strip=True) if company_name else ""
    detail_product = detail_product.get_text(strip=True) if detail_product else ""

    base_url = "https://buykorea.org"  # 크롤링하는 사이트의 기본 URL
    # img_list = [urljoin(base_url, img["src"]) for img in soup.select(".detail-left .swiper-gallery-thumbs .swiper-wrapper img") if "src" in img.attrs]

    img_list = [
        urljoin(base_url, img["src"])
        for img in soup.select(".detail-left .swiper-gallery-thumbs .swiper-wrapper img")
        if img.has_attr("src") and img["src"].startswith(("http", "/"))
    ]

    detail_img_list = [
        urljoin(base_url, img["src"])
        for img in soup.select("#tab-detail-product .product-detail img")
        if img.has_attr("src") and img["src"].startswith(("http", "/"))
    ]
    keywords = [tag.text.strip() for tag in soup.select("#dv-goodsDtl-keyword-list .text")]

    goodsinfo_list = [
        {
            "goodsinfocd": btn.get("goodsinfocd"),
            "goodsinfosn": btn.get("goodsinfosn")
        }
        for btn in soup.select(".list-download .bk-btn.btn-default.btn-outline")
        if btn.get("goodsinfocd") and btn.get("goodsinfosn")
    ]


    return {
        "PID": goods_sn,
        "list_location": list_location,
        "title": title,
        "price": price,
        "name": name,
        "goods_overview": goods_overview,
        "quantity": quantity,
        "company_name": company_name,
        "img_list": img_list,
        "detail_product": detail_product,
        "detail_img_list": detail_img_list,
        "keywords": keywords,
        "goodsinfo_list": goodsinfo_list
    }

def save_images(img_urls, base_path, pid):
    os.makedirs(base_path, exist_ok=True)
    for idx, img_url in enumerate(img_urls, start=1):
        img_path = os.path.join(base_path, f"{pid}_{idx}.jpg")
        print(f"img_path: {img_path}")
        img_data = requests.get(img_url).content
        with open(img_path, "wb") as img_file:
            img_file.write(img_data)
    print(f"이미지 저장 완료: {base_path}")


def download_product_data(goodsSn, goodsInfoCd, goodsInfoSn, save_path="downloads"):
    """
    상품 데이터를 다운로드하는 함수
    """
    url = f"https://buykorea.org/ec/prd/goodsFileDownload.do?goodsSn={goodsSn}&goodsInfoCd={goodsInfoCd}&goodsInfoSn={goodsInfoSn}"
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        os.makedirs(save_path, exist_ok=True)
        filename = os.path.join(save_path, f"{goodsSn}_{goodsInfoCd}_{goodsInfoSn}.pdf")  # 파일 확장자 필요시 수정

        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"파일 다운로드 완료: {filename}")
    else:
        print(f"다운로드 실패: {response.status_code}")



def update_csv(csv_path, product_list):
    """
    CSV 파일을 업데이트하는 함수
    """
    if not product_list:
        print(f"⚠️ 업데이트할 데이터가 없습니다: {csv_path}")
        return

    keys = product_list[0].keys()  # 기존 필드에 product_data 추가
    temp_path = csv_path + ".tmp"  # 임시 파일 경로

    with open(temp_path, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(product_list)

    os.replace(temp_path, csv_path)  # 기존 파일을 새로운 파일로 덮어쓰기
    print(f"✅ CSV 업데이트 완료: {csv_path}")


def main(start_index = 0, end_index = None):
    ctgrycd_path = "ctgrycd"  # 실행경로의 ctgrycd 폴더
    csv_files = [f for f in os.listdir(ctgrycd_path) if f.endswith(".csv")][start_index:end_index]  # 특정 범위만 처리

    for csv_file in csv_files:
        csv_path = os.path.join(ctgrycd_path, csv_file)

        # CSV 파일 읽기
        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            product_list = [row for row in reader]  # 객체 리스트로 변환

        for idx, product in enumerate(product_list):
            goods_sn = product["goodsSn"]  # goodsSn 값 가져오기

            product_data = fetch_product_details(goods_sn)

            category_path = os.path.join("Product Categories", os.sep.join(product_data["list_location"].split(" > ")[2:]))

            safe_title = product_data["title"].replace("/", "-")
            product_img_path = os.path.join(category_path, safe_title, "product_img")
            product_detail_path = os.path.join(category_path, safe_title, "detail_img")

            save_images(product_data["img_list"], product_img_path, product_data["PID"])
            save_images(product_data["detail_img_list"], product_detail_path, product_data["PID"])

            for goodsinfo in product_data["goodsinfo_list"]:
                product_downloads_path = os.path.join(category_path, safe_title, "catalog_downloads")
                download_product_data(product_data["PID"], goodsinfo['goodsinfocd'], goodsinfo['goodsinfosn'], product_downloads_path)

            # ✅ `product_data` 내용을 기존 `product` 객체에 추가
            product.update(product_data)
            print(f'idx : {idx}, goods_sn : {goods_sn} 성공')

        # ✅ CSV 파일 업데이트
        update_csv(csv_path, product_list)



if __name__ == "__main__":
    start_index = 17  # 시작 인덱스
    end_index = 18  # 종료 인덱스 (None이면 끝까지)

    main(start_index, end_index)