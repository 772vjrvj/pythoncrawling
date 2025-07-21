from src.workers.main.api_albamon_set_worker import ApiAlbamonSetLoadWorker
# from src.workers.main.api_naver_place_set_worker import ApiNaverPlaceSetLoadWorker
from src.workers.main.api_naver_place_loc_all_set_worker import ApiNaverPlaceLocAllSetLoadWorker
from src.workers.main.api_naver_blog_contents_set_worker import ApiNaverBlogContentsSetLoadWorker
from src.workers.main.api_coupang_set_worker import ApiCoupangSetLoadWorker
from src.workers.main.api_alba_set_worker import ApiAlbaSetLoadWorker
from src.workers.main.api_sotong_set_worker import ApiSotongSetLoadWorker
from src.workers.main.api_seoulfood2025_place_set_worker import ApiSeoulfood2025PlaceSetLoadWorker
from src.workers.main.api_iherb_set_worker import ApiIherbSetLoadWorker
from src.workers.main.api_yupoo_set_worker import ApiYupooSetLoadWorker
from src.workers.main.api_ovreple_set_worker import ApiOvrepleSetLoadWorker
from src.workers.main.api_1004ya_set_worker import Api1004yaSetLoadWorker

WORKER_CLASS_MAP = {
    "ALBAMON": ApiAlbamonSetLoadWorker,
    # "NAVER_PLACE": ApiNaverPlaceSetLoadWorker,
    "NAVER_PLACE_LOC_ALL": ApiNaverPlaceLocAllSetLoadWorker,
    "NAVER_BLOG_CTT": ApiNaverBlogContentsSetLoadWorker,
    "COUPANG": ApiCoupangSetLoadWorker,
    "ALBA": ApiAlbaSetLoadWorker,
    "SOTONG": ApiSotongSetLoadWorker,
    "SEOUL_FOOD_2025": ApiSeoulfood2025PlaceSetLoadWorker,
    "IHERB": ApiIherbSetLoadWorker,
    "YUPOO": ApiYupooSetLoadWorker,
    "OVREPLE": ApiOvrepleSetLoadWorker,
    "1004YA": Api1004yaSetLoadWorker,
}