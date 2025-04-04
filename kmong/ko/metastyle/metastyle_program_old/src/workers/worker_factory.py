from src.workers.main.delay.api_kohls_set_worker import ApiKohlsSetLoadWorker
from src.workers.main.delay.api_mytheresa_set_worker import ApiMytheresaSetLoadWorker
from src.workers.main.delay.api_zalando_set_worker import ApiZalandoSetLoadWorker
from src.workers.main.site.api_zara_set_worker import ApiZaraSetLoadWorker
from src.workers.main.site.api_mango_set_worker import ApiMangoSetLoadWorker
from src.workers.main.delay.api_oldnavy_set_worker import ApiOldnavySetLoadWorker
from src.workers.main.site.api_farfetch_set_worker import ApiFarfetchSetLoadWorker
from src.workers.main.site.api_hm_set_worker import ApiHmSetLoadWorker
from src.workers.main.site.api_stores_set_worker import ApiStoresSetLoadWorker
from src.workers.main.site.api_bananarepublic_set_worker import ApiBananarepublicSetLoadWorker
from src.workers.main.site.api_aritzia_set_worker import ApiAritziaSetLoadWorker

WORKER_CLASS_MAP = {
    "MYTHERESA": ApiMytheresaSetLoadWorker,
    "ZALANDO": ApiZalandoSetLoadWorker,
    "OLDNAVY": ApiOldnavySetLoadWorker,
    "KOHLS": ApiKohlsSetLoadWorker,
    "ZARA": ApiZaraSetLoadWorker,
    "MANGO": ApiMangoSetLoadWorker,
    "FARFETCH": ApiFarfetchSetLoadWorker,
    "H&M": ApiHmSetLoadWorker,
    "&OTHER STORIES": ApiStoresSetLoadWorker,
    "BANANAREPUBLIC": ApiBananarepublicSetLoadWorker,
    "ARITZIA": ApiAritziaSetLoadWorker,
}