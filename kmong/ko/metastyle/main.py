import requests

def get_cc_list(cid, pageNumber):
    url = "https://api.gap.com/commerce/search/products/v2/cc"
    params = {
        "brand": "on",
        "market": "us",
        "cid": cid,
        "locale": "en_US",
        "pageSize": "300",
        "ignoreInventory": "false",
        "includeMarketingFlagsDetails": "true",
        "enableDynamicFacets": "true",
        "enableSwatchSort": "true",
        "sortSwatchesBy": "bestsellers",
        "pageNumber": pageNumber,
        "vendor": "Certona",
    }
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://oldnavy.gap.com",
        "referer": "https://oldnavy.gap.com/",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "x-client-application-name": "Browse"
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        return [category.get("ccList", []) for category in data.get("categories", [])]

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except Exception as e:
        return {"error": f"Parsing error: {e}"}



# 사용 예시
cc_list = get_cc_list("3028309", "2")
print(cc_list)
