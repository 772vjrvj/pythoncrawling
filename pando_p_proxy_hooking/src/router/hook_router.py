# src/router/hook_router.py
import sys
import os
# src 상위 루트 경로를 PYTHONPATH에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import json
from src.utils.api_test import patch, delete as api_delete
from src.utils.token_manager import get_token, get_store_id
from src.utils.common import to_iso_kst_format, compact
from src.utils.logger import get_logger, info_log, error_log


CRAWLING_SITE = 'GolfzonPark'
request_store = {}
logger = get_logger("proxy_logger")


def save_request(action, url, data):
    request_store[url] = {'action': action, 'data': data}
    info_log(f"저장됨: [{action}]:data - {data}", logger=logger)
    info_log(f"저장됨: [{action}]:url - {url}", logger=logger)


async def match_and_dispatch(action, url, response_data):
    entry = request_store.get(url)
    info_log(f"저장됨: [{action}]:entry - {entry}", logger=logger)

    token = get_token()
    store_id = get_store_id()

    if action == 'delete_mobile':
        info_log(f"[{action}] 단독 응답 처리", logger=logger)
        await dispatch_action(action, {'request': None, 'response': response_data}, token, store_id)
        return

    if not entry or entry['action'] != action:
        return

    info_log(f"요청-응답 매칭됨: [{action}] - {url}", logger=logger)
    request_data = entry['data']
    request_store.pop(url, None)

    await dispatch_action(action, {'request': request_data, 'response': response_data}, token, store_id)


async def dispatch_action(action, combined_data, token, store_id):
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
                    'paymentAmount': int(request.get('bookingTotAmount', 0)),
                    'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                    'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                    'externalGroupId': str(request.get('reserveNo')) if request.get('reserveNo') else None,
                }, exclude_keys=['phone'])
                info_log("register payload:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                await patch(token, store_id, payload)

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
                info_log("delete 고객 payload:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                await api_delete(token, store_id, payload, 'g')

            elif len(entities) > 0:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '수정 취소',
                    'externalId': str(booking_number),
                }
                info_log("delete 운영자 payload:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                await api_delete(token, store_id, payload)

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
                        'paymentAmount': int(request.get('bookingTotAmount', 0)),
                        'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                        'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                        'externalGroupId': str(reserve_no) if reserve_no else None,
                    }, exclude_keys=['phone'])
                    info_log("edit payload:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                    await patch(token, store_id, payload)
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
                    'paymentAmount': int(request.get('bookingTotAmount', 0)),
                    'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                    'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                    'externalGroupId': str(reserve_no) if reserve_no else None,
                }, exclude_keys=['phone'])
                info_log("edit payload:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                await patch(token, store_id, payload)

        elif action == 'edit_move':
            payload = compact({
                'externalId': str(request.get('bookingNumber')),
                'roomId': str(request.get('machineNumber')),
                'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                'crawlingSite': CRAWLING_SITE,
            })
            info_log("edit_move payload:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
            await patch(token, store_id, payload, 'm')

        elif action == 'delete':
            reserve_no = request.get('reservation.reserveNo')
            if reserve_no:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '모바일 고객 예약을 운영자가 취소',
                    'externalGroupId': str(reserve_no),
                }
                info_log("delete 고객:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                await api_delete(token, store_id, payload, 'g')
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
                    info_log("delete 운영자:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                    await api_delete(token, store_id, payload)

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
                    info_log("delete 모바일 고객:", json.dumps(payload, ensure_ascii=False, indent=2), logger=logger)
                    await api_delete(token, store_id, payload, 'g')

        else:
            info_log(f"알 수 없는 액션: {action}", logger=logger)

    except Exception as e:
        error_log(f"dispatch 처리 실패 [{action}]: {e}", logger=logger)
