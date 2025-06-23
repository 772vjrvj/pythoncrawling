from src.workers.main.api_albamon_set_worker import ApiAlbamonSetLoadWorker
from src.workers.main.api_naver_place_set_worker import ApiNaverPlaceSetLoadWorker
from src.workers.main.api_naver_blog_contents_set_worker import ApiNaverBlogContentsSetLoadWorker
from src.workers.main.api_coupang_set_worker import ApiCoupangSetLoadWorker
from src.workers.main.api_alba_set_worker import ApiAlbaSetLoadWorker
from src.workers.main.api_sotong_set_worker import ApiSotongSetLoadWorker
from src.workers.main.api_seoulfood2025_place_set_worker import ApiSeoulfood2025PlaceSetLoadWorker
from src.workers.main.api_iherb_set_worker import ApiIherbSetLoadWorker





WORKER_CLASS_MAP = {
    "ALBAMON": ApiAlbamonSetLoadWorker,
    "NAVER_PLACE": ApiNaverPlaceSetLoadWorker,
    "COUPANG": ApiCoupangSetLoadWorker,
    "ALBA": ApiAlbaSetLoadWorker,
    "SOTONG": ApiSotongSetLoadWorker,
    "SEOUL_FOOD_2025": ApiSeoulfood2025PlaceSetLoadWorker,
    "NAVER_BLOG_CTT": ApiNaverBlogContentsSetLoadWorker,
    "IHERB": ApiIherbSetLoadWorker
}