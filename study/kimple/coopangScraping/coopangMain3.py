from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
import warnings

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

AUTH = 'brd-customer-hl_7b5686a6-zone-scraping_browser1:1myeocpnrd19'
SBR_WEBDRIVER = f'https://{AUTH}@zproxy.lum-superproxy.io:9515'

host = "brd.superproxy.io:22225"
user_name = "brd-customer-hl_7b5686a6-zone-web_unlocker1"
password = "rl3in84k3t57"
proxy_url = f"https://{user_name}:{password}@{host}"

proxies = {"http": proxy_url, "https": proxy_url}

print(proxy_url)

keyword = input("검색할 제품 입력 : ")

link_list = []
for page_num in range(1, 2):
    print(f"<<<<<{page_num}페이지>>>>>")
    url = f"https://www.coupang.com/np/search?component=&q={keyword}&page={page_num}&listSize=36"
    print(url)
    print()
    response = requests.get(url, proxies=proxies, verify=False)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    #광고까지 가져옴
    # items = soup.select(".search-product")
    items = soup.select("[class=search-product]")

    print(len(items))

    for index, item in enumerate(items):

        name = item.select_one(".name").text
        price = item.select_one(".price-value")
        if not price:
            continue
        link = f"https://coupang.com{item.a['href']}"

        link_list.append(link)

        print(f"index : {index}")
        print(f"{name} : {price.text}")
        print(link)
        print()


print(link_list)
print(len(link_list))

for url in link_list:

    print('Connecting to Scraping Browser...')
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        print('Connected! Navigating...')
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        brand = soup.select_one(".prod-brand-name")
        brand = "" if not brand else brand.text.strip()

        title = soup.select_one(".prod-buy-header__title")
        title = "" if not title else title.text.strip()

        seller = soup.select_one(".prod-sale-vendor-name")
        seller = "로켓배송" if not seller else seller.text.strip()

        prod_sale_price = soup.select_one(".prod_sale-price") #현재 판매가
        prod_coupon_price = soup.select_one(".prod-coupon-price") #현재 할인가

        if prod_sale_price and prod_sale_price.select_one(".total-price"):
            prod_sale_price = prod_sale_price.select_one(".total-price").text.strip()
        else:
            prod_sale_price = ""


        if prod_coupon_price and prod_coupon_price.select_one(".total-price"):
            prod_coupon_price = prod_coupon_price.select_one(".total-price").text.strip()
        else:
            prod_coupon_price = ""

        print(f"브랜드: {brand}, 제품명: {title}, 현재 판매가: {prod_sale_price}, 회원 판매가: {prod_coupon_price}")

        prod_option_item = soup.select(".prod-option__item") # 옵션

        if prod_option_item:
            option_list = []
            for item in prod_option_item:
                title = item.select_one(".title").string.strip()
                value = item.select_one(".value").string.strip()
                option_list.append(f"{title}: {value}")
            prod_option_item = ", ".join(option_list)
            print(prod_option_item)
        else:
            prod_option_item = ""

        prod_description = soup.select(".prod-description .prod-attr-item") # 상세정보

        if prod_description:
            description_list = []
            for description in prod_description:
                description_list.append(description.string.strip())
            prod_description = ", ".join(description_list)
            print(prod_description)
        else:
            prod_description = ""

        print()