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
import urllib.parse
import unicodedata

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fetch_product_details(goods_sn):
    try:
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

        result = ""
        if detail_product:
            for element in detail_product.children:
                if element.name == 'p':
                    text = element.get_text(strip=True)
                    if not text or text.isspace():
                        result += "\n"
                    else:
                        result += text + "\n"
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        text = li.get_text(strip=True)
                        if text:
                            result += text + "\n"

        base_url = "https://buykorea.org"
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
            {"goodsinfocd": btn.get("goodsinfocd"), "goodsinfosn": btn.get("goodsinfosn")}
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
            "detail_product": result,
            "detail_img_list": detail_img_list,
            "keywords": keywords,
            "goodsinfo_list": goodsinfo_list
        }
    except Exception as e:
        print(f"⚠ [ERROR] 상품 상세 정보 가져오기 실패: {goods_sn}, 이유: {e}")
        return None  # 실패 시 None 반환

def get_fixed_url(url):
    url = urllib.parse.unquote(url)
    url = url.replace(" ", "")
    return url

def save_images(img_urls, base_path, pid):
    os.makedirs(base_path, exist_ok=True)
    for idx, img_url in enumerate(img_urls, start=1):
        try:
            fixed_url = get_fixed_url(img_url)
            img_data = requests.get(fixed_url, timeout=10).content
            img_path = os.path.join(base_path, f"{pid}_{idx}.jpg")
            with open(img_path, "wb") as img_file:
                img_file.write(img_data)
            print(f"✅ 이미지 저장 완료: {img_path}")
        except Exception as e:
            print(f"⚠ [ERROR] 이미지 저장 실패: {img_url}, 이유: {e}")

def download_product_data(goodsSn, goodsInfoCd, goodsInfoSn, save_path="downloads"):
    try:
        url = f"https://buykorea.org/ec/prd/goodsFileDownload.do?goodsSn={goodsSn}&goodsInfoCd={goodsInfoCd}&goodsInfoSn={goodsInfoSn}"
        response = requests.get(url, stream=True, timeout=10)

        if response.status_code == 200:
            os.makedirs(save_path, exist_ok=True)
            filename = os.path.join(save_path, f"{goodsSn}_{goodsInfoCd}_{goodsInfoSn}.pdf")
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"✅ 파일 다운로드 완료: {filename}")
        else:
            print(f"⚠ 다운로드 실패: {response.status_code}")
    except Exception as e:
        print(f"⚠ [ERROR] 파일 다운로드 실패: {url}, 이유: {e}")

def update_csv(csv_path, product_list):
    if not product_list:
        return

    keys = product_list[0].keys()
    temp_path = csv_path + ".tmp"

    with open(temp_path, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(product_list)

    os.replace(temp_path, csv_path)
    print(f"✅ CSV 업데이트 완료: {csv_path}")

def sanitize_filename(filename):
    filename = unicodedata.normalize("NFKD", filename)
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename.strip()

def main(start_index=0, end_index=None):
    ctgrycd_path = "ctgrycd"
    csv_files = [f for f in os.listdir(ctgrycd_path) if f.endswith(".csv")][start_index:end_index]

    for csv_file in csv_files:
        csv_path = os.path.join(ctgrycd_path, csv_file)

        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            product_list = [row for row in reader]

        for idx, product in enumerate(product_list):
            try:
                goods_sn = product["goodsSn"]
                print(f"상품 처리 시작 {idx} : {goods_sn}==========")
                product_data = fetch_product_details(goods_sn)

                if product_data is None:
                    continue  # 데이터 가져오기 실패 시 건너뜀

                category_path = os.path.join(
                    "Product Categories",
                    *[sanitize_filename(part) for part in product_data["list_location"].split(" > ")[2:]]
                )
                safe_title = sanitize_filename(product_data["title"])
                product_img_path = os.path.join(category_path, safe_title, "product_img")
                product_detail_path = os.path.join(category_path, safe_title, "detail_img")

                save_images(product_data["img_list"], product_img_path, product_data["PID"])
                save_images(product_data["detail_img_list"], product_detail_path, product_data["PID"])

                for goodsinfo in product_data["goodsinfo_list"]:
                    product_downloads_path = os.path.join(category_path, safe_title, "catalog_downloads")
                    download_product_data(product_data["PID"], goodsinfo['goodsinfocd'], goodsinfo['goodsinfosn'], product_downloads_path)

                product.update(product_data)
                print(f"상품 처리 끝 {idx} : {goods_sn}==========")
            except Exception as e:
                print(f"⚠ [ERROR] 상품 처리 실패: {goods_sn}, 이유: {e}")

        update_csv(csv_path, product_list)

if __name__ == "__main__":
    start_index = 0  # 시작 인덱스
    end_index = 1  # 종료 인덱스 (None이면 끝까지)

    main(start_index, end_index)
