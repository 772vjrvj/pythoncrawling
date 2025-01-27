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
        "operationName": "getRestaurants",
        "variables": {
            "useReverseGeocode": True,
            "isNmap": True,
            "restaurantListInput": {
                "query": "강남 치킨",
                "x": "",
                "y": "",
                "start": 1,
                "display": 100,
                "takeout": None,
                "orderBenefit": None,
                "isCurrentLocationSearch": None,
                "filterOpening": None,
                "deviceType": "pcmap",
                "bounds": "",
                "isPcmap": True
            },
            "restaurantListFilterInput": {
                "x": "",
                "y": "",
                "display": 100,
                "start": 1,
                "query": "강남 치킨",
                "bounds": "",
                "isCurrentLocationSearch": None
            },
            "reverseGeocodingInput": {
                "x": "",
                "y": ""
            }
        },
        "query": "query getRestaurants($restaurantListInput: RestaurantListInput, $restaurantListFilterInput: RestaurantListFilterInput, $reverseGeocodingInput: ReverseGeocodingInput, $useReverseGeocode: Boolean = false, $isNmap: Boolean = false) {\n  restaurants: restaurantList(input: $restaurantListInput) {\n    items {\n      apolloCacheId\n      coupon {\n        ...CouponItems\n        __typename\n      }\n      ...CommonBusinessItems\n      ...RestaurantBusinessItems\n      __typename\n    }\n    ...RestaurantCommonFields\n    optionsForMap {\n      ...OptionsForMap\n      __typename\n    }\n    nlu {\n      ...NluFields\n      __typename\n    }\n    searchGuide {\n      ...SearchGuide\n      __typename\n    }\n    __typename\n  }\n  filters: restaurantListFilter(input: $restaurantListFilterInput) {\n    ...RestaurantFilter\n    __typename\n  }\n  reverseGeocodingAddr(input: $reverseGeocodingInput) @include(if: $useReverseGeocode) {\n    ...ReverseGeocodingAddr\n    __typename\n  }\n}\n\nfragment OptionsForMap on OptionsForMap {\n  maxZoom\n  minZoom\n  includeMyLocation\n  maxIncludePoiCount\n  center\n  spotId\n  keepMapBounds\n  __typename\n}\n\nfragment NluFields on Nlu {\n  queryType\n  user {\n    gender\n    __typename\n  }\n  queryResult {\n    ptn0\n    ptn1\n    region\n    spot\n    tradeName\n    service\n    selectedRegion {\n      name\n      index\n      x\n      y\n      __typename\n    }\n    selectedRegionIndex\n    otherRegions {\n      name\n      index\n      __typename\n    }\n    property\n    keyword\n    queryType\n    nluQuery\n    businessType\n    cid\n    branch\n    forYou\n    franchise\n    titleKeyword\n    location {\n      x\n      y\n      default\n      longitude\n      latitude\n      dong\n      si\n      __typename\n    }\n    noRegionQuery\n    priority\n    showLocationBarFlag\n    themeId\n    filterBooking\n    repRegion\n    repSpot\n    dbQuery {\n      isDefault\n      name\n      type\n      getType\n      useFilter\n      hasComponents\n      __typename\n    }\n    type\n    category\n    menu\n    context\n    __typename\n  }\n  __typename\n}\n\nfragment SearchGuide on SearchGuide {\n  queryResults {\n    regions {\n      displayTitle\n      query\n      region {\n        rcode\n        __typename\n      }\n      __typename\n    }\n    isBusinessName\n    __typename\n  }\n  queryIndex\n  types\n  __typename\n}\n\nfragment ReverseGeocodingAddr on ReverseGeocodingResult {\n  rcode\n  region\n  __typename\n}\n\nfragment CouponItems on Coupon {\n  total\n  promotions {\n    promotionSeq\n    couponSeq\n    conditionType\n    image {\n      url\n      __typename\n    }\n    title\n    description\n    type\n    couponUseType\n    __typename\n  }\n  __typename\n}\n\nfragment CommonBusinessItems on BusinessSummary {\n  id\n  dbType\n  name\n  businessCategory\n  category\n  description\n  hasBooking\n  hasNPay\n  x\n  y\n  distance\n  imageUrl\n  imageCount\n  phone\n  virtualPhone\n  routeUrl\n  streetPanorama {\n    id\n    pan\n    tilt\n    lat\n    lon\n    __typename\n  }\n  roadAddress\n  address\n  commonAddress\n  blogCafeReviewCount\n  bookingReviewCount\n  totalReviewCount\n  bookingUrl\n  bookingBusinessId\n  talktalkUrl\n  detailCid {\n    c0\n    c1\n    c2\n    c3\n    __typename\n  }\n  options\n  promotionTitle\n  agencyId\n  businessHours\n  newOpening\n  markerId @include(if: $isNmap)\n  markerLabel @include(if: $isNmap) {\n    text\n    style\n    __typename\n  }\n  imageMarker @include(if: $isNmap) {\n    marker\n    markerSelected\n    __typename\n  }\n  __typename\n}\n\nfragment RestaurantFilter on RestaurantListFilterResult {\n  filters {\n    index\n    name\n    displayName\n    value\n    multiSelectable\n    defaultParams {\n      age\n      gender\n      day\n      time\n      __typename\n    }\n    items {\n      index\n      name\n      value\n      selected\n      representative\n      displayName\n      clickCode\n      laimCode\n      type\n      icon\n      __typename\n    }\n    __typename\n  }\n  votingKeywordList {\n    items {\n      name\n      displayName\n      value\n      icon\n      clickCode\n      __typename\n    }\n    menuItems {\n      name\n      value\n      icon\n      clickCode\n      __typename\n    }\n    total\n    __typename\n  }\n  optionKeywordList {\n    items {\n      name\n      displayName\n      value\n      icon\n      clickCode\n      __typename\n    }\n    total\n    __typename\n  }\n  __typename\n}\n\nfragment RestaurantCommonFields on RestaurantListResult {\n  restaurantCategory\n  queryString\n  siteSort\n  selectedFilter {\n    order\n    rank\n    tvProgram\n    region\n    brand\n    menu\n    food\n    mood\n    purpose\n    sortingOrder\n    takeout\n    orderBenefit\n    cafeFood\n    day\n    time\n    age\n    gender\n    myPreference\n    hasMyPreference\n    cafeMenu\n    cafeTheme\n    theme\n    voting\n    filterOpening\n    keywordFilter\n    property\n    realTimeBooking\n    hours\n    __typename\n  }\n  rcodes\n  location {\n    sasX\n    sasY\n    __typename\n  }\n  total\n  __typename\n}\n\nfragment RestaurantBusinessItems on RestaurantListSummary {\n  categoryCodeList\n  visitorReviewCount\n  visitorReviewScore\n  imageUrls\n  bookingHubUrl\n  bookingHubButtonName\n  visitorImages {\n    id\n    reviewId\n    imageUrl\n    profileImageUrl\n    nickname\n    __typename\n  }\n  visitorReviews {\n    id\n    review\n    reviewId\n    __typename\n  }\n  foryouLabel\n  foryouTasteType\n  microReview\n  priceCategory\n  broadcastInfo {\n    program\n    date\n    menu\n    __typename\n  }\n  michelinGuide {\n    year\n    star\n    comment\n    url\n    hasGrade\n    isBib\n    alternateText\n    hasExtraNew\n    region\n    __typename\n  }\n  broadcasts {\n    program\n    menu\n    episode\n    broadcast_date\n    __typename\n  }\n  tvcastId\n  naverBookingCategory\n  saveCount\n  uniqueBroadcasts\n  isDelivery\n  deliveryArea\n  isCvsDelivery\n  isTableOrder\n  isPreOrder\n  isTakeOut\n  bookingDisplayName\n  bookingVisitId\n  bookingPickupId\n  popularMenuImages {\n    name\n    price\n    bookingCount\n    menuUrl\n    menuListUrl\n    imageUrl\n    isPopular\n    usePanoramaImage\n    __typename\n  }\n  newBusinessHours {\n    status\n    description\n    __typename\n  }\n  baemin {\n    businessHours {\n      deliveryTime {\n        start\n        end\n        __typename\n      }\n      closeDate {\n        start\n        end\n        __typename\n      }\n      temporaryCloseDate {\n        start\n        end\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  yogiyo {\n    businessHours {\n      actualDeliveryTime {\n        start\n        end\n        __typename\n      }\n      bizHours {\n        start\n        end\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  realTimeBookingInfo {\n    description\n    hasMultipleBookingItems\n    bookingBusinessId\n    bookingUrl\n    itemId\n    itemName\n    timeSlots {\n      date\n      time\n      timeRaw\n      available\n      __typename\n    }\n    __typename\n  }\n  __typename\n}"
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
    rs = first_result['data']['restaurants']['items']

    for r in rs:
        print(r['name'])

    # print(json.dumps(rs, ensure_ascii=False, indent=2))  # 첫 번째 요소를 예쁘게 출력
    print(len(rs))
else:
    print(f"요청 실패: {response.status_code}")
