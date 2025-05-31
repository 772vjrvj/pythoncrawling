from urllib.parse import parse_qs, unquote
import time
from src.utils.log import log


def parse_urlencoded_form(raw_body: str) -> dict:
    decoded = unquote(raw_body)
    return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(decoded).items()}


def wait_for_response(driver, url_part: str, timeout=7.0, response_timeout=5.0):
    """
    요청 + 응답까지 안정적으로 대기하는 함수
    :param driver: Selenium Wire driver
    :param url_part: URL 일부 문자열
    :param timeout: 요청 대기 시간
    :param response_timeout: 요청 이후 응답 기다리는 시간
    :return: response or None
    """
    try:
        request = driver.wait_for_request(url_part, timeout=timeout)

        # 응답 기다리기
        wait_start = time.time()
        while not request.response and time.time() - wait_start < response_timeout:
            time.sleep(0.1)

        if not request.response:
            log(f"요청은 잡았으나 응답이 {response_timeout}s 내 도착하지 않음: {request.url}")
            return None

        return request.response

    except Exception as e:
        log(f"wait_for_response 예외 발생: {e}")
        return None


def wait_for_response_mobile_delete(driver, url_part: str, timeout=7.0, response_timeout=5.0):
    """
    지정된 URL 일부가 포함된 가장 최신 요청의 응답을 기다림

    :param driver: Selenium Wire driver
    :param url_part: 요청 URL에 포함되는 고정된 일부 문자열 (ex: 'bookingNumber=80538110')
    :param timeout: 요청이 도착할 때까지 최대 대기 시간 (초)
    :param response_timeout: 응답이 도착할 때까지의 추가 대기 시간 (초)
    :return: response or None
    """
    try:
        matched_request = None
        end_time = time.time() + timeout

        # timeout까지 기다리며 최신 요청을 계속 갱신
        while time.time() < end_time:
            for req in reversed(driver.requests):  # 최신 요청부터 확인
                if url_part in req.url:
                    matched_request = req
                    break
            if matched_request:
                break
            time.sleep(0.1)

        if not matched_request:
            log(f"[] {timeout}s 내에 '{url_part}' 포함된 요청을 찾지 못함")
            return None

        # 응답 기다리기
        wait_start = time.time()
        while not matched_request.response and time.time() - wait_start < response_timeout:
            time.sleep(0.1)

        if not matched_request.response:
            log(f"[] 요청은 감지했지만 {response_timeout}s 내 응답 도착 안함: {matched_request.url}")
            return None

        return matched_request.response

    except Exception as e:
        log(f"[] wait_for_response 예외 발생: {e}")
        return None
