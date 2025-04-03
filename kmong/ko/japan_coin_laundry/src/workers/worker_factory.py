from src.workers.main.api_google_map_set_worker import ApiGoogleMapSetLoadWorker
from src.workers.main.api_naver_map_set_worker import ApiNaverMapSetLoadWorker

WORKER_CLASS_MAP = {
    "GOOGLE_MAP": ApiGoogleMapSetLoadWorker,
    "NAVER_MAP": ApiNaverMapSetLoadWorker
}