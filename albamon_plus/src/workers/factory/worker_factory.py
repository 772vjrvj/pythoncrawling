from src.workers.main.api_albamon_set_worker import ApiAlbamonSetLoadWorker
from src.workers.main.api_naver_place_set_worker import ApiNaverPlaceSetLoadWorker
from src.workers.main.api_coupang_set_worker import ApiCoupangSetLoadWorker
from src.workers.main.api_alba_set_worker import ApiAlbaSetLoadWorker

WORKER_CLASS_MAP = {
    "ALBAMON": ApiAlbamonSetLoadWorker,
    "NAVER_PLACE": ApiNaverPlaceSetLoadWorker,
    "COUPANG": ApiCoupangSetLoadWorker,
    "ALBA": ApiAlbaSetLoadWorker,
}