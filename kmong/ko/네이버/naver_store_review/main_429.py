import requests
import json
import os
import pandas as pd
from datetime import datetime
from urllib.request import urlretrieve
import warnings
from requests.exceptions import Timeout, TooManyRedirects, RequestException, ConnectionError, HTTPError, URLRequired, MissingSchema, InvalidURL, SSLError
from urllib3.exceptions import InsecureRequestWarning
import logging
import time
import random

def setup_logging(log_level=logging.INFO):
    """
    로깅을 설정하는 함수

    :param log_level: 로그 레벨 (기본값 INFO)
    """
    # 로그 포맷 정의
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 로깅 설정 (콘솔에만 로그 출력)
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler()  # 콘솔에만 로그 출력
        ]
    )


# InsecureRequestWarning 경고 무시 설정
# 경고 메시지 무시: verify=False를 사용할 때 발생하는 SSL 경고(InsecureRequestWarning)를 숨기기 위해 사용
warnings.simplefilter('ignore', InsecureRequestWarning)

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



# 이미지 다운로드 함수
def download_images(attach_urls, attach_names, writer_id):
    folder_name = f"{writer_id}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    image_files = []
    for i, (url, name) in enumerate(zip(attach_urls[:9], attach_names[:9])):  # 최대 9개까지 다운로드
        image_path = os.path.join(folder_name, name)  # attach_name을 파일 이름으로 사용
        # 이미지 다운로드
        urlretrieve(url, image_path)
        image_files.append(name)

    return image_files


def parse_datetime(date_str):
    try:
        # createDate가 빈 문자열이 아니고, 형식이 맞을 경우 datetime으로 변환
        if date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f+00:00").strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ''  # 빈 문자열일 경우 빈 문자열 반환
    except ValueError:
        # ValueError 발생 시 잘못된 날짜 형식인 경우
        logging.error(f"Invalid date format: {date_str}")
        return ''  # 오류 발생 시 빈 문자열 반환


# 리뷰 데이터를 처리하고 Excel로 출력하는 함수
def process_reviews():
    result_data = []

    page = 1
    while True:
        time.sleep(random.uniform(1, 2))
        logging.info(f'\n')
        logging.info(f'시작 {page} ==========')

        reviews = reviews_request(page)

        # reviews가 None인 경우 종료
        if reviews is None:
            break

        if reviews and 'contents' in reviews:

            for review in reviews['contents']:
                review_data = {
                    '내용': review.get('reviewContent', ''),
                    '작성자': review.get('writerId', ''),
                    '작성시각': parse_datetime(review.get('createDate', '')),
                    '평점': review.get('reviewScore', ''),
                    '옵션': review.get('productOptionContent', ''),
                    '첨부파일': '',
                }
                # reviewAttaches 처리
                attach_urls = []
                attach_names = []
                if 'reviewAttaches' in review:
                    for attach in review['reviewAttaches']:
                        attach_url = attach.get('attachUrl')  # attachUrl이 없으면 None이 반환
                        attach_name = attach.get('attachName')  # attachName이 없으면 None이 반환

                        if attach_url and attach_name:  # attachUrl과 attachName이 모두 있을 경우에만 추가
                            attach_urls.append(attach_url)
                            attach_names.append(attach_name)

                    # 최대 9개까지 이미지 다운로드 및 이름 저장
                    image_files = download_images(attach_urls, attach_names, review_data['작성자'])
                    logging.info(f'image_files : {image_files}')
                    review_data['첨부파일'] = ",".join(attach_names[:9])  # 최대 9개까지 결합

                logging.info(f'page {page}, review_data : {review_data}')

                result_data.append(review_data)



        logging.info(f'끝 {page} ==========')

        page += 1

    # 결과를 DataFrame으로 변환 후 Excel로 저장
    df = pd.DataFrame(result_data)
    df.to_excel("reviews_result.xlsx", index=False)

# 메인 함수 실행
if __name__ == "__main__":

    # 설정 함수 호출
    setup_logging(log_level=logging.INFO)
    process_reviews()
