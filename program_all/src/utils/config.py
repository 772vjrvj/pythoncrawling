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
    #
    # Site("네이버 플레이스", "NAVER_PLACE", "#03C75A", enabled=True,
    #      setting=[]
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

     Site("네이버 부동산업체 전국 번호", "NAVER_LAND_REAL_ESTATE_LOC_ALL", "#03C75A", enabled=True,
          setting=[
              {'name': '1. 키워드(콤마(,)로 구분해주세요)', 'code': 'keyword',    'value': '', 'type': 'input'}
          ],
          columns = [
              # 메타
              {"code": "article_number",        "value": "번호",   "checked": False},
              {"code": "region",                "value": "지역",   "checked": False},
              {"code": "city",                  "value": "시도",   "checked": True},
              {"code": "division",              "value": "시군구",  "checked": True},
              {"code": "sector",                "value": "읍면동",  "checked": True},

              # {"code": "item_name",             "value": "매물명",  "checked": True},

              # 주소/위치
              {"code": "latitude",              "value": "위도",         "checked": False},   # yCoordinate
              {"code": "longitude",             "value": "경도",         "checked": False},   # xCoordinate
              {"code": "keyword",               "value": "키워드",  "checked": True},
              {"code": "complex_name",          "value": "단지명",  "checked": True},
              {"code": "complex_dong_name",     "value": "동(단지)",     "checked": True},

              # 중개사
              {"code": "brokerage_name",        "value": "중개사무소 이름",      "checked": True},
              {"code": "broker_name",           "value": "중개사 이름",        "checked": True},
              {"code": "broker_address",        "value": "중개사무소 주소",         "checked": True},
              {"code": "phone_brokerage",       "value": "중개사무소 번호",   "checked": True},
              {"code": "phone_mobile",          "value": "중개사 헨드폰번호",   "checked": True},
                  # 층/방향
              {"code": "floor_info",            "value": "층",           "checked": False},   # 예: "2/6" 또는 "고/8"
              {"code": "target_floor",          "value": "층(목표)",     "checked": False},
              {"code": "total_floor",           "value": "층(전체)",     "checked": False},
              {"code": "direction_ko",          "value": "방향",         "checked": False},   # self._direction_to_ko 적용값
              # {"code": "direction_raw",         "value": "방향(원문)",   "checked": True},
              {"code": "direction_standard",    "value": "방향기준",     "checked": False},

              # 면적
              {"code": "exclusive_sqm_pyeong",  "value": "전용(㎡/평)",  "checked": False},
              {"code": "supply_sqm_pyeong",     "value": "공급(㎡/평)",  "checked": False},
              {"code": "contract_sqm_pyeong",   "value": "계약(㎡/평)",  "checked": False},

              # 가격/비용
              {"code": "deal_price_fmt",        "value": "매매가",       "checked": False},   # 예: "8억"
              {"code": "deal_price",            "value": "매매가(원)",   "checked": False},
              {"code": "maintenance_fee",       "value": "관리비",       "checked": False},

              # 유형/일자
              # {"code": "real_estate_type",      "value": "부동산종류",   "checked": True},
           # {"code": "trade_type",            "value": "거래유형",     "checked": True},
              {"code": "exposure_date",         "value": "노출일",       "checked": False},
             {"code": "confirm_date",          "value": "확인일",       "checked": False},
              {"code": "approval_elapsed_year", "value": "준공연차",     "checked": False},
              {"code": "completion_date",       "value": "준공일",       "checked": False},
          ],
          region = True
          ),

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
    #Site("송장번호 택배사", "DELIVERY_CONTENT", "#00A1FF", enabled=True, popup=True,
    #    columns = [
    #     {"code": "market",           "value": "마켓",           "checked": True},
    #     {"code": "order_date",       "value": "주문일자",        "checked": True},
    #     {"code": "id",               "value": "id",            "checked": True},
    #     {"code": "password",         "value": "password",      "checked": True},
    #     {"code": "order_code",       "value": "주문고유코드",    "checked": True},
    #      {"code": "invoice_no",       "value": "송장번호",       "checked": True},
    #      {"code": "delivery_company", "value": "택배사",         "checked": True}
    #   ]
    #),
]

# 전역 변수
server_url = "http://vjrvj.cafe24.com"
# server_url = "http://localhost"

server_name = "MyAppAutoLogin"
