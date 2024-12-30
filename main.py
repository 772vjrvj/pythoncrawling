import requests
import json

# 요청 URL
url = "https://pcmap-api.place.naver.com/graphql"

# 요청 헤더 설정
headers = {
    'scheme': 'https',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'ko',
    'content-type': 'application/json',
    'cookie': 'NNB=2HHDT25LLBYWO; SRT30=1735481515; NAC=qpjLBcAU3Vpv; NACT=1; nid_inf=192615909; NID_AUT=6aZ2xXToKW+4coczi2XBP47AbmOvpRo1TYrhdD1eZdFgUFp9uIVMXsrWNyDANqza; NID_SES=AAABu7zftQtFzn8hBy4CLHXJPPQQba9XcbMfOvQ9Z5cDiUjRQ59h25vV9W0QOhdz4b3UNsAGginZM4qHBgFMJy8DYhcFWqfB2lSuLh0UjpPZpT/lI56psQrI1UszWeH9BByDA3Zk6fccfLUG7nJsOwnwSpq6Pc5K4vEkwmwyrVEhZh2x+5HJn+pax2QL4pM+WocRiDG1EiGq/X2bDnmV7Myr/vBun4PFnGsgJU+cfuJLlkHV4Ku6iq9F/yEKTHBk4MgSEUMTtds01no/EIcecdT1EFGpM1WieBR4kxNhh6HQYU+zm4bzpA3mMN1HDsEpU15JMq6BpKEOx/2viuRJc9LMVTClpkEPRgjWurYvqRiePLYmEs2qA+sUAtyOgeZNTLhLNL8H8MzXWFdICuwsR+9Hs/gFkhL5sONc/rEK34+dbCpBqROVqHa/W7Bpxa8VgzIkUTuL880SmjdtVxwxevjTrFX74o0WHG/5ECuIJVME+whCZIHGy4hSTnAPVqtUWu7LAej+3Ser1NukO/N4qeV3Vv6/QMKaU9qxoJd4EZ8ePZd4OKr6Jvd2dNuinn8YAOTXf60ihbMjOb3gjXgFpMueRp4=; BUC=AVU0lH7nviqJcxrQ7Ub_LqeuIyaljg-b1UB99wgdwHU=',
    'origin': 'https://pcmap.place.naver.com',
    'referer': 'https://pcmap.place.naver.com/restaurant/list',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

# 페이로드 데이터
payload = [
    {
        "operationName": "getBeautyList",
        "variables": {
            "useReverseGeocode": True,
            "input": {
                "query": "중계역네일",
                "display": 1,
                "start": 70,
                "filterBooking": False,
                "filterCoupon": False,
                "naverBenefit": False,
                "sortingOrder": "precision",
                "x": "",
                "y": "",
                "bounds": "",
                "deviceType": "pcmap"
            },
            "businessType": "",
            "isNmap": True,
            "isBounds": True,
            "reverseGeocodingInput": {
                "x": "",
                "y": ""
            }
        },
        "query": "query getBeautyList($input: BeautyListInput, $businessType: String, $isNmap: Boolean!, $isBounds: Boolean!, $reverseGeocodingInput: ReverseGeocodingInput, $useReverseGeocode: Boolean = false) {\n  businesses: nailshops(input: $input) {\n    total\n    userGender\n    items {\n      ...BeautyBusinessItems\n      imageMarker @include(if: $isNmap) {\n        marker\n        markerSelected\n        __typename\n      }\n      markerId @include(if: $isNmap)\n      markerLabel @include(if: $isNmap) {\n        text\n        style\n        __typename\n      }\n      __typename\n    }\n    nlu {\n      ...NluFields\n      __typename\n    }\n    optionsForMap @include(if: $isBounds) {\n      ...OptionsForMap\n      __typename\n    }\n    __typename\n  }\n  brands: beautyBrands(input: $input, businessType: $businessType) {\n    name\n    cid\n    __typename\n  }\n  reverseGeocodingAddr(input: $reverseGeocodingInput) @include(if: $useReverseGeocode) {\n    ...ReverseGeocodingAddr\n    __typename\n  }\n}\n\nfragment NluFields on Nlu {\n  queryType\n  user {\n    gender\n    __typename\n  }\n  queryResult {\n    ptn0\n    ptn1\n    region\n    spot\n    tradeName\n    service\n    selectedRegion {\n      name\n      index\n      x\n      y\n      __typename\n    }\n    selectedRegionIndex\n    otherRegions {\n      name\n      index\n      __typename\n    }\n    property\n    keyword\n    queryType\n    nluQuery\n    businessType\n    cid\n    branch\n    forYou\n    franchise\n    titleKeyword\n    location {\n      x\n      y\n      default\n      longitude\n      latitude\n      dong\n      si\n      __typename\n    }\n    noRegionQuery\n    priority\n    showLocationBarFlag\n    themeId\n    filterBooking\n    repRegion\n    repSpot\n    dbQuery {\n      isDefault\n      name\n      type\n      getType\n      useFilter\n      hasComponents\n      __typename\n    }\n    type\n    category\n    menu\n    context\n    __typename\n  }\n  __typename\n}\n\nfragment ReverseGeocodingAddr on ReverseGeocodingResult {\n  rcode\n  region\n  __typename\n}\n\nfragment OptionsForMap on OptionsForMap {\n  maxZoom\n  minZoom\n  includeMyLocation\n  maxIncludePoiCount\n  center\n  spotId\n  keepMapBounds\n  __typename\n}\n\nfragment CouponItems on Coupon {\n  total\n  promotions {\n    promotionSeq\n    couponSeq\n    conditionType\n    image {\n      url\n      __typename\n    }\n    title\n    description\n    type\n    couponUseType\n    __typename\n  }\n  __typename\n}\n\nfragment BeautyBusinessItemBase on BeautySummary {\n  id\n  apolloCacheId\n  name\n  hasBooking\n  hasNPay\n  blogCafeReviewCount\n  bookingReviewCount\n  bookingReviewScore\n  description\n  roadAddress\n  address\n  imageUrl\n  talktalkUrl\n  distance\n  x\n  y\n  representativePrice {\n    isFiltered\n    priceName\n    price\n    __typename\n  }\n  promotionTitle\n  stylesCount\n  visitorReviewCount\n  visitorReviewScore\n  styleBookingCounts {\n    styleNum\n    name\n    count\n    isPopular\n    __typename\n  }\n  newOpening\n  coupon {\n    ...CouponItems\n    __typename\n  }\n  __typename\n}\n\nfragment BeautyBusinessItems on BeautySummary {\n  ...BeautyBusinessItemBase\n  styles {\n    desc\n    shortDesc\n    styleNum\n    isPopular\n    images {\n      imageUrl\n      __typename\n    }\n    styleOptions {\n      num\n      __typename\n    }\n    __typename\n  }\n  streetPanorama {\n    id\n    pan\n    tilt\n    lat\n    lon\n    __typename\n  }\n  __typename\n}"
    }
]

# POST 요청 보내기
response = requests.post(url, headers=headers, json=payload)

# UTF-8 인코딩 처리
response.encoding = 'utf-8'

# 응답 처리
if response.status_code == 200:
    data = response.json()

    # 첫 번째 배열을 추출하여 출력
    first_result = data[0] if data else None
    rs = first_result['data']['businesses']['items']

    for r in rs:
        print(r['name'])

    # print(json.dumps(rs, ensure_ascii=False, indent=2))  # 첫 번째 요소를 예쁘게 출력
    print(len(rs))
else:
    print(f"요청 실패: {response.status_code}")
