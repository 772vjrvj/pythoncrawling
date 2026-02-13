import os
import sys

# runtime 패키지를 import 할 수 있게 base_dir를 sys.path에 넣어준다
_base = os.path.abspath(".")
if _base not in sys.path:
    sys.path.insert(0, _base)

from runtime.mitm.addons import naver_band_member_addon

WORKERS = {
    "NAVER_BAND_MEMBER": naver_band_member_addon,
}

def get_addon_path(key):
    key = str(key).strip().upper()

    if key not in WORKERS:
        raise Exception("Unknown addon key: " + key)

    return WORKERS[key].__file__
