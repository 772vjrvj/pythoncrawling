from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import os
import time

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
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    list_location = " > ".join([li.text.strip() for li in soup.select(".list-location li a")])
    title = soup.select_one(".detail-right .goods-info .bk-title .title-sub").text.strip()
    price = soup.select_one(".detail-right .goods-info .goods-price").text.strip()
    name = f"{title}\n{price}"
    goods_overview = soup.select_one(".detail-right .goods-info .goods-overview-area").text.strip()
    quantity = soup.select_one(".detail-right .goods-info .quantity-area dd").text.strip()
    company_name = soup.select_one(".goods-companyName .text").text.strip()

    img_list = [img["src"] for img in soup.select(".detail-left .swiper-gallery-thumbs .swiper-wrapper img")]

    detail_product = soup.select_one("#tab-detail-product .product-detail").text.strip()
    detail_img_list = [img["src"] for img in soup.select("#tab-detail-product .product-detail img")]

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


if __name__ == "__main__":
    goods_sn = "3732079"

    product_data = fetch_product_details(goods_sn)
    category_path = os.path.join("Product Categories", os.sep.join(product_data["list_location"].split(" > ")[2:]))
    product_img_path = os.path.join(category_path, product_data["title"], "product_img")
    product_detail_path = os.path.join(category_path, product_data["title"], "detail_img")

    save_images(product_data["img_list"], product_img_path, product_data["PID"])
    save_images(product_data["detail_img_list"], product_detail_path, product_data["PID"])

    for goodsinfo in product_data["goodsinfo_list"]:
        product_downloads_path = os.path.join(category_path, product_data["title"], "catalog_downloads")
        download_product_data(product_data["PID"], goodsinfo['goodsinfocd'], goodsinfo['goodsinfosn'], product_downloads_path)
