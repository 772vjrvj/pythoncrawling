import sys
import os
import asyncio
import json
from mitmproxy import ctx
from src.utils.logger import log_info, log_error, log_warn

# 실행 위치 기준으로 data.json 접근을 위해 base_dir 설정
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

DATA_JSON_PATH = os.path.join(get_base_dir(), "data.json")

# src 가이드 라우터를 위한 가운데 경로 추가
sys.path.insert(0, get_base_dir())

from src.utils.api_proxy import patch, local_web_req, delete as api_delete
from src.utils.common import to_iso_kst_format, compact

CRAWLING_SITE = 'GolfzonPark'
request_store = {}


def load_data():
    try:
        with open(DATA_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"[proxy_server] [data.json] 로딩 실패: {e}")
        return {}


def get_token():
    token = load_data().get("token")
    log_info(f"[proxy_server] token : {token}")
    return token

def get_store_id():
    store_id = load_data().get("store_id")
    log_info(f"[proxy_server] store_id : {store_id}")
    return store_id

def save_request(action, url, data):
    request_store[url] = {'action': action, 'data': data}
    log_info(f"[proxy_server] 저장됨: [{action}]:data - {data}")
    log_info(f"[proxy_server] 저장됨: [{action}]:url - {url}")

def match_and_dispatch(action, url, response_data):
    entry = request_store.get(url)
    log_info(f"[proxy_server] [match_and_dispatch] : [경로 확인] DATA_JSON_PATH: {DATA_JSON_PATH}")
    log_info(f"[proxy_server] [match_and_dispatch] : 시도: [{action}]:entry - {entry}")

    token = get_token()
    store_id = get_store_id()

    if action == 'delete_mobile':
        log_info(f"[proxy_server] [match_and_dispatch] : [{action}] 응답 처리")
        dispatch_action(action, {'request': None, 'response': response_data}, token, store_id)
        return

    if action == 'mobile_host':
        log_info(f"[proxy_server] [match_and_dispatch] : [{action}] 응답 처리")
        dispatch_action(action, {'request': None, 'response': response_data}, token, store_id)
        return

    if not entry or entry['action'] != action:
        return

    log_info(f"[proxy_server] [match_and_dispatch] : 요청-응답 매칭됨: [{action}] - {url}")
    request_data = entry['data']
    request_store.pop(url, None) # .pop(url, None)은 해당 url 키가 존재하면 그 값을 꺼내고, 딕셔너리에서 제거합니다.

    dispatch_action(action, {'request': request_data, 'response': response_data}, token, store_id)

def dispatch_action(action, combined_data, token, store_id):
    request = combined_data.get('request')
    response = combined_data.get('response')

    try:
        if action == 'register':
            entities = response.get('entitys') or response.get('entity') or []
            for entity in entities:
                payload = compact({
                    'externalId': str(entity.get('bookingNumber', [''])[0]),
                    'roomId': str(entity.get('machineNumber')),
                    'crawlingSite': CRAWLING_SITE,
                    'name': str(request.get('bookingName')),
                    'phone': str(request.get('cellNumber', '')),
                    'requests': request.get('bookingMemo'),
                    'paymented': request.get('paymentYn') == 'Y',
                    'partySize': int(request.get('bookingCnt', 1)),
                    'paymentAmount': int(
                        request.get('bookingTotAmount') or request.get('paymentTotAmount') or 0
                    ),
                    'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                    'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                    'externalGroupId': str(request.get('reserveNo')) if request.get('reserveNo') else None,
                }, ['phone'])
                log_info("[proxy_server] [dispatch_action] : register payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                patch(token, store_id, payload)

        elif action == 'edit':
            reserve_no = request.get('reserveNo')
            booking_number = request.get('bookingNumber')
            machine_number = request.get('machineNumber') or []
            entities = response.get('entitys', [])

            if reserve_no and isinstance(machine_number, list) and len(machine_number) > 0:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '모바일 예약 변경 취소',
                    'externalGroupId': str(reserve_no),
                }
                log_info("[proxy_server] delete 고객 payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                api_delete(token, store_id, payload, 'g')

            elif len(entities) > 0:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '수정 취소',
                    'externalId': str(booking_number),
                }
                log_info("[proxy_server] delete 운영자 payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                api_delete(token, store_id, payload)

            if len(entities) > 0:
                for entity in entities:
                    payload = compact({
                        'externalId': str(entity.get('bookingNumber', [''])[0]),
                        'roomId': str(entity.get('machineNumber')),
                        'crawlingSite': CRAWLING_SITE,
                        'name': str(request.get('bookingName')),
                        'phone': str(request.get('cellNumber', '')),
                        'requests': request.get('bookingMemo'),
                        'paymented': request.get('paymentYn') == 'Y',
                        'partySize': int(request.get('bookingCnt', 1)),
                        'paymentAmount': int(
                            request.get('bookingTotAmount') or request.get('paymentTotAmount') or 0
                        ),
                        'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                        'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                        'externalGroupId': str(reserve_no) if reserve_no else None,
                    }, ['phone'])
                    log_info("[proxy_server] [dispatch_action] : edit payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                    patch(token, store_id, payload)
            else:
                payload = compact({
                    'externalId': str(booking_number),
                    'roomId': str(request.get('machineNumber')),
                    'crawlingSite': CRAWLING_SITE,
                    'name': str(request.get('bookingName')),
                    'phone': str(request.get('cellNumber', '')),
                    'requests': request.get('bookingMemo'),
                    'paymented': request.get('paymentYn') == 'Y',
                    'partySize': int(request.get('bookingCnt', 1)),
                    'paymentAmount': int(
                        request.get('bookingTotAmount') or request.get('paymentTotAmount') or 0
                    ),
                    'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                    'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                    'externalGroupId': str(reserve_no) if reserve_no else None,
                }, ['phone'])
                log_info("[proxy_server] [dispatch_action] edit payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                patch(token, store_id, payload)

        elif action == 'edit_move':
            payload = compact({
                'externalId': str(request.get('bookingNumber')),
                'roomId': str(request.get('machineNumber')),
                'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                'crawlingSite': CRAWLING_SITE,
            })
            log_info("[proxy_server] [dispatch_action] edit_move payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
            patch(token, store_id, payload, 'm')

        elif action == 'delete':
            reserve_no = request.get('reservation.reserveNo')
            if reserve_no:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '모바일 고객 예약을 운영자가 취소',
                    'externalGroupId': str(reserve_no),
                }
                log_info("[proxy_server] delete 고객:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                api_delete(token, store_id, payload, 'g')
            else:
                booking_nums = request.get('bookingNums')
                if not isinstance(booking_nums, list):
                    booking_nums = [booking_nums]
                for num in booking_nums:
                    payload = {
                        'crawlingSite': CRAWLING_SITE,
                        'reason': '운영자 취소',
                        'externalId': str(num),
                    }
                    log_info("[proxy_server] [dispatch_action] delete 운영자:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                    api_delete(token, store_id, payload)

        elif action == 'delete_mobile':
            destroyed = response.get('entity', {}).get('destroy', [])
            if destroyed:
                reserve_no = destroyed[0].get('reserveNo')
                if reserve_no:
                    payload = {
                        'crawlingSite': CRAWLING_SITE,
                        'reason': '모바일 고객 예약 취소',
                        'externalGroupId': str(reserve_no),
                    }
                    log_info("[proxy_server] [dispatch_action] delete 모바일 고객:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
                    api_delete(token, store_id, payload, 'g')

        elif action == 'reseration':
            payload = compact({
                'bookingDate': request.get('booking_date'),
                'type': 'p'
            }, [])

            log_info("[proxy_server] [dispatch_action] [전화예약] reseration payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
            local_web_req(token, store_id, payload)

        elif action == 'mobile_host':
            entitys = response.get('entitys', [])
            reserve_datetime = None

            if entitys and isinstance(entitys, list):
                reserve_datetime = entitys[0].get('reserveDatetime')

            payload = compact({
                'bookingDate': reserve_datetime,
                'type': 'm'
            }, [])

            log_info("[proxy_server] [dispatch_action] [모바일 예약 요청] reservation payload:\n" +
                     json.dumps(payload, ensure_ascii=False, indent=2))

            local_web_req(token, store_id, payload)

        else:
            log_warn(f"[proxy_server] [dispatch_action] 알 수 없는 액션: {action}")

    except Exception as e:
        log_error(f"[proxy_server] [dispatch_action] 처리 실패 [{action}]: {e}")
