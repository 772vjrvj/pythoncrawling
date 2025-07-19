import requests

url = "https://pcmap-api.place.naver.com/graphql"

headers = {
    "method": "POST",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko",
    "content-type": "application/json",
    "referer": "https://pcmap.place.naver.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}

# 👉 이후 여기에 실제 payload 붙여넣기
payload = [
    {
        "operationName": "getPlacesList",
        "variables": {
            "useReverseGeocode": True,
            "input": {
                "query": "강남 네일",
                "start": 1,
                "display": 100,
                "adult": True,
                "spq": True,
                "queryRank": "",
                "x": "",
                "y": "",
                "clientX": "",
                "clientY": "",
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
        "query": "query getPlacesList($input: PlacesInput, $isNmap: Boolean!, $isBounds: Boolean!, $reverseGeocodingInput: ReverseGeocodingInput, $useReverseGeocode: Boolean = false) {  businesses: places(input: $input) {    total    items {      id      name      normalizedName      category      cid      detailCid {        c0        c1        c2        c3        __typename      }      categoryCodeList      dbType      distance      roadAddress      address      fullAddress      commonAddress      bookingUrl      phone      virtualPhone      businessHours      daysOff      imageUrl      imageCount      x      y      poiInfo {        polyline {          shapeKey {            id            name            version            __typename          }          boundary {            minX            minY            maxX            maxY            __typename          }          details {            totalDistance            arrivalAddress            departureAddress            __typename          }          __typename        }        polygon {          shapeKey {            id            name            version            __typename          }          boundary {            minX            minY            maxX            maxY            __typename          }          __typename        }        __typename      }      subwayId      markerId @include(if: $isNmap)      markerLabel @include(if: $isNmap) {        text        style        stylePreset        __typename      }      imageMarker @include(if: $isNmap) {        marker        markerSelected        __typename      }      oilPrice @include(if: $isNmap) {        gasoline        diesel        lpg        __typename      }      isPublicGas      isDelivery      isTableOrder      isPreOrder      isTakeOut      isCvsDelivery      hasBooking      naverBookingCategory      bookingDisplayName      bookingBusinessId      bookingVisitId      bookingPickupId      baemin {        businessHours {          deliveryTime {            start            end            __typename          }          closeDate {            start            end            __typename          }          temporaryCloseDate {            start            end            __typename          }          __typename        }        __typename      }      yogiyo {        businessHours {          actualDeliveryTime {            start            end            __typename          }          bizHours {            start            end            __typename          }          __typename        }        __typename      }      isPollingStation      hasNPay      talktalkUrl      visitorReviewCount      visitorReviewScore      blogCafeReviewCount      bookingReviewCount      streetPanorama {        id        pan        tilt        lat        lon        __typename      }      naverBookingHubId      bookingHubUrl      bookingHubButtonName      newOpening      newBusinessHours {        status        description        dayOff        dayOffDescription        __typename      }      coupon {        total        promotions {          promotionSeq          couponSeq          conditionType          image {            url            __typename          }          title          description          type          couponUseType          __typename        }        __typename      }      mid      hasMobilePhoneNumber      hiking {        distance        startName        endName        __typename      }      __typename    }    optionsForMap @include(if: $isBounds) {      ...OptionsForMap      displayCorrectAnswer      correctAnswerPlaceId      __typename    }    searchGuide {      queryResults {        regions {          displayTitle          query          region {            rcode            __typename          }          __typename        }        isBusinessName        __typename      }      queryIndex      types      __typename    }    queryString    siteSort    __typename  }  reverseGeocodingAddr(input: $reverseGeocodingInput) @include(if: $useReverseGeocode) {    ...ReverseGeocodingAddr    __typename  }}fragment OptionsForMap on OptionsForMap {  maxZoom  minZoom  includeMyLocation  maxIncludePoiCount  center  spotId  keepMapBounds  __typename}fragment ReverseGeocodingAddr on ReverseGeocodingResult {  rcode  region  __typename}"
    }
]

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    print("✅ 요청 성공")
    print(response.text)
else:
    print(f"❌ 요청 실패: {response.status_code}")
    print(response.text)
