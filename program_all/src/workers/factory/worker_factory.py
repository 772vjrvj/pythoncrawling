# from src.workers.main.api_albamon_set_worker                        import ApiAlbamonSetLoadWorker
# from src.workers.main.api_naver_place_set_worker                    import ApiNaverPlaceSetLoadWorker
# from src.workers.main.api_naver_place_loc_all_set_worker            import ApiNaverPlaceLocAllSetLoadWorker
# from src.workers.main.api_naver_place_url_all_set_worker            import ApiNaverPlaceUrlAllSetLoadWorker
# from src.workers.main.api_naver_blog_contents_set_worker            import ApiNaverBlogContentsSetLoadWorker
# from src.workers.main.api_coupang_set_worker                        import ApiCoupangSetLoadWorker
# from src.workers.main.api_alba_set_worker                           import ApiAlbaSetLoadWorker
# from src.workers.main.api_sotong_set_worker                         import ApiSotongSetLoadWorker
# from src.workers.main.api_seoulfood2025_place_set_worker            import ApiSeoulfood2025PlaceSetLoadWorker
# from src.workers.main.api_iherb_set_worker                          import ApiIherbSetLoadWorker
# from src.workers.main.api_yupoo_set_worker                          import ApiYupooSetLoadWorker
# from src.workers.main.api_ovreple_set_worker                        import ApiOvrepleSetLoadWorker
# from src.workers.main.api_1004ya_set_worker                         import Api1004yaSetLoadWorker
# from src.workers.main.api_app_sensortower_set_worker                import ApiAppSensertowerSetLoadWorker

# from src.workers.main.api_abcmart_brand_set_worker                  import ApiAbcmartBrandSetLoadWorker
# from src.workers.main.api_abcmart_detail_set_worker                 import ApiAbcmartDetailSetLoadWorker
# from src.workers.main.api_grandstage_brand_set_worker               import ApiGrandstageBrandSetLoadWorker
# from src.workers.main.api_grandstage_detail_set_worker              import ApiGrandstageDetailSetLoadWorker
# from src.workers.main.api_okmall_brand_set_worker                   import ApiOkmallBrandSetLoadWorker
# from src.workers.main.api_okmall_detail_set_worker                  import ApiOkmallDetailSetLoadWorker
# from src.workers.main.api_onthespot_brand_set_worker                import ApiOnthespotBrandSetLoadWorker
# from src.workers.main.api_onthespot_detail_set_worker               import ApiOnthespotDetailSetLoadWorker

# from src.workers.main.api_the_first_hall_wedding_set_worker         import ApiThefirsthallweddingDetailSetLoadWorker

# from src.workers.main.api_nh_bank_set_worker                        import ApiNhBankSetLoadWorker
# from src.workers.main.api_naver_cafe_count_only_set_worker          import ApiNaverCafeCountOnlySetLoadWorker
# from src.workers.main.api_naver_land_real_estate_loc_all_set_worker import ApiNaverLandRealEstateLocAllSetLoadWorker
# from src.workers.main.api_contest_deadline_set_worker               import ApiContestDealineSetLoadWorker
# from src.workers.main.api_naver_land_real_estate_detail_set_worker  import ApiNaverLandRealEstateDetailSetLoadWorker
# from src.workers.main.invoice.api_invoice_set_worker                import ApiInvoiceSetLoadWorker
from src.workers.main.api_kakao_store_food_set_worker  import Api


WORKER_CLASS_MAP = {
    # "ALBAMON"                           :   ApiAlbamonSetLoadWorker,
    # "NAVER_PLACE"                       :   ApiNaverPlaceSetLoadWorker,
    # "NAVER_PLACE_LOC_ALL"               :   ApiNaverPlaceLocAllSetLoadWorker,
    # "NAVER_PLACE_URL_ALL"               :   ApiNaverPlaceUrlAllSetLoadWorker,
    # "NAVER_BLOG_CTT"                    :   ApiNaverBlogContentsSetLoadWorker,
    # "COUPANG"                           :   ApiCoupangSetLoadWorker,
    # "ALBA"                              :   ApiAlbaSetLoadWorker,
    # "SOTONG"                            :   ApiSotongSetLoadWorker,
    # "SEOUL_FOOD_2025"                   :   ApiSeoulfood2025PlaceSetLoadWorker,
    # "IHERB"                             :   ApiIherbSetLoadWorker,
    # "YUPOO"                             :   ApiYupooSetLoadWorker,
    # "OVREPLE"                           :   ApiOvrepleSetLoadWorker,
    # "1004YA"                            :   Api1004yaSetLoadWorker,
    # "APP_SENSORTOWER"                   :   ApiAppSensertowerSetLoadWorker,

    # "ABC_MART_BRAND"                    :   ApiAbcmartBrandSetLoadWorker,
    # "ABC_MART_DETAIL"                   :   ApiAbcmartDetailSetLoadWorker,
    # "GRAND_STAGE_BRAND"                 :   ApiGrandstageBrandSetLoadWorker,
    # "GRAND_STAGE_DETAIL"                :   ApiGrandstageDetailSetLoadWorker,
    # "ON_THE_SPOT_BRAND"                 :   ApiOnthespotBrandSetLoadWorker,
    # "ON_THE_SPOT_DETAIL"                :   ApiOnthespotDetailSetLoadWorker,
    # "OK_MALL_BRAND"                     :   ApiOkmallBrandSetLoadWorker,
    # "OK_MALL_DETAIL"                    :   ApiOkmallDetailSetLoadWorker,

    # "THE_FIRST_HALL_WEDDING"            :   ApiThefirsthallweddingDetailSetLoadWorker,

    # "NH_BANK"                           :   ApiNhBankSetLoadWorker,
    # "NAVER_CAFE_CTT_CNT_ONLY"           :   ApiNaverCafeCountOnlySetLoadWorker,
    # "NAVER_LAND_REAL_ESTATE_LOC_ALL"    :   ApiNaverLandRealEstateLocAllSetLoadWorker,
    # "CONTEST_DEADLINE"                  :   ApiContestDealineSetLoadWorker,
    # "NAVER_LAND_REAL_ESTATE_DETAIL"     :   ApiNaverLandRealEstateDetailSetLoadWorker,
    # "INVOICE"                           :   ApiInvoiceSetLoadWorker,
    "INVOICE"                           :   ApiInvoiceSetLoadWorker,
}