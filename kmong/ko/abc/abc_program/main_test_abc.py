def brand_api_name_list(self, brand_no):
    brand_name_list = []
    url = "https://onthespot.com/display/search-word/smart-option/list"
    payload = {
        "searchPageType": "brand",
        "page": "1",
        "pageColumn": "4",
        "deviceCode": "10000",
        "firstSearchYn": "Y",
        "tabGubun": "total",
        "searchPageGubun": "brsearch",
        "searchRcmdYn": "Y",
        "brandNo": f"{brand_no}",
        # "_": "1736952631519"
    }
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "abcmart.a-rt.com",
        "referer": f"https://abcmart.a-rt.com/product/brand/page/main?brandNo=={brand_no}",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    try:
        response = self.sess.get(url, headers=headers, params=payload)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        data = response.json()
        brand_name_list = data.get("SELECT", {}).get("BRAND_LIST", [])
    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 에러: {e}")
    except Exception as e:
        print(f"알 수 없는 에러 발생: {e}")
    finally:
        return brand_name_list