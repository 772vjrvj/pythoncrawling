import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import os



def fetch_search_results(query, page):
    try:
        url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Referer': '',
            'Cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; page_uid=ixPkCsqo15VssueBrYsssssstUV-337987; NACT=1; nid_inf=391334397; NID_AUT=AkHBiaJ3C4EjzWnGbBaqiTSmzoP+ueiVC84APMXvj6smfuLXcHYNZ3oelKEPvm1C; NID_JKL=besn+Kf8iK3gVT9ZFSBdXuR7Vz3Y254B1dRljq2xqWg=; NID_SES=AAABpzILtWv/VocpJax4U8X7VC7woOBVWTQqPmI2Q/UryKdNzakhGcJOlp1dIzu7AxYOHHv2XV1ARABxDRbcyID0lzZWwtEWYY5UEHycWROo3nUH1JaoxQ3QXzQsFjs6D4QxF0vxtaxM3OixO0gpORofdUcVqCdpzEKq/jMWa/GmLPbOV8JnlMzqtFOZodvSB6a3u8K1RuvxT7zJ2wfE6DewALFJjhfmq2quz5MjoGMx4WH4vNRTg/Ujy/I8eiiDYIi5n1CMw1jegIsW33+a8mgnh1IGbRDT/jc0b18TLX3/YHdSxqVA4sUuI1yqY3e4wM8wm7GRuF8QTmOKH+Sthbn1FZ9nlOmFVNNHSo806tml5v+n7Km2tRHx8gS+kvouXPpOiEaiOCCLkpDtLrhAdKCFv7UGdlIaEwpLokv/yiowwh9l3kJIoCGGIz2XbstSdDqH/+klaDXDNgF3ThQ1VSCXnKCVZTNRV8oNFsWBleXsLol5dqW642NNaWRHHuD7kLZtAeZQGaIae5a6GRN1fiYJdRLwMmF2sOg4AieLgXXq8IXOPQiATMrCU8BClpyfBtn2cQ==; _naver_usersession_=K3Q05oOrwdRKJlLUub4B645m; BUC=lLlQEsDUA5pZpYRCYhvKzWaaeEJgPQz4xjly0U4DjrU='
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch search results: {e}")
    return None

def fetch_photos(place_id):
    url = "https://api.place.naver.com/graphql"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; page_uid=ixPkCsqo15VssueBrYsssssstUV-337987; NACT=1; nid_inf=391334397; NID_AUT=AkHBiaJ3C4EjzWnGbBaqiTSmzoP+ueiVC84APMXvj6smfuLXcHYNZ3oelKEPvm1C; NID_JKL=besn+Kf8iK3gVT9ZFSBdXuR7Vz3Y254B1dRljq2xqWg=; NID_SES=AAABpzILtWv/VocpJax4U8X7VC7woOBVWTQqPmI2Q/UryKdNzakhGcJOlp1dIzu7AxYOHHv2XV1ARABxDRbcyID0lzZWwtEWYY5UEHycWROo3nUH1JaoxQ3QXzQsFjs6D4QxF0vxtaxM3OixO0gpORofdUcVqCdpzEKq/jMWa/GmLPbOV8JnlMzqtFOZodvSB6a3u8K1RuvxT7zJ2wfE6DewALFJjhfmq2quz5MjoGMx4WH4vNRTg/Ujy/I8eiiDYIi5n1CMw1jegIsW33+a8mgnh1IGbRDT/jc0b18TLX3/YHdSxqVA4sUuI1yqY3e4wM8wm7GRuF8QTmOKH+Sthbn1FZ9nlOmFVNNHSo806tml5v+n7Km2tRHx8gS+kvouXPpOiEaiOCCLkpDtLrhAdKCFv7UGdlIaEwpLokv/yiowwh9l3kJIoCGGIz2XbstSdDqH/+klaDXDNgF3ThQ1VSCXnKCVZTNRV8oNFsWBleXsLol5dqW642NNaWRHHuD7kLZtAeZQGaIae5a6GRN1fiYJdRLwMmF2sOg4AieLgXXq8IXOPQiATMrCU8BClpyfBtn2cQ==; _naver_usersession_=K3Q05oOrwdRKJlLUub4B645m; BUC=lLlQEsDUA5pZpYRCYhvKzWaaeEJgPQz4xjly0U4DjrU=',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Origin': 'https://m.place.naver.com',
        'Referer': f'https://m.place.naver.com/place/{place_id}/home'
    }
    payload = [
        {
            "operationName": "getPhotoViewerItems",
            "variables": {
                "input": {
                    "businessId": place_id,
                    "businessType": "restaurant",
                    "cursors": [
                        {"id": "biz"},
                        {"id": "cp0"},
                        {"id": "visitorReview"},
                        {"id": "clip"},
                        {"id": "imgSas"}
                    ],
                    "excludeAuthorIds": [],
                    "excludeSection": [],
                    "excludeClipIds": [],
                    "dateRange": ""
                }
            },
            "query": """
            query getPhotoViewerItems($input: PhotoViewerInput) {
              photoViewer(input: $input) {
                cursors {
                  id
                  startIndex
                  hasNext
                  lastCursor
                  __typename
                }
                photos {
                  viewId
                  originalUrl
                  width
                  height
                  title
                  text
                  desc
                  link
                  date
                  photoType
                  mediaType
                  option {
                    channelName
                    dateString
                    playCount
                    likeCount
                    __typename
                  }
                  to
                  relation
                  logId
                  author {
                    id
                    nickname
                    from
                    imageUrl
                    objectId
                    url
                    borderImageUrl
                    __typename
                  }
                  votedKeywords {
                    code
                    iconUrl
                    iconCode
                    displayName
                    __typename
                  }
                  visitCount
                  originType
                  isFollowing
                  businessName
                  rating
                  externalLink {
                    title
                    url
                    __typename
                  }
                  sourceTitle
                  moment {
                    channelId
                    contentId
                    momentId
                    gdid
                    blogRelation
                    statAllowYn
                    category
                    docNo
                    __typename
                  }
                  video {
                    videoId
                    videoUrl
                    trailerUrl
                    __typename
                  }
                  music {
                    artists
                    title
                    __typename
                  }
                  clip {
                    viewerHash
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
            """
        }
    ]
    image_urls = []
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        data = response.json()

        # 원하는 데이터 추출 예시 (originalUrl만 추출)
        photos = data[0].get('data', {}).get('photoViewer', {}).get('photos', [])
        for photo in photos:
            image_urls.append(photo.get('originalUrl'))

        return image_urls[:5]

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return image_urls

def download_image(image_url, save_path):
    try:
        img_data = requests.get(image_url).content
        with open(save_path, 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")

def fetch_reviews(place_id):
    try:
        url = "https://api.place.naver.com/place/graphql"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; page_uid=ixPkCsqo15VssueBrYsssssstUV-337987; NACT=1; nid_inf=391334397; NID_AUT=AkHBiaJ3C4EjzWnGbBaqiTSmzoP+ueiVC84APMXvj6smfuLXcHYNZ3oelKEPvm1C; NID_JKL=besn+Kf8iK3gVT9ZFSBdXuR7Vz3Y254B1dRljq2xqWg=; NID_SES=AAABpzILtWv/VocpJax4U8X7VC7woOBVWTQqPmI2Q/UryKdNzakhGcJOlp1dIzu7AxYOHHv2XV1ARABxDRbcyID0lzZWwtEWYY5UEHycWROo3nUH1JaoxQ3QXzQsFjs6D4QxF0vxtaxM3OixO0gpORofdUcVqCdpzEKq/jMWa/GmLPbOV8JnlMzqtFOZodvSB6a3u8K1RuvxT7zJ2wfE6DewALFJjhfmq2quz5MjoGMx4WH4vNRTg/Ujy/I8eiiDYIi5n1CMw1jegIsW33+a8mgnh1IGbRDT/jc0b18TLX3/YHdSxqVA4sUuI1yqY3e4wM8wm7GRuF8QTmOKH+Sthbn1FZ9nlOmFVNNHSo806tml5v+n7Km2tRHx8gS+kvouXPpOiEaiOCCLkpDtLrhAdKCFv7UGdlIaEwpLokv/yiowwh9l3kJIoCGGIz2XbstSdDqH/+klaDXDNgF3ThQ1VSCXnKCVZTNRV8oNFsWBleXsLol5dqW642NNaWRHHuD7kLZtAeZQGaIae5a6GRN1fiYJdRLwMmF2sOg4AieLgXXq8IXOPQiATMrCU8BClpyfBtn2cQ==; _naver_usersession_=K3Q05oOrwdRKJlLUub4B645m; BUC=lLlQEsDUA5pZpYRCYhvKzWaaeEJgPQz4xjly0U4DjrU=',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Origin': f'https://m.place.naver.com',
            'Referer': f'https://m.place.naver.com/place/{place_id}/home'
        }

        payload = [
            {
                "operationName": "getVisitorReviews",
                "variables": {
                    "input": {
                        "businessId": place_id,
                        "businessType": "place",
                        "size": 7,
                        "page": 1,
                        "includeContent": True,
                        "cidList": ["222412", "222415", "222446", "1004920"]
                    }
                },
                "query": """
                query getVisitorReviews($input: VisitorReviewsInput) {
                  visitorReviews(input: $input) {
                    items {
                      id
                      rating
                      author {
                        nickname
                        imageUrl
                      }
                      body
                      created
                      tags
                      media {
                        type
                        thumbnail
                      }
                    }
                    total
                  }
                }"""
            },
            {
                "operationName": "getVisitorReviewStats",
                "variables": {
                    "businessType": "place",
                    "id": place_id
                },
                "query": """
                query getVisitorReviewStats($id: String, $businessType: String = "place") {
                  visitorReviewStats(input: {businessId: $id, businessType: $businessType}) {
                    id
                    name
                    review {
                      avgRating
                      totalCount
                    }
                    analysis {
                      votedKeyword {
                        totalCount
                        reviewCount
                        userCount
                        details {
                          code
                          iconUrl
                          displayName
                          count
                        }
                      }
                    }
                  }
                }"""
            }
        ]

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        review_data = response.json()

        if review_data and len(review_data) > 1:
            visitor_reviews_data = review_data[0].get("data", {}).get("visitorReviews", {})
            visitor_reviews = visitor_reviews_data.get("items", []) if visitor_reviews_data else []

            analysis_data = review_data[1].get("data", {}).get("visitorReviewStats", {})
            voted_keyword_data = analysis_data.get("analysis", {}) if analysis_data else {}

            # 여기서 votedKeyword가 None일 때를 추가로 처리
            voted_keyword_details = (
                voted_keyword_data.get("votedKeyword", {}).get("details", [])
                if voted_keyword_data.get("votedKeyword") is not None
                else []
            )

            return {
                "reviews": visitor_reviews,
                "stats": voted_keyword_details
            }
        else:
            print(f"No review data available for Place ID: {place_id}")
            return {"reviews": [], "stats": []}

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch reviews for Place ID: {place_id}. Error: {e}")
        return {"reviews": [], "stats": []}
    except Exception as e:
        print(f"Error while processing data for Place ID: {place_id}: {e}")
        return {"reviews": [], "stats": []}

def fetch_link_url(place_id):
    url = "https://me2do.naver.com/common/requestJsonpV2"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "me2do.naver.com",
        "referer": f"https://pcmap.place.naver.com/{place_id}/home?from=map&fromPanelNum=1&additionalHeight=76&timestamp=202410090914",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "cookie": 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; page_uid=ixPkCsqo15VssueBrYsssssstUV-337987; NACT=1; nid_inf=391334397; NID_AUT=AkHBiaJ3C4EjzWnGbBaqiTSmzoP+ueiVC84APMXvj6smfuLXcHYNZ3oelKEPvm1C; NID_JKL=besn+Kf8iK3gVT9ZFSBdXuR7Vz3Y254B1dRljq2xqWg=; NID_SES=AAABpzILtWv/VocpJax4U8X7VC7woOBVWTQqPmI2Q/UryKdNzakhGcJOlp1dIzu7AxYOHHv2XV1ARABxDRbcyID0lzZWwtEWYY5UEHycWROo3nUH1JaoxQ3QXzQsFjs6D4QxF0vxtaxM3OixO0gpORofdUcVqCdpzEKq/jMWa/GmLPbOV8JnlMzqtFOZodvSB6a3u8K1RuvxT7zJ2wfE6DewALFJjhfmq2quz5MjoGMx4WH4vNRTg/Ujy/I8eiiDYIi5n1CMw1jegIsW33+a8mgnh1IGbRDT/jc0b18TLX3/YHdSxqVA4sUuI1yqY3e4wM8wm7GRuF8QTmOKH+Sthbn1FZ9nlOmFVNNHSo806tml5v+n7Km2tRHx8gS+kvouXPpOiEaiOCCLkpDtLrhAdKCFv7UGdlIaEwpLokv/yiowwh9l3kJIoCGGIz2XbstSdDqH/+klaDXDNgF3ThQ1VSCXnKCVZTNRV8oNFsWBleXsLol5dqW642NNaWRHHuD7kLZtAeZQGaIae5a6GRN1fiYJdRLwMmF2sOg4AieLgXXq8IXOPQiATMrCU8BClpyfBtn2cQ==; _naver_usersession_=K3Q05oOrwdRKJlLUub4B645m; BUC=lLlQEsDUA5pZpYRCYhvKzWaaeEJgPQz4xjly0U4DjrU=',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    params = {
        "_callback": "window.spi_9197316230",
        "svcCode": "0022",
        "url": f"https://m.place.naver.com/share?id={place_id}&tabsPath=%2Fhome&appMode=detail"
    }
    link_url = ""
    try:
        # GET 요청 보내기
        response = requests.get(url, headers=headers, params=params)

        # 응답 내용에서 콜백 함수 제거 (JSON 부분만 추출하기 위해 정규 표현식 사용)
        jsonp_data = response.text
        json_data = re.search(r'window\.spi_9197316230\((.*)\)', jsonp_data).group(1)

        # 추출된 JSON 문자열을 파이썬 딕셔너리로 변환
        data = json.loads(json_data)

        # 필요한 'url' 값 출력
        print(data['result']['url'])
        link_url = data['result']['url']
        return link_url

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return link_url

def fetch_place_info(idx, place_id):
    try:
        url = f"https://m.place.naver.com/place/{place_id}"
        headers = {
            'authority': 'm.place.naver.com',
            'method': 'GET',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; page_uid=ixPkCsqo15VssueBrYsssssstUV-337987; NACT=1; nid_inf=391334397; NID_AUT=AkHBiaJ3C4EjzWnGbBaqiTSmzoP+ueiVC84APMXvj6smfuLXcHYNZ3oelKEPvm1C; NID_JKL=besn+Kf8iK3gVT9ZFSBdXuR7Vz3Y254B1dRljq2xqWg=; NID_SES=AAABpzILtWv/VocpJax4U8X7VC7woOBVWTQqPmI2Q/UryKdNzakhGcJOlp1dIzu7AxYOHHv2XV1ARABxDRbcyID0lzZWwtEWYY5UEHycWROo3nUH1JaoxQ3QXzQsFjs6D4QxF0vxtaxM3OixO0gpORofdUcVqCdpzEKq/jMWa/GmLPbOV8JnlMzqtFOZodvSB6a3u8K1RuvxT7zJ2wfE6DewALFJjhfmq2quz5MjoGMx4WH4vNRTg/Ujy/I8eiiDYIi5n1CMw1jegIsW33+a8mgnh1IGbRDT/jc0b18TLX3/YHdSxqVA4sUuI1yqY3e4wM8wm7GRuF8QTmOKH+Sthbn1FZ9nlOmFVNNHSo806tml5v+n7Km2tRHx8gS+kvouXPpOiEaiOCCLkpDtLrhAdKCFv7UGdlIaEwpLokv/yiowwh9l3kJIoCGGIz2XbstSdDqH/+klaDXDNgF3ThQ1VSCXnKCVZTNRV8oNFsWBleXsLol5dqW642NNaWRHHuD7kLZtAeZQGaIae5a6GRN1fiYJdRLwMmF2sOg4AieLgXXq8IXOPQiATMrCU8BClpyfBtn2cQ==; _naver_usersession_=K3Q05oOrwdRKJlLUub4B645m; BUC=lLlQEsDUA5pZpYRCYhvKzWaaeEJgPQz4xjly0U4DjrU=',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'referer': '',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', string=re.compile('window.__APOLLO_STATE__'))

            if script_tag:
                json_text = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*\});', script_tag.string)
                if json_text:
                    data = json.loads(json_text.group(1))

                    name = data.get(f"PlaceDetailBase:{place_id}", {}).get("name", "")
                    road = data.get(f"PlaceDetailBase:{place_id}", {}).get("road", "")
                    address = data.get(f"PlaceDetailBase:{place_id}", {}).get("address", "")
                    roadAddress = data.get(f"PlaceDetailBase:{place_id}", {}).get("roadAddress", "")
                    category = data.get(f"PlaceDetailBase:{place_id}", {}).get("category", "")
                    conveniences = data.get(f"PlaceDetailBase:{place_id}", {}).get("conveniences", [])
                    virtualPhone = data.get(f"PlaceDetailBase:{place_id}", {}).get("virtualPhone", [])
                    visitorReviewsScore = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsScore", "")
                    visitorReviewsTotal = data.get(f"PlaceDetailBase:{place_id}", {}).get("visitorReviewsTotal", "")

                    root_query = data.get("ROOT_QUERY", {})
                    place_detail_key = f'placeDetail({{"input":{{"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                    # 기본 place_detail_key 값이 없으면 checkRedirect 포함된 key로 재시도
                    if place_detail_key not in root_query:
                        place_detail_key = f'placeDetail({{"input":{{"checkRedirect":true,"deviceType":"pc","id":"{place_id}","isNx":false}}}})'

                    fsasReviewsTotal = root_query.get(place_detail_key, {}).get('fsasReviews', {}).get("total", "")
                    if not fsasReviewsTotal:
                        fsasReviewsTotal = root_query.get(place_detail_key, {}).get("fsasReviews({\"fsasReviewsType\":\"restaurant\"})", {}).get("total", "")

                    # business_hours 초기 시도
                    business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"shopWindow\"]})", [])

                    # business_hours 값이 없으면 다른 source를 시도
                    if not business_hours:
                        business_hours = root_query.get(place_detail_key, {}).get("businessHours({\"source\":[\"tpirates\",\"jto\",\"shopWindow\"]})", [])

                    new_business_hours_json = root_query.get(place_detail_key, {}).get('newBusinessHours', [])

                    if not new_business_hours_json:
                        new_business_hours_json = root_query.get(place_detail_key, {}).get("newBusinessHours({\"format\":\"restaurant\"})", [])

                    # 별점, 방문자 리뷰 수, 블로그 리뷰 수가 0이거나 없으면 공백 처리
                    visitorReviewsScore = visitorReviewsScore if visitorReviewsScore and visitorReviewsScore != "0" else ""
                    visitorReviewsTotal = visitorReviewsTotal if visitorReviewsTotal and visitorReviewsTotal != "0" else ""
                    fsasReviewsTotal = fsasReviewsTotal if fsasReviewsTotal and fsasReviewsTotal != "0" else ""

                    # category를 대분류와 소분류로 나누기
                    category_list = category.split(',') if category else ["", ""]
                    main_category = category_list[0] if len(category_list) > 0 else ""
                    sub_category = category_list[1] if len(category_list) > 1 else ""

                    url = f"https://m.place.naver.com/place/{place_id}/home"
                    map_url = f"https://map.naver.com/p/entry/place/{place_id}"

                    urls = []
                    homepages = root_query.get(place_detail_key, {}).get('shopWindow', {}).get("homepages", "")
                    if homepages:
                        # etc 배열에서 url 가져오기
                        for item in homepages.get("etc", []):
                            urls.append(item.get("url", ""))

                        # repr의 url 가져오기
                        repr_data = homepages.get("repr")
                        repr_url = repr_data.get("url", "") if repr_data else ""
                        if repr_url:
                            urls.append(repr_url)

                    result = {
                        "이름": name,
                        "주소(지번)": address,
                        "주소(도로명)": roadAddress,
                        "대분류": main_category,
                        "소분류": sub_category,
                        "별점": visitorReviewsScore,
                        "방문자리뷰수": visitorReviewsTotal,
                        "블로그리뷰수": fsasReviewsTotal,
                        "이용시간1": format_business_hours(business_hours),
                        "이용시간2": format_new_business_hours(new_business_hours_json),
                        "카테고리": category,
                        "URL": url,
                        "지도": map_url,
                        "편의시설": ', '.join(conveniences) if conveniences else '',

                        "전화번호": virtualPhone,
                        "사이트": urls,
                        "주소지정보": road,
                    }

                    reviews_info = fetch_reviews(place_id)
                    # nickname과 body만 추출
                    simplified_reviews = [{'아이디': review['author']['nickname'], '내용': review['body']} for review in reviews_info.get("reviews", [])]

                    # 예쁘게 JSON 출력
                    pretty_json = json.dumps(simplified_reviews, ensure_ascii=False, indent=4)
                    result["리뷰"] = pretty_json

                    image_urls = fetch_photos(place_id)
                    os.makedirs(f'images/{query}/{idx}. {name}', exist_ok=True)
                    for i, image_url in enumerate(image_urls, start=1):
                        download_image(image_url, f'images/{query}/{idx}. {name}/{name}_{i}.jpg')
                    result['이미지 URLs'] = json.dumps(image_urls, ensure_ascii=False, indent=4)

                    ## 메뉴 처리
                    menus = []
                    menu_index = 0
                    while True:
                        # Menu 데이터를 순차적으로 가져오기
                        menu = data.get(f"Menu:{place_id}_{menu_index}", {})
                        if not menu:
                            break
                        # 필요한 정보만 추출하여 메뉴 배열에 담기
                        menus.append({
                            '이름': menu.get('name', ''),
                            '가격': menu.get('price', ''),
                            'images': menu.get('images', [])
                        })
                        menu_index += 1

                    # 다운로드 경로 설정

                    os.makedirs(f'menu/{query}/{idx}. {name}', exist_ok=True)
                    result['메뉴'] = json.dumps(menus, ensure_ascii=False, indent=4)

                    # 메뉴 배열 순회
                    for menu in menus:
                        menu_name = menu['이름']

                        # 이미지 다운로드
                        for image_idx, image_url in enumerate(menu['images']):
                            image_name = f"{menu_name}_{idx}.jpg"
                            download_image(image_url, f'menu/{query}/{idx}. {name}/{image_name}')

                    return result

    except requests.exceptions.RequestException as e:
        new_print(f"Failed to fetch data for Place ID: {place_id}. Error: {e}")
    except Exception as e:
        new_print(f"Error processing data for Place ID: {place_id}: {e}")
    return None

def format_business_hours(business_hours):
    formatted_hours = []
    try:
        if business_hours:
            for hour in business_hours:
                day = hour.get('day', '') or ''
                start_time = hour.get('startTime', '') or ''
                end_time = hour.get('endTime', '') or ''
                if day and start_time and end_time:
                    formatted_hours.append(f"{day} {start_time} - {end_time}")
    except Exception as e:
        new_print(f"Unexpected error: {e}")
        return ""
    return '\n'.join(formatted_hours).strip() if formatted_hours else ""

def format_new_business_hours(new_business_hours):
    formatted_hours = []
    try:
        if new_business_hours:
            for item in new_business_hours:
                status_description = item.get('businessStatusDescription', {}) or {}
                status = status_description.get('status', '') or ''
                description = status_description.get('description', '') or ''

                if status:
                    formatted_hours.append(status)
                if description:
                    formatted_hours.append(description)

                for info in item.get('businessHours', []) or []:
                    day = info.get('day', '') or ''
                    business_hours = info.get('businessHours', {}) or {}
                    start_time = business_hours.get('start', '') or ''
                    end_time = business_hours.get('end', '') or ''

                    break_hours = info.get('breakHours', []) or []
                    break_times = [f"{bh.get('start', '') or ''} - {bh.get('end', '') or ''}" for bh in break_hours]
                    break_times_str = ', '.join(break_times) + ' 브레이크타임' if break_times else ''

                    last_order_times = info.get('lastOrderTimes', []) or []
                    last_order_times_str = ', '.join([f"{lo.get('type', '')}: {lo.get('time', '')}" for lo in last_order_times]) + ' 라스트오더' if last_order_times else ''

                    if day:
                        formatted_hours.append(day)
                    if start_time and end_time:
                        formatted_hours.append(f"{start_time} - {end_time}")
                    if break_times_str:
                        formatted_hours.append(break_times_str)
                    if last_order_times_str:
                        formatted_hours.append(last_order_times_str)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ""
    return '\n'.join(formatted_hours).strip() if formatted_hours else ""

def new_print(text, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"[{timestamp}] [{level}] {text}"
    print(formatted_text)

def append_to_excel(data, filename="서울시 맛집1.xlsx"):
    df = pd.DataFrame(data)

    try:
        # 기존 파일이 있을 경우 파일을 열고 데이터를 추가
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            workbook = load_workbook(filename)
            sheet_name = workbook.sheetnames[0]  # 첫 번째 시트 이름 가져오기
            startrow = writer.sheets[sheet_name].max_row  # 기존 데이터의 마지막 행 번호
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=startrow)
    except FileNotFoundError:
        # 파일이 없을 경우 새로 생성
        df.to_excel(filename, index=False)

def main(query):
    try:
        page = 1
        results = []
        all_ids = set()

        new_print(f"크롤링 시작")
        # 아이디 추출
        while True:
            result = fetch_search_results(query, page)
            if not result:
                break

            place_list = result.get("result", {}).get("place", {}).get("list", [])
            ids_this_page = [place.get("id") for place in place_list if place.get("id")]

            new_print(f"페이지 : {page}, 목록 : {ids_this_page}")

            if not ids_this_page:
                break

            all_ids.update(ids_this_page)
            page += 1
            time.sleep(random.uniform(2, 3))
            break

        all_ids_list = list(all_ids)
        total_count = len(all_ids_list)
        new_print(f"전체 매물 수 : {total_count}")

        for idx, place_id in enumerate(all_ids_list, start=1):
            place_info = fetch_place_info(idx, place_id)
            if place_info:
                place_info["검색어"] = query
                new_print(place_info)
                results.append(place_info)
                time.sleep(random.uniform(2, 3))
            break

        return results

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    names = [
        "오마카세 오사이초밥 홍대점",
        # "가락시장 홍홍"
    ]
    # names = ["가락 진성한우곱창", "가락시장 홍홍"]
    # 현재 시간 가져오기
    current_time = datetime.now().strftime("%Y%m%d%H%M")
    # 파일 이름에 시간 추가
    filename = f"오마카세 오사이초밥 홍대점_{current_time}.xlsx"
    for index, name in enumerate(names, start=1):
        new_print(f"Total : {len(names)}, index : {index}, name : {name}==============================================")
        query = f"{name}"
        rs = main(query)
        if rs:
            append_to_excel(rs, filename=filename)

        new_print(f"============================================================================")
