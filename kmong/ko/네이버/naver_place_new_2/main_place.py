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
        "operationName": "getPlacesList",
        "variables": {
            "useReverseGeocode": True,
            "input": {
                "query": "중계역네일",
                "start": 1,
                "display": 100,
                "adult": False,
                "spq": False,
                "queryRank": "",
                "x": "",
                "y": "",
                "deviceType": "pcmap",
                "bounds": ""
            },
            "isNmap": True,
            "isBounds": True,
            "reverseGeocodingInput": {
                "x": "",
                "y": ""
            }
        },
        "query": "query getPlacesList($input: PlacesInput, $isNmap: Boolean!, $isBounds: Boolean!, $reverseGeocodingInput: ReverseGeocodingInput, $useReverseGeocode: Boolean = false) {\n  businesses: places(input: $input) {\n    total\n    items {\n      id\n      name\n      normalizedName\n      category\n      detailCid {\n        c0\n        c1\n        c2\n        c3\n        __typename\n      }\n      categoryCodeList\n      dbType\n      distance\n      roadAddress\n      address\n      fullAddress\n      commonAddress\n      bookingUrl\n      phone\n      virtualPhone\n      businessHours\n      daysOff\n      imageUrl\n      imageCount\n      x\n      y\n      poiInfo {\n        polyline {\n          shapeKey {\n            id\n            name\n            version\n            __typename\n          }\n          boundary {\n            minX\n            minY\n            maxX\n            maxY\n            __typename\n          }\n          details {\n            totalDistance\n            arrivalAddress\n            departureAddress\n            __typename\n          }\n          __typename\n        }\n        polygon {\n          shapeKey {\n            id\n            name\n            version\n            __typename\n          }\n          boundary {\n            minX\n            minY\n            maxX\n            maxY\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      subwayId\n      markerId @include(if: $isNmap)\n      markerLabel @include(if: $isNmap) {\n        text\n        style\n        stylePreset\n        __typename\n      }\n      imageMarker @include(if: $isNmap) {\n        marker\n        markerSelected\n        __typename\n      }\n      oilPrice @include(if: $isNmap) {\n        gasoline\n        diesel\n        lpg\n        __typename\n      }\n      isPublicGas\n      isDelivery\n      isTableOrder\n      isPreOrder\n      isTakeOut\n      isCvsDelivery\n      hasBooking\n      naverBookingCategory\n      bookingDisplayName\n      bookingBusinessId\n      bookingVisitId\n      bookingPickupId\n      baemin {\n        businessHours {\n          deliveryTime {\n            start\n            end\n            __typename\n          }\n          closeDate {\n            start\n            end\n            __typename\n          }\n          temporaryCloseDate {\n            start\n            end\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      yogiyo {\n        businessHours {\n          actualDeliveryTime {\n            start\n            end\n            __typename\n          }\n          bizHours {\n            start\n            end\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      isPollingStation\n      hasNPay\n      talktalkUrl\n      visitorReviewCount\n      visitorReviewScore\n      blogCafeReviewCount\n      bookingReviewCount\n      streetPanorama {\n        id\n        pan\n        tilt\n        lat\n        lon\n        __typename\n      }\n      naverBookingHubId\n      bookingHubUrl\n      bookingHubButtonName\n      newOpening\n      newBusinessHours {\n        status\n        description\n        dayOff\n        dayOffDescription\n        __typename\n      }\n      coupon {\n        total\n        promotions {\n          promotionSeq\n          couponSeq\n          conditionType\n          image {\n            url\n            __typename\n          }\n          title\n          description\n          type\n          couponUseType\n          __typename\n        }\n        __typename\n      }\n      mid\n      hasMobilePhoneNumber\n      hiking {\n        distance\n        startName\n        endName\n        __typename\n      }\n      __typename\n    }\n    optionsForMap @include(if: $isBounds) {\n      ...OptionsForMap\n      displayCorrectAnswer\n      correctAnswerPlaceId\n      __typename\n    }\n    searchGuide {\n      queryResults {\n        regions {\n          displayTitle\n          query\n          region {\n            rcode\n            __typename\n          }\n          __typename\n        }\n        isBusinessName\n        __typename\n      }\n      queryIndex\n      types\n      __typename\n    }\n    queryString\n    siteSort\n    __typename\n  }\n  reverseGeocodingAddr(input: $reverseGeocodingInput) @include(if: $useReverseGeocode) {\n    ...ReverseGeocodingAddr\n    __typename\n  }\n}\n\nfragment OptionsForMap on OptionsForMap {\n  maxZoom\n  minZoom\n  includeMyLocation\n  maxIncludePoiCount\n  center\n  spotId\n  keepMapBounds\n  __typename\n}\n\nfragment ReverseGeocodingAddr on ReverseGeocodingResult {\n  rcode\n  region\n  __typename\n}"
    },

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
