import requests
import logging
import warnings
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from urllib3.exceptions import InsecureRequestWarning


def reviews_request(page, timeout=30):

    # HTTP 요청 헤더 설정
    headers = {
        'authority': 'smartstore.naver.com',
        'method': 'POST',
        'path': '/i/v1/contents/reviews/query-pages',
        'scheme': 'https',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-length': '124',
        'content-type': 'application/json',
        'cookie': 'wcs_bt=s_93690c83369e:1735315445; NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; _fwb=4kg5BRewSJLxC4WQ2Js4e.1727705907262; tooltipDisplayed=true; NACT=1; 066c80626d06ffa5b32035f35cabe88d=%AD3%23%88%FC%DB%3Ey%FFx%A0j%AA%14f%0C%B1%CC%86%0C%E6a%84J%B9%BF%1B%CC%DF%F4%F4%07Z%0DS%7C%18%A1%D3Z%B9%ED%EE%11%98d%FE%C2%09%C6%FC%A5%F5H%EA9%F5%94%BD%BDE%0Bq%9D%23w%B8qq%91l%80%21%F6d%9F%2A%8D%3A%9Bd%02%BF%17%0B4%A1%2F%F4bl%28%01%83%BF-%E4%05oBN%E2VrA%402%0Ep%A2%B3X%C8Yq%0AN-T%B7%C6%F3%90%18H%DD0%FB%99%0D%2F%90%81G%8D%CB%ABu%D6%88%B1k%97%A1; 1a5b69166387515780349607c54875af=k%7Dh%BA%12%80%81%D2; SRT30=1735313626; SRT5=1735315428; nid_inf=184703044; NID_AUT=EYMGENH6moFheMGTEY84wHfhZiPtx+BJSt+pBXnXRRAGnw8NrzmqZLfqfkIMzmxT; NID_SES=AAABtAJMEwwQqFzKn0mK5z2PVYRcMoVBOGjeKxOVGkNONk7Fc8XHz6a/8P8zZTCFx+tGKJnZ+miAyDfTGYlUtfasYi4QS2WUOK/f4r43MVOum6k+6weTxLvOwQXnX5THowCzBQrhNRH5sD8iVu35C9N27tfToCP3KMHEU2G6e8THa86C3xRVFSquD2IgnoSY2ZiVF+GWPLDkUdVLOYCxQ/D9oDyH4MBO4yCBbTkeQVHLewmRqalHDp0WrRmZbWg65/Lj4lnjQbYfTEr1HysqpT5uxEALVwp5WwYOL8RV2A7bMjETaf4SuLAZ8Zg3z6/D8thmxCs+ZLtTU4u3XLzLPppZRA4H+QzDc9BsN/YCjcPfHepleIfiA46hkboHkQwHeXJwu2PRjlAEOd0+zYmXJCPQ1ztv33E1mT9+uYNoaw4vpizCqodTt4B6CjxCPRuFu8ehWkqmiCZHltPdrv6EsZyTrGZxv7FADWdD59j/svhEisYpJee5MgkCZlmiiPrFyNwbwDqEwvOUDuAh5m1gzQ8v35PO4Hmnlo9HjGESadi27155/nD1lhyNjMLKrKciEHpPYtPkqaXFyZhEapEmXNWNRNo=; NID_JKL=VDfVkZucGwGVLAh/nDcGTmTQ5pFM8deqtaxBNZ5EWQ8=; BUC=q7Ndyh7giM-l-LQMYdcdai5R1o7LPkqiVoPFsxZ_dnM=',
        'origin': 'https://smartstore.naver.com',
        'priority': 'u=1, i',
        'referer': 'https://smartstore.naver.com/foldableideas/products/5614699710',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-client-version': '20241226151221',
    }

    # 요청할 URL 설정
    url = "https://smartstore.naver.com/i/v1/contents/reviews/query-pages"

    # 요청할 페이로드 설정
    payload = {
        "checkoutMerchantNo": 511111508,  # 상점 번호
        "originProductNo": 5590313137,  # 제품 번호
        "page": page,  # 요청할 페이지 번호
        "pageSize": 20,  # 한 페이지에 담을 리뷰 수
        "reviewSearchSortType": "REVIEW_RANKING"  # 리뷰 정렬 기준 (랭킹 순)
    }
    proxies = {
        "http": "http://27.77.79.174:8080",  # HTTP 프록시
        "https": "https://27.77.79.174:8080"  # HTTPS 프록시
    }

    try:

        # POST 요청을 보내고 응답 받기
        # response = requests.post(url, headers=headers, json=payload, timeout=timeout, proxies=proxies)
        response = requests.post(url, headers=headers, data=payload, verify=True, timeout=timeout)

        # 응답의 인코딩을 UTF-8로 설정
        response.encoding = 'utf-8'

        # HTTP 상태 코드가 200이 아닌 경우 예외 처리
        response.raise_for_status()

        # 상태 코드가 200인 경우 응답 JSON 반환
        if response.status_code == 200:
            return response.json()  # JSON 형식으로 응답 반환
        else:
            # 상태 코드가 200이 아닌 경우 로그 기록
            logging.error(f"Unexpected status code: {response.status_code}")
            return None

    # 타임아웃 오류 처리
    except Timeout:
        logging.error("Request timed out")
        return None

    # 너무 많은 리다이렉트 발생 시 처리
    except TooManyRedirects:
        logging.error("Too many redirects")
        return None

    # 네트워크 연결 오류 처리
    except ConnectionError:
        logging.error("Network connection error")
        return None

    # HTTP 응답 코드가 4xx 또는 5xx일 경우 처리
    except HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
        return None

    # URL이 유효하지 않거나 제공되지 않았을 경우 처리
    except URLRequired:
        logging.error("A valid URL is required")
        return None

    # SSL 인증서 오류 처리
    except SSLError:
        logging.error("SSL certificate verification failed")
        return None

    # 기타 모든 예외 처리
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    # 예상치 못한 예외 처리
    except Exception as e:
        logging.error(f"Unexpected exception: {e}")
        return None
