from src.workers.main.api_albamon_set_worker import ApiAlbamonSetLoadWorker

WORKER_CLASS_MAP = {
    "ALBAMON": ApiAlbamonSetLoadWorker,
    "NAVER_PLACE": None,
    "COUPANG": None,
    "ALBA": None,
}