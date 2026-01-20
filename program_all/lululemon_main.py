import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from decimal import Decimal


def shorten_color(color: str) -> str:
    color = (color or "").strip()
    if len(color) <= 25:
        return color

    parts = [p for p in color.split() if p]
    if not parts:
        return color[:25]

    first = parts[0]
    tail = "".join(p[0].upper() for p in parts[1:] if p)
    short = (first + " " + tail).strip()

    # 그래도 25 넘으면 강제로 컷 (안전장치)
    return short[:25]


def fetch_options(url: str):
    u = urlparse(url)
    authority = u.netloc
    path = u.path + (("?" + u.query) if u.query else "")
    origin = f"{u.scheme}://{u.netloc}"
    referer = origin + "/"

    headers = {
        "authority": authority,
        "method": "GET",
        "path": path,
        "scheme": u.scheme,

        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",

        "host": authority,
        "origin": origin,
        "referer": referer,
    }

    s = requests.Session()

    # s.cookies.set("cookie_name", "", domain=authority, path="/")

    s.get(referer, headers=headers, timeout=20)
    resp = s.get(url, headers=headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    productgroup = None
    for sc in scripts:
        if not sc.string:
            continue
        try:
            data = json.loads(sc.string)
        except Exception:
            continue

        try:
            data.get("@type")
            objs = [data]
        except Exception:
            objs = data

        for obj in objs:
            try:
                if obj.get("@type") == "ProductGroup" and obj.get("hasVariant"):
                    productgroup = obj
                    break
            except Exception:
                continue
        if productgroup:
            break

    if not productgroup:
        print("[]")
        return

    variants = productgroup.get("hasVariant") or []
    rows = []

    for v in variants:
        color = (v.get("color") or "").strip()
        size = (v.get("size") or "").strip()

        nm = (v.get("name") or "").strip()
        if nm and (not color or not size):
            parts = [p.strip() for p in nm.split(" - ")]
            if len(parts) >= 3:
                if not color:
                    color = parts[-2]
                if not size:
                    size = parts[-1]

        offers = v.get("offers") or []
        offer0 = offers[0] if offers else {}

        priceCurrency = (offer0.get("priceCurrency") or "").strip()
        price = (offer0.get("price") or "").strip()
        availability = (offer0.get("availability") or "").strip()

        rows.append({
            "color": color,
            "size": size,
            "priceCurrency": priceCurrency,
            "price": price,
            "availability": availability,
        })

    min_price = None
    for r in rows:
        try:
            p = Decimal(r["price"])
        except Exception:
            continue
        if min_price is None or p < min_price:
            min_price = p

    def size_key(sv):
        try:
            return int(sv)
        except Exception:
            return 10**9

    rows.sort(key=lambda r: (r["color"], size_key(r["size"])))

    out = []
    for r in rows:
        in_stock = "Y" if r["availability"].endswith("InStock") else "N"

        opt = 0
        if min_price is not None and r["priceCurrency"] == "CAD":
            try:
                diff = Decimal(r["price"]) - min_price
                if diff > 0:
                    opt = int(diff) * 1000
            except Exception:
                opt = 0

        out.append({
            "컬러": shorten_color(r["color"]),
            "사이즈": r["size"],
            "옵션가": opt,
            "재고수량": 5 if in_stock == "Y" else 0,
            "관리코드":"",
            "사용여부": "Y",
        })

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_url = "https://shop.lululemon.com/en-ca/p/womens-leggings/Align-Pant-2/_/prod2020015?color=30210&sz=18"
    fetch_options(test_url)
