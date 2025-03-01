import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures

BASE_URL = "https://saphir1612.cafe24.com"
LIST_URL = f"{BASE_URL}/disp/admin/shop1/product/productmanage"
HEADERS = {
    "authority": "saphir1612.cafe24.com",
    "method": "GET",
    "scheme": "https",
    "cookie": "_fwb=40hz6iQBGce3ITf0SVRGcJ.1740328311559; _fbp=fb.1.1740328311778.145355876906639091; _gcl_au=1.1.613501043.1740328312; _hjSessionUser_2368957=eyJpZCI6IjRiZjUwMTc5LTg3YWEtNWVkOC1iM2NiLTgwMGQ5NDhjZmM0NSIsImNyZWF0ZWQiOjE3NDAzMjgzMTIwNjUsImV4aXN0aW5nIjp0cnVlfQ==; _ga_12RF674XCD=GS1.1.1740336113.2.0.1740336113.60.0.0; _clck=1ieqng%7C2%7Cftu%7C0%7C1880; _ga=GA1.1.1928481410.1740328313; PHPSESSID=c7feaea5ce0e14602280146ed65f2cc1; ECSESSID=2a8f552ac7df6cf82473a30beadfcbc6; is_pcver=T; is_mobile_admin=false; FROM_DCAFE=echosting; PHPSESSVERIFY=7c7b49a575dec3f5951b9cef310513d2; iscache=F; ec_mem_level=999999999; checkedImportantNotification=false; checkedFixedNotification=false; is_new_pro_mode=T; is_mode=false; ytshops_frame=; _ga_Z6CSBGDNRT=GS1.1.1740822219.3.1.1740822634.0.0.0; _ga_ZTM1Z99BLE=GS1.1.1740822220.2.1.1740822635.55.0.0; _ga_JC3MGH4M4T=GS1.1.1740822220.3.1.1740822635.0.0.0; _ga_TW9JR58492=GS1.1.1740822446.1.1.1740822658.37.0.0; cafe_user_name=saphir1612%2C%EC%83%81%ED%92%88%EA%B4%80%EB%A6%AC%2Cue1359.echosting.cafe24.com; PRODUCTMANAGE_LimitCnt=100; _clsk=1c9h4hh%7C1740829176783%7C3%7C1%7Cx.clarity.ms%2Fcollect; is_new_pro_mode_lnb_fold=T; _ga_EGNE1592YF=GS1.1.1740828852.3.1.1740829183.48.0.0",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

def parse_product_row(row):
    product = {}
    product_no_input = row.find_all("td")[0].find("input")
    product["product_no"] = product_no_input["value"] if product_no_input else ""

    goods_div = row.find_all("td")[4].find("div", class_="gGoods gMedium")
    if goods_div:
        p_tag = goods_div.find("p", recursive=False)
        if p_tag:
            a_tag = p_tag.find("a")
            if a_tag:
                product["product_name"] = a_tag.text.strip()
                href = a_tag["href"].strip()
                product["product_url"] = href if href.startswith("https") else f"{BASE_URL}{href}"

    ul_tag = goods_div.find("ul", class_="etc") if goods_div else None
    if ul_tag:
        li_tags = ul_tag.find_all("li")
        for i, li in enumerate(li_tags, start=1):
            label, values = li.text.split(" : ", 1) if " : " in li.text else ("", "")
            valid_values = [v.strip() for v in li.find_all(text=True) if v.strip() and (v.parent.name != "span" or "disabled" not in v.parent.get("class", []))]
            valid_values = list(dict.fromkeys(filter(None, valid_values)))
            cleaned_values = ", ".join(valid_values).split(":")[-1].strip()
            cleaned_values = " ".join(cleaned_values.split()).replace(", ", ",").lstrip(",").rstrip(",")
            while ",," in cleaned_values:
                cleaned_values = cleaned_values.replace(",,", ",")
            if cleaned_values:
                product[f"product_opt{i}_name"] = label.strip()
                product[f"product_opt{i}_value"] = cleaned_values
    return product

def fetch_page(page):
    print(f'fetch_page : {page}')
    params = {
        "page": page,
        "eField[]": "product_name",
        "Condition[]": "N",
        "origin_level1[]": "F",
        "product_type": "all",
        "eToggleDisplay": "on",
        "category": "0",
        "date": "regist",
        "date_type": "-1",
        "display": "A",
        "selling": "A",
        "market_selecter": "A",
        "market_search_type": "market",
        "UseStock": "A",
        "stockcount[]": "stock",
        "stock_importance": "T",
        "use_soldout": "A",
        "soldout_status": "A",
        "item_display": "A",
        "item_selling": "A",
        "price[]": "product",
        "orderby": "regist_d",
        "limit": "100",
        "default_column[shop_product_name]": "T",
        "default_column[sale_price]": "T",
        "default_column[mobile_sale_price]": "T",
        "bIsSearchClickAction": "T",
    }
    response = requests.get(LIST_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch page {page}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr", class_="ec-product-manage-list")
    return [parse_product_row(row) for row in rows]

def scrape_products():
    all_products = []
    pages = list(range(1, 339))
    print('시작')

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_page = {executor.submit(fetch_page, page): page for page in pages}
        for future in concurrent.futures.as_completed(future_to_page):
            result = future.result()
            if result:
                all_products.extend(result)

    return all_products

if __name__ == "__main__":
    product_list = scrape_products()
    df = pd.DataFrame(product_list)
    df.to_excel("product_data.xlsx", index=False)
    print("Excel file 'product_data.xlsx' has been saved.")
