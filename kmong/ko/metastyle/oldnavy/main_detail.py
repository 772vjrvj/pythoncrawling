import requests
from bs4 import BeautifulSoup

def get_product_info(pid, cid):
    url = "https://oldnavy.gap.com/browse/product.do"
    params = {"pid": pid, "cid": cid, "pcid": cid, "ctype": "Listing"}
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        obj = {
            "name": soup.find("h1", class_="sitewide-1t5lfed").get_text(strip=True) if soup.find("h1", class_="sitewide-1t5lfed") else "",
            "desc": "\n".join(li.get_text(strip=True) for li in soup.select(".drawer-trigger-container .sitewide-jxz45b:nth-of-type(2) .product-information-item__list li")) or "",
            "img_list": [
                (src if src.startswith("http") else f"https://oldnavy.gap.com/{src.lstrip('/')}")
                for src in [img["src"] for img in soup.select(".brick__product-image-wrapper img") if "src" in img.attrs]
            ]
        }
        return obj

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except Exception as e:
        return {"error": f"Parsing error: {e}"}

# 사용 예시
product = get_product_info("484662052", "3028309")
print(product)
