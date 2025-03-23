from src.workers.main.api_kohls_set_worker import ApiKohlsSetLoadWorker
from src.workers.main.api_mytheresa_set_worker import ApiMytheresaSetLoadWorker
from src.workers.main.api_zalando_set_worker import ApiZalandoSetLoadWorker
from src.workers.main.api_zara_set_worker import ApiZaraSetLoadWorker
from src.workers.main.api_mango_set_worker import ApiMangoSetLoadWorker
from src.workers.main.api_oldnavy_set_worker import ApiOldnavySetLoadWorker

WORKER_CLASS_MAP = {
    "MYTHERESA": ApiMytheresaSetLoadWorker,
    "ZALANDO": ApiZalandoSetLoadWorker,
    "OLDNAVY": ApiOldnavySetLoadWorker,
    "KOHLS": ApiKohlsSetLoadWorker,
    "ZARA": ApiZaraSetLoadWorker,
    "MANGO": ApiMangoSetLoadWorker
}