from src.vo.site import Site

SITE_LIST = [
    # Site("공모전 마감 사이트 통합", "CONTEST_DEADLINE", "#D73227", enabled=True,  setting=[
    #     {'name': '중복제거',    'code': 'dup','value': True, 'type': 'check'},
    #     {'name': 'THINKGOOD', 'code': 'thinkgood','value': 'Y_lDUDfEFsFTgLsbFt-VyefFa_wNrqLAoJIolxPo8ycVd6GOlgXVj7ap50cJxtWOLgFMFsM1kbLnzIZm-i9SszImy2-ricuLrjl9bQDJNig'},
    #     {'name': 'LINKAREER', 'code': 'linkareer', 'value': 'f59df641666ef9f55c69ed6a14866bfd2f87fb32c89a80038a466b201ee11422'},
    #     ],
    #     columns = [
    #          {"code": "site",           "value": "사이트",     "checked": True},
    #          {"code": "contest_name",   "value": "공모전명",   "checked": True},
    #          {"code": "host",           "value": "주최사",     "checked": True},
    #          {"code": "url",            "value": "URL",       "checked": True},
    #          {"code": "deadline",       "value": "마감일",     "checked": True},
    #          {"code": "page",           "value": "페이지",     "checked": True},
    #     ],
    #      sites = [
    #          {"code": "wevity",          "value": "WEVITY",      "checked": True},
    #          {"code": "linkareer",       "value": "LINKareer",   "checked": True},
    #          {"code": "all_con",         "value": "올콘",         "checked": True},
    #          {"code": "thinkcontest",    "value": "Thinkgood",   "checked": True},
    #      ],
    # ),
    # Site("네이버 플레이스 전국", "NAVER_PLACE_LOC_ALL", "#03C75A", enabled=True,
    #      setting=[
    #          {'name': '1. 키워드(콤마(,)로 구분해주세요)', 'code': 'keyword',    'value': '', 'type': 'input'}
    #      ],
    #      columns = [
    #         {"code": "id",             "value": "아이디",        "checked": True},
    #         {"code": "name",           "value": "이름",          "checked": True},
    #         {"code": "addr_jibun",     "value": "주소(지번)",    "checked": True},
    #         {"code": "addr_road",      "value": "주소(도로명)",  "checked": True},
    #         {"code": "category_main",  "value": "대분류",        "checked": True},
    #         {"code": "category_sub",   "value": "소분류",        "checked": True},
    #         {"code": "rating",         "value": "별점",          "checked": True},
    #         {"code": "review_visitors","value": "방문자리뷰수",  "checked": True},
    #         {"code": "review_blogs",   "value": "블로그리뷰수",  "checked": True},
    #         {"code": "open_time1",     "value": "이용시간1",     "checked": True},
    #         {"code": "open_time2",     "value": "이용시간2",     "checked": True},
    #         {"code": "category",       "value": "카테고리",      "checked": True},
    #         {"code": "url",            "value": "URL",           "checked": True},
    #         {"code": "map",            "value": "지도",          "checked": True},
    #         {"code": "amenities",      "value": "편의시설",      "checked": True},
    #         {"code": "virtual_phone",  "value": "가상번호",      "checked": True},
    #         {"code": "phone",          "value": "전화번호",      "checked": True},
    #         {"code": "site",           "value": "사이트",        "checked": True},
    #         {"code": "region_info",    "value": "주소지정보",    "checked": True},
    #         {"code": "city",           "value": "시도(검색)",    "checked": True},
    #         {"code": "division",       "value": "시군구(검색)",  "checked": True},
    #         {"code": "sector",         "value": "읍면동(검색)",  "checked": True},
    #         {"code": "keyword",        "value": "키워드(검색)",  "checked": True},
    #         {"code": "all_keyword",    "value": "전체 검색어",  "checked": True},
    #
    #         {"code": "zip_code",       "value": "우편번호",          "checked": True},
    #
    #         # 행사 정보
    #         {"code": "agency_name",    "value": "대행사 상호",          "checked": False},
    #         {"code": "agency_ceo",     "value": "대행사 대표자명",      "checked": False},
    #         {"code": "agency_address", "value": "대행사 소재지",        "checked": False},
    #         {"code": "agency_bizno",   "value": "대행사 사업자번호",    "checked": False},
    #         {"code": "agency_mailno",  "value": "대행사 통신판매업번호","checked": False},
    #         {"code": "agency_phone",   "value": "대행사 연락처",        "checked": False},
    #         {"code": "agency_site",    "value": "대행사 홈페이지",      "checked": False},
    #         ],
    #      region = True
    #      ),
    # Site("네이버 플레이스 URL", "NAVER_PLACE_URL_ALL", "#03C75A", enabled=True,
    #      setting=[
    #          {'name': '용량(MB) 1 ~ 1000사이 숫자를 입력하세요', 'code': 'image_size',    'value': '1000', 'type': 'input'},
    #          {'name': '이미지 압축 여부', 'code': 'zip',    'value': True, 'type': 'check'}
    #      ],
    #      columns = [
    #          {"code": "url",            "value": "URL",           "checked": True},
    #          {"code": "image",          "value": "이미지",          "checked": True},
    #          {"code": "id",             "value": "아이디",        "checked": True},
    #          {"code": "name",           "value": "이름",          "checked": True},
    #          {"code": "addr_jibun",     "value": "주소(지번)",    "checked": True},
    #          {"code": "addr_road",      "value": "주소(도로명)",  "checked": True},
    #          {"code": "category_main",  "value": "대분류",        "checked": True},
    #          {"code": "category_sub",   "value": "소분류",        "checked": True},
    #          {"code": "rating",         "value": "별점",          "checked": True},
    #          {"code": "review_visitors","value": "방문자리뷰수",  "checked": True},
    #          {"code": "review_blogs",   "value": "블로그리뷰수",  "checked": True},
    #          {"code": "open_time1",     "value": "이용시간1",     "checked": True},
    #          {"code": "open_time2",     "value": "이용시간2",     "checked": True},
    #          {"code": "category",       "value": "카테고리",      "checked": True},
    #          {"code": "map",            "value": "지도",          "checked": True},
    #          {"code": "amenities",      "value": "편의시설",      "checked": True},
    #          {"code": "virtual_phone",  "value": "가상번호",      "checked": True},
    #          {"code": "phone",          "value": "전화번호",      "checked": True},
    #          {"code": "site",           "value": "사이트",        "checked": True},
    #          {"code": "region_info",    "value": "주소지정보",     "checked": True},
    #      ],
    #      region = False,
    #      popup=True
    #      ),

    # Site("네이버 부동산업체 전국 번호", "NAVER_LAND_REAL_ESTATE_LOC_ALL", "#03C75A", enabled=True,
    #      setting=[
    #          {'name': '1. 키워드(콤마(,)로 구분해주세요)', 'code': 'keyword',    'value': '', 'type': 'input'}
    #      ],
    #      columns = [
    #          # 메타
    #          {"code": "article_number",        "value": "번호",   "checked": False},
    #          {"code": "region",                "value": "지역",   "checked": False},
    #          {"code": "city",                  "value": "시도",   "checked": True},
    #          {"code": "division",              "value": "시군구",  "checked": True},
    #          {"code": "sector",                "value": "읍면동",  "checked": True},
    #
    #          # {"code": "item_name",             "value": "매물명",  "checked": True},
    #
    #          # 주소/위치
    #          {"code": "latitude",              "value": "위도",         "checked": False},   # yCoordinate
    #          {"code": "longitude",             "value": "경도",         "checked": False},   # xCoordinate
    #          {"code": "keyword",               "value": "키워드",  "checked": True},
    #          {"code": "complex_name",          "value": "단지명",  "checked": True},
    #          {"code": "complex_dong_name",     "value": "동(단지)",     "checked": True},
    #
    #          # 중개사
    #          {"code": "brokerage_name",        "value": "중개사무소 이름",      "checked": True},
    #          {"code": "broker_name",           "value": "중개사 이름",        "checked": True},
    #          {"code": "broker_address",        "value": "중개사무소 주소",         "checked": True},
    #          {"code": "phone_brokerage",       "value": "중개사무소 번호",   "checked": True},
    #          {"code": "phone_mobile",          "value": "중개사 헨드폰번호",   "checked": True},
    #
    #          # 층/방향
    #          {"code": "floor_info",            "value": "층",           "checked": False},   # 예: "2/6" 또는 "고/8"
    #          {"code": "target_floor",          "value": "층(목표)",     "checked": False},
    #          {"code": "total_floor",           "value": "층(전체)",     "checked": False},
    #          {"code": "direction_ko",          "value": "방향",         "checked": False},   # self._direction_to_ko 적용값
    #          # {"code": "direction_raw",         "value": "방향(원문)",   "checked": True},
    #          {"code": "direction_standard",    "value": "방향기준",     "checked": False},
    #
    #          # 면적
    #          {"code": "exclusive_sqm_pyeong",  "value": "전용(㎡/평)",  "checked": False},
    #          {"code": "supply_sqm_pyeong",     "value": "공급(㎡/평)",  "checked": False},
    #          {"code": "contract_sqm_pyeong",   "value": "계약(㎡/평)",  "checked": False},
    #
    #          # 가격/비용
    #          {"code": "deal_price_fmt",        "value": "매매가",       "checked": False},   # 예: "8억"
    #          {"code": "deal_price",            "value": "매매가(원)",   "checked": False},
    #          {"code": "maintenance_fee",       "value": "관리비",       "checked": False},
    #
    #          # 유형/일자
    #          # {"code": "real_estate_type",      "value": "부동산종류",   "checked": True},
    #          # {"code": "trade_type",            "value": "거래유형",     "checked": True},
    #          {"code": "exposure_date",         "value": "노출일",       "checked": False},
    #          {"code": "confirm_date",          "value": "확인일",       "checked": False},
    #          {"code": "approval_elapsed_year", "value": "준공연차",     "checked": False},
    #          {"code": "completion_date",       "value": "준공일",       "checked": False},
    #      ],
    #      region = True
    #      ),
    # Site("네이버 공인중개사 번호", "NAVER_LAND_REAL_ESTATE_DETAIL", "#03C75A", enabled=True,
    #      setting=[],
    #      columns = [
    #          # 게시정보
    #          {"code": "article_number",         "value": "게시번호",        "checked": True},
    #
    #          # 기본 정보
    #          {"code": "complexName",           "value": "단지명",          "checked": True},
    #          {"code": "dongName",              "value": "동이름",          "checked": True},
    #          {"code": "price",                 "value": "매매가",          "checked": True},
    #          {"code": "warrantyAmount",        "value": "보증금",          "checked": True},
    #          {"code": "rentAmount",            "value": "월세",            "checked": True},
    #          {"code": "supplySpace",           "value": "공급면적",         "checked": True},
    #          {"code": "pyeongArea",            "value": "평수",            "checked": True},
    #          {"code": "landSpace",             "value": "대지면적",         "checked": True},
    #          {"code": "floorSpace",            "value": "연면적",           "checked": True},
    #          {"code": "buildingSpace",         "value": "건축면적",           "checked": True},
    #          {"code": "exclusiveSpace",        "value": "전용면적",           "checked": True},
    #
    #          {"code": "articleFeatureDescription",        "value": "매물특징",           "checked": True},
    #          {"code": "exposureStartDate",        "value": "매물확인일",           "checked": True},
    #          {"code": "buildingPrincipalUse",        "value": "건축물용도",           "checked": True},
    #
    #          # 종합 정보 (주소)
    #          {"code": "city",                  "value": "시도",             "checked": True},
    #          {"code": "division",              "value": "시군구",           "checked": True},
    #          {"code": "sector",                "value": "읍면동",           "checked": True},
    #          {"code": "jibun",                 "value": "번지",             "checked": True},
    #          {"code": "roadName",              "value": "도로명주소",        "checked": True},
    #          {"code": "zipCode",               "value": "우편번호",          "checked": True},
    #          {"code": "full_addr",              "value": "전체주소",          "checked": True},
    #
    #          # 중개사
    #          {"code": "brokerage_name",        "value": "중개사무소이름",   "checked": True},
    #          {"code": "broker_name",           "value": "중개사이름",      "checked": True},
    #          {"code": "broker_address",        "value": "중개사무소주소",   "checked": True},
    #          {"code": "phone_brokerage",       "value": "중개사무소번호",   "checked": True},
    #          {"code": "phone_mobile",          "value": "중개사핸드폰번호", "checked": True},
    #
    #          {"code": "url",                    "value": "URL",            "checked": True},
    #
    #          # 부모정보
    #          {"code": "atclNm",                 "value": "상위매물명",      "checked": True},
    #          {"code": "bildNm",                 "value": "상위매물동",      "checked": True},
    #          {"code": "atclNo",                 "value": "상위매물게시번호", "checked": True},
    #          {"code": "parts",                  "value": "검색주소",       "checked": True},
    #
    #          {"code": "rletType",               "value": "매물유형",       "checked": True},
    #          {"code": "tradeType",              "value": "거래유형",       "checked": True},
    #      ],
    #      region = True
    #      ),
    # Site("NH Bank", "NH_BANK", "#03C75A", enabled=True,  setting=[]),
    # Site("네이버 카페", "NAVER_CAFE_CTT_CNT_ONLY", "#03C75A", enabled=True,  setting=[], popup=True),
    # Site("네이버 블로그 글조회", "NAVER_BLOG_CTT", "#03C75A", enabled=False,  setting=[
    #     {'name': '블로그 URL', 'code': 'url',        'value': '', 'type': 'button'},
    #     {'name': '게시판 선택', 'code': 'url_select', 'value': '', 'type': 'select'},
    #     {'name': '시작 페이지', 'code': 'st_page',    'value': '', 'type': 'input'},
    #     {'name': '종료 페이지', 'code': 'ed_page',    'value': '', 'type': 'input'}
    # ]),
    # Site("알바몬", "ALBAMON", "#FF6600", enabled=True,  setting=[]),
    # Site("쿠팡", "COUPANG", "#D73227", enabled=True,  setting=[
    #     {'name': '제품 딜레이 시간(초)', 'code': 'html_source_delay_time','value': 6},
    #     {'name': '크롬 재시작 딜레이 시간(초)', 'code': 'chrome_delay_time','value': 3600}
    # ]),
    # Site("알바천국", "ALBA", "#FFF230", enabled=True,  setting=[
    #     {'name': '감지 대기 딜레이 시간(초)', 'code': 'alba_delay_time','value': 1200}
    # ]),
    # Site("소통한방병원", "SOTONG", "#29ADA6", enabled=True,  setting=[
    #     {'name': '시작 날짜(YYYY-MM-DD)', 'code': 'fr_date','value': '', 'type': 'input'},
    #     {'name': '종료 날짜(YYYY-MM-DD)', 'code': 'to_date','value': '', 'type': 'input'}
    # ]),
    # Site("SEOUL FOOD 2025", "SEOUL_FOOD_2025", "#000000", enabled=True,  setting=[]),
    # Site("IHERB", "IHERB", "#458500", enabled=True,  setting=[
    #     {'name': '시작 페이지', 'code': 'st_page','value': '', 'type': 'input'},
    #     {'name': '종료 페이지', 'code': 'ed_page','value': '', 'type': 'input'}
    # ]),
    # Site("YUPOO", "YUPOO", "#49BC85", enabled=True,  setting=[
    #          {'name': '1. 아이디(콤마(,)로 구분해주세요)', 'code': 'keyword',    'value': '', 'type': 'input'},
    #          {'name': '2. 쿠키 목록페이지', 'code': 'cookie1',    'value': '', 'type': 'input'},
    #          {'name': '2. 쿠키 상세페이지', 'code': 'cookie2',    'value': '', 'type': 'input'},
    #      ]),
    # Site("OVREPLE", "OVREPLE", "#812625", enabled=True,  setting=[
    #          {'name': '1. 카테고리 아이디',                   'code': 'ca_id',      'value': '', 'type': 'input'},
    #          {'name': '2. 상품 아이디(콤마(,)로 구분해주세요)', 'code': 'keyword',    'value': '', 'type': 'input'}
    #      ]),
    # Site("1004YA", "1004YA", "#FB92BA", enabled=True,  setting=[]),
    # Site("APP SENSORTOWER", "APP_SENSORTOWER", "#1F9E8F", enabled=True,  setting=[], popup=True),
    # Site("ABC MART BRAND", "ABC_MART_BRAND", "#ee1c25", enabled=True, setting=[], popup=True,
    #      columns = [
    #          {"code": "brand_name",        "value": "브랜드명",   "checked": True},
    #          {"code": "style_code",        "value": "스타일코드",  "checked": True},
    #          {"code": "size",              "value": "사이즈",     "checked": True},
    #          {"code": "price",             "value": "가격",      "checked": True},
    #          {"code": "prd_link",          "value": "상품 링크",  "checked": True},
    #      ]
    # ),
    # Site("ABC MART DETAIL", "ABC_MART_DETAIL", "#ee1c25", enabled=True, setting=[], popup=True,
    #      columns = [
    #          {"code": "prdtName",            "value": "상품명",         "checked": True},
    #          {"code": "product_status",      "value": "상품 상태",       "checked": True},
    #          {"code": "brandName",           "value": "브랜드",         "checked": True},
    #          {"code": "url",                 "value": "상품상세url",     "checked": True},
    #          {"code": "sellAmt",             "value": "판매가",         "checked": True},
    #          {"code": "available_options",   "value": "구매 가능한 옵션",  "checked": True},
    #          {"code": "sold_out_options",    "value": "품절된 옵션",      "checked": True},
    #          {"code": "styleInfo",           "value": "스타일코드",       "checked": True},
    #          {"code": "prdtColorInfo",       "value": "색상코드",         "checked": True},
    #          {"code": "retailer",            "value": "판매처",           "checked": True},
    #      ]
    #  ),
    # Site("GRAND STAGE BRAND", "GRAND_STAGE_BRAND", "#03C75A", enabled=True, setting=[], popup=True,
    #      columns = [
    #          {"code": "brand_name",        "value": "브랜드명",   "checked": True},
    #          {"code": "style_code",        "value": "스타일코드",  "checked": True},
    #          {"code": "size",              "value": "사이즈",     "checked": True},
    #          {"code": "price",             "value": "가격",      "checked": True},
    #          {"code": "prd_link",          "value": "상품 링크",  "checked": True},
    #      ]
    #  ),
    # Site("GRAND STAGE DETAIL", "GRAND_STAGE_DETAIL", "#03C75A", enabled=True, setting=[], popup=True,
    #      columns = [
    #          {"code": "prdtName",            "value": "상품명",         "checked": True},
    #          {"code": "product_status",      "value": "상품 상태",       "checked": True},
    #          {"code": "brandName",           "value": "브랜드",         "checked": True},
    #          {"code": "url",                 "value": "상품상세url",     "checked": True},
    #          {"code": "sellAmt",             "value": "판매가",         "checked": True},
    #          {"code": "available_options",   "value": "구매 가능한 옵션",  "checked": True},
    #          {"code": "sold_out_options",    "value": "품절된 옵션",      "checked": True},
    #          {"code": "styleInfo",           "value": "스타일코드",       "checked": True},
    #          {"code": "prdtColorInfo",       "value": "색상코드",         "checked": True},
    #          {"code": "retailer",            "value": "판매처",           "checked": True},
    #      ]
    # ),
    # Site("ON THE SPOT BRAND", "ON_THE_SPOT_BRAND", "#A63191", enabled=True,  setting=[], popup=True,
    #      columns = [
    #          {"code": "brand_name",        "value": "브랜드명",   "checked": True},
    #          {"code": "style_code",        "value": "스타일코드",  "checked": True},
    #          {"code": "size",              "value": "사이즈",     "checked": True},
    #          {"code": "price",             "value": "가격",      "checked": True},
    #          {"code": "prd_link",          "value": "상품 링크",  "checked": True},
    #      ]
    # ),
    # Site("ON THE SPOT DETAIL", "ON_THE_SPOT_DETAIL", "#A63191", enabled=True, setting=[], popup=True,
    #      columns = [
    #          {"code": "prdtName",            "value": "상품명",         "checked": True},
    #          {"code": "product_status",      "value": "상품 상태",       "checked": True},
    #          {"code": "brandName",           "value": "브랜드",         "checked": True},
    #          {"code": "url",                 "value": "상품상세url",     "checked": True},
    #          {"code": "sellAmt",             "value": "판매가",         "checked": True},
    #          {"code": "available_options",   "value": "구매 가능한 옵션",  "checked": True},
    #          {"code": "sold_out_options",    "value": "품절된 옵션",      "checked": True},
    #          {"code": "styleInfo",           "value": "스타일코드",       "checked": True},
    #          {"code": "prdtColorInfo",       "value": "색상코드",         "checked": True},
    #          {"code": "retailer",            "value": "판매처",           "checked": True},
    #      ]
    # ),
    # Site("OK MALL BRAND", "OK_MALL_BRAND", "#000000", enabled=True, setting=[], popup=True,
    #     columns = [
    #         {"code": "prd_link",        "value": "상품링크",   "checked": True},
    #         {"code": "brand",           "value": "브랜드",     "checked": True},
    #         {"code": "prd_name",        "value": "상품명",     "checked": True},
    #         {"code": "price",           "value": "가격",      "checked": True},
    #         {"code": "tag_size",        "value": "택 사이즈",  "checked": True},
    #     ]
    # ),
    # Site("OK MALL DETAIL", "OK_MALL_DETAIL", "#000000", enabled=True, setting=[], popup=True,
    #      columns = [
    #          {"code": "prd_link",        "value": "상품링크",   "checked": True},
    #          {"code": "brand",           "value": "브랜드",     "checked": True},
    #          {"code": "prd_name",        "value": "상품명",     "checked": True},
    #          {"code": "price",           "value": "가격",      "checked": True},
    #          {"code": "tag_size",        "value": "택 사이즈",  "checked": True},
    #      ]
    #  ),
    # Site("THE FIRST HALL WEDDING", "THE_FIRST_HALL_WEDDING", "#918074", enabled=True, setting=[],
    #      columns = [
    #          {"code": "url",        "value": "URL",   "checked": True},
    #          {"code": "no",         "value": "NO",    "checked": True},
    #          {"code": "title",      "value": "제목",   "checked": True},
    #          {"code": "content",    "value": "내용",   "checked": True},
    #          {"code": "create_dt",  "value": "등록일", "checked": True},
    #          {"code": "page",       "value": "PAGE",  "checked": True},
    #      ]
    # ),
    # Site("INVOICE", "INVOICE", "#918074", enabled=True, setting=[],
    #      columns = [
    #          {"code": "bio_renuva",             "value": "BioRenuva",           "checked": True},
    #          {"code": "contipro",               "value": "CONTIPRO",            "checked": True},
    #          {"code": "evident_ingredients",    "value": "Evident ingredients", "checked": True},
    #          {"code": "gfn",                    "value": "GFN",                 "checked": True},
    #          {"code": "hallstar_italy_us",      "value": "HALLSTAR ITALY & US", "checked": True},
    #          {"code": "lignopure",              "value": "Lignopure",           "checked": True},
    #          {"code": "protameen",              "value": "Protameen",           "checked": True},
    #          {"code": "selco",                  "value": "SELCO",               "checked": True},
    #      ]
    # ),
    # Site("카카오 스토어 푸드", "KAKAO_STORE_FOOD", "#FEE500", enabled=True,
    #      setting=[
    #          {'name': '시작 페이지(숫자 1부터)', 'code': 'st_page',    'value': '1', 'type': 'input'},
    #          {'name': '종료 페이지(숫자 12까지)', 'code': 'ed_page',    'value': '12', 'type': 'input'},
    #      ],
    #      columns = [
    #          {"code": "no",                          "value": "순번",            "checked": True},
    #          {"code": "groupDiscountPeriod",         "value": "톡딜 행사기간",    "checked": True},
    #          {"code": "linkPath",                    "value": "상품 구매 URL",   "checked": True},
    #          {"code": "encoreOrigin",                "value": "앵콜/산지",        "checked": True},   # === 신규 ===
    #          {"code": "category",                    "value": "카테고리",        "checked": True},   # === 신규 ===
    #          {"code": "subCategory",                 "value": "세부카테고리",     "checked": True},   # === 신규 ===
    #          {"code": "productName",                 "value": "상품명",          "checked": True},
    #          {"code": "realPrice",                   "value": "메인가격",        "checked": True},   # === 기존 talkdeal_price
    #          {"code": "priceOptions",                "value": "옵션별금액",       "checked": True},   # === 신규 ===
    #          {"code": "couponEvent",                 "value": "쿠폰/이벤트유무",  "checked": True},   # === 신규 ===
    #          {"code": "day1",                        "value": "1일차",           "checked": True},   # === 신규 ===
    #          {"code": "day2",                        "value": "2일차",           "checked": True},   # === 신규 ===
    #          {"code": "day3",                        "value": "3일차",           "checked": True},   # === 신규 ===
    #          {"code": "day4",                        "value": "4일차",           "checked": True},   # === 신규 ===
    #          {"code": "reviewCount",                 "value": "리뷰 개수",        "checked": True},
    #          {"code": "productPositivePercentage",   "value": "만족도(%)",        "checked": True},
    #          {"code": "storeName",                   "value": "업체명",          "checked": True},
    #          {"code": "remark",                      "value": "비고",            "checked": True}    # === 신규 ===
    #      ]
    # ),
    # Site("오늘의 집", "OHOU_SE_CATEGORY", "#00A1FF", enabled=True, popup=True,
    #      setting=[
    #          {'name': '시작 페이지(숫자 1부터)', 'code': 'st_page',    'value': '1', 'type': 'input'},
    #          {'name': '종료 페이지(숫자 9999까지)', 'code': 'ed_page',    'value': '9999', 'type': 'input'},
    #      ],
    #      columns = [
    #          {"code": "category",       "value": "카테고리",           "checked": True},
    #          {"code": "id",             "value": "아이디",            "checked": True},
    #          {"code": "name",           "value": "상품명",            "checked": True},
    #          {"code": "company",        "value": "상호",              "checked": True},
    #          {"code": "address",        "value": "사업장소재지",       "checked": True},
    #          {"code": "cs_phone",       "value": "고객센터 전화번호",   "checked": True},
    #          {"code": "email",          "value": "E-mail",           "checked": True},
    #          {"code": "license",        "value": "사업자 등록번호",     "checked": True},
    #          {"code": "ec_license",     "value": "통신판매업 신고번호",  "checked": True},
    #          {"code": "page",           "value": "페이지",             "checked": True},
    #      ]
    # ),
    # Site("배송정보 11번가", "DELIVERY_11ST_CONTENT", "#FF003E", enabled=True, popup=True,
    #    columns = [
    #     {"code": "id",               "value": "id",            "checked": True},
    #     {"code": "password",         "value": "password",      "checked": True},
    #     {"code": "market",           "value": "마켓",           "checked": True},
    #     {"code": "order_date",       "value": "주문일자",        "checked": True},
    #     {"code": "order_code",       "value": "주문고유코드",    "checked": True},
    #      {"code": "invoice_no",       "value": "송장번호",       "checked": True},
    #      {"code": "delivery_company", "value": "택배사",         "checked": True}
    #   ],
    # ),
    #  Site("배송정보 SSG", "DELIVERY_SSG_CONTENT", "#F12972", enabled=True, popup=True,
    #       columns = [
    #           {"code": "id",               "value": "id",            "checked": True},
    #           {"code": "password",         "value": "password",      "checked": True},
    #           {"code": "market",           "value": "마켓",           "checked": True},
    #           {"code": "order_date",       "value": "주문일자",        "checked": True},
    #           {"code": "order_code",       "value": "주문고유코드",    "checked": True},
    #           {"code": "invoice_no",       "value": "송장번호",       "checked": True},
    #           {"code": "delivery_company", "value": "택배사",         "checked": True}
    #       ]
    # ),
    # Site("피치힐26", "PEACHCHILL26", "#121212", enabled=True,
    #      columns = [
    #          {"code": "product_code", "value": "상품코드", "checked": True},
    #          {"code": "product_name", "value": "상품명", "checked": True},
    #          {"code": "product_price","value": "상품가격", "checked": True},
    #          {"code": "detail_url",   "value": "상품 상세 정보 URL", "checked": True},
    #          {"code": "list_image_urls",  "value": "상품 목록 이미지 URL", "checked": True},
    #          {"code": "list_image_names", "value": "상품 목록 이미지명", "checked": True},
    #          {"code": "thumbnail_image_urls",  "value": "썸네일 이미지 URL", "checked": True},
    #          {"code": "thumbnail_image_names", "value": "썸네일 이미지명", "checked": True},
    #          {"code": "youtube_url", "value": "YOUTUBE URL", "checked": True},
    #          {"code": "detail_image_urls",  "value": "상품 상세정보 이미지 URL", "checked": True},
    #          {"code": "detail_image_names", "value": "상품 상세정보 이미지명", "checked": True},
    #      ],
    #      setting=[
    #          {'name': '시작 페이지', 'code': 'st_page',    'value': '', 'type': 'input'},
    #          {'name': '종료 페이지', 'code': 'ed_page',    'value': '', 'type': 'input'}
    #      ]
    # ),
   # Site("주식 KRX NEXTRADE", "KRX_NEXTRADE", "#121212", enabled=True,
   #      columns = [
   #          {"code": "date",  "value": "날짜",        "checked": True},
   #          {"code": "rank",  "value": "순위",        "checked": True},
   #          {"code": "name",  "value": "종목명",      "checked": True},
   #          {"code": "sum",   "value": "거래대금합계", "checked": True},
   #          {"code": "rate",  "value": "등락률",      "checked": True},
   #      ],
   #      setting=[
   #          {'name': '[조건1] 일 거래대금[억](콤마없이) 이상(▲)', 'code': 'price_sum1',    'value': '0', 'type': 'input'},
   #          {'name': '[조건1] 일 등락률(%)(숫자) 이상(▲)', 'code': 'rate1','value': '0', 'type': 'input'},
   #          {'name': '[조건2] 일 거래대금[억](콤마없이) 이상(▲)', 'code': 'price_sum2',    'value': '0', 'type': 'input'},
   #          {'name': '[조건2] 일 등락률(%)(숫자) 이상(▲)', 'code': 'rate2','value': '0', 'type': 'input'},
   #          {'name': '날짜(YYYYMMDD) 시작', 'code': 'fr_date','value': '20260101', 'type': 'input'},
   #          {'name': '날짜(YYYYMMDD) 종료', 'code': 'to_date','value': '20260101', 'type': 'input'},
   #          {'name': '자동 리포트 여부(날짜 작업할 땐 체크 해재 하세요)',            'code': 'auto_yn','value': True, 'type': 'check'},
   #          {'name': '자동 리포트 시간(기본 20시 [HHMM으로])',   'code': 'auto_time','value': '2000', 'type': 'input'},
   #      ]
   # ),
   #  Site("COCO LABEL", "COCO_LABEL", "#121212", enabled=True,
   #       columns = [
   #           {"code": "product_code",        "value": "상품코드",        "checked": True},
   #           {"code": "category_main",       "value": "기본분류",        "checked": True},
   #           {"code": "category_2",          "value": "분류2",           "checked": True},
   #           {"code": "category_3",          "value": "분류3",           "checked": True},
   #           {"code": "product_name",        "value": "상품명",          "checked": True},
   #           {"code": "manufacturer",        "value": "제조사",          "checked": True},
   #           {"code": "origin",              "value": "원산지",          "checked": True},
   #           {"code": "brand",               "value": "브랜드",          "checked": True},
   #           {"code": "model",               "value": "모델",            "checked": True},
   #
   #           {"code": "product_type_1",      "value": "상품유형1",       "checked": True},
   #           {"code": "product_type_2",      "value": "상품유형2",       "checked": True},
   #           {"code": "product_type_3",      "value": "상품유형3",       "checked": True},
   #           {"code": "product_type_4",      "value": "상품유형4",       "checked": True},
   #           {"code": "product_type_5",      "value": "상품유형5",       "checked": True},
   #
   #           {"code": "basic_description",   "value": "기본설명",        "checked": True},
   #           {"code": "description",         "value": "상품설명",        "checked": True},
   #           {"code": "mobile_description",  "value": "모바일상품설명",  "checked": True},
   #
   #           {"code": "market_price",        "value": "시중가격",        "checked": True},
   #           {"code": "sale_price",          "value": "판매가격",        "checked": True},
   #           {"code": "phone_inquiry",        "value": "전화문의",        "checked": True},
   #
   #           {"code": "point",               "value": "포인트",          "checked": True},
   #           {"code": "point_type",          "value": "포인트타입",      "checked": True},
   #
   #           {"code": "seller_email",        "value": "판매자이메일",    "checked": True},
   #           {"code": "is_sale",             "value": "판매가능",        "checked": True},
   #
   #           {"code": "stock_qty",           "value": "재고수량",        "checked": True},
   #           {"code": "stock_alert_qty",     "value": "재고통보수량",    "checked": True},
   #
   #           {"code": "min_order_qty",       "value": "최소구매수량",    "checked": True},
   #           {"code": "max_order_qty",       "value": "최대구매수량",    "checked": True},
   #
   #           {"code": "tax_type",            "value": "과세유형",        "checked": True},
   #           {"code": "sort_order",          "value": "정렬순서",        "checked": True},
   #
   #           {"code": "image_1",             "value": "이미지1",         "checked": True},
   #           {"code": "image_2",             "value": "이미지2",         "checked": True},
   #           {"code": "image_3",             "value": "이미지3",         "checked": True},
   #           {"code": "image_4",             "value": "이미지4",         "checked": True},
   #           {"code": "image_5",             "value": "이미지5",         "checked": True},
   #           {"code": "image_6",             "value": "이미지6",         "checked": True},
   #           {"code": "image_7",             "value": "이미지7",         "checked": True},
   #           {"code": "image_8",             "value": "이미지8",         "checked": True},
   #           {"code": "image_9",             "value": "이미지9",         "checked": True},
   #           {"code": "image_10",            "value": "이미지10",        "checked": True},
   #
   #           {"code": "options",             "value": "옵션",            "checked": True},
   #       ],
   #        setting=[
   #            {'name': '1. 키워드(콤마(,)로 구분해주세요)', 'code': 'keyword',    'value': '베스트, 시계, 잡화, 남성, 에르메스프리미엄, 샤넬 프리미엄', 'type': 'input'}
   #        ],
   #  ),
   # Site("네이버 주식 번호", "NAVER_STOCK_PHONE", "#03C75A", enabled=True, popup=True,
   #    columns = [
   #       {"code": "company_name",     "value": "기업명",           "checked": True},
   #       {"code": "market_division",  "value": "시장 구분",        "checked": True},
   #       {"code": "stock_code",       "value": "종목코드",         "checked": True},
   #       {"code": "main_phone",       "value": "대표전화",         "checked": True},
   #       {"code": "ir_phone",         "value": "IR전화",          "checked": True},
   #       {"code": "home_page",        "value": "홈페이지",          "checked": True},
   #   ]
   # ),
   Site("호호요가", "HOHOYOGA", "#2BAAB1", enabled=True,
        columns = [
           {"code": "recruit_yn",               "value": "모집여부",        "checked": True},
           {"code": "company_nm",               "value": "업체명",          "checked": True},
           {"code": "deadline_dt",              "value": "마감날짜",        "checked": True},
           {"code": "region",                   "value": "지역",           "checked": True},
           {"code": "wage",                     "value": "임금",            "checked": True},
           {"code": "address",                  "value": "주소",            "checked": True},
           {"code": "contact",                  "value": "연락처",          "checked": True},
           {"code": "email",                    "value": "이메일주소",       "checked": True},
           {"code": "profile_required_yn",      "value": "프로필 필수여부",   "checked": True},
            {"code": "local_name",      "value": "지역이름",   "checked": True},
            {"code": "local_code",      "value": "지역코드",   "checked": True},
        ],
        setting=[
            {'name': '아이디', 'code': 'id',           'value': 'feelgood2',   'type': 'input'},
            {'name': '비밀번호', 'code': 'password',     'value': 'dyddks123!',  'type': 'input'},
            {'name': '시작번호', 'code': 'start_page',   'value': '',           'type': 'input'},
            {'name': '끝번호', 'code': 'end_page',     'value': '',         'type': 'input'},
            {'name': '지역이름', 'code': 'local_name',     'value': '',         'type': 'input'},
            {'name': '지역코드', 'code': 'local_code',     'value': '',         'type': 'input'},
        ],
   )
]

# 전역 변수
server_url = "http://vjrvj.cafe24.com"
# server_url = "http://localhost"

server_name = "MyAppAutoLogin"
