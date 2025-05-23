from urllib.parse import parse_qs, unquote
import time
from src.utils.log import log


def parse_urlencoded_form(raw_body: str) -> dict:
    decoded = unquote(raw_body)
    return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(decoded).items()}


def wait_for_response(request, timeout=30.0, interval=0.1):
    start = time.monotonic()
    while not request.response:
        if time.monotonic() - start > timeout:
            return None
        time.sleep(interval)
    return request.response