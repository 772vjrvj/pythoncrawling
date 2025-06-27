# hook_router.py
import asyncio
import json
from src.utils.api import patch, delete as api_delete  # 'delete'는 파이썬 예약어라 api_delete로 임포트
from src.services.token_manager import get_token, get_store_id
from src.utils.common import to_iso_kst_format, compact  # 필요시 구현

CRAWLING_SITE = 'GolfzonPark'
request_store = {}

def nodeLog(*args):
    print(*args)

def nodeError(*args):
    print("[ERROR]", *args)

def save_request(action, url, data):
    request_store[url] = {'action': action, 'data': data}
    nodeLog(f"📅 저장됨: [{action}]:data - {data}")
    nodeLog(f"📅 저장됨: [{action}]:url - {url}")

async def match_and_dispatch(action, url, response_data):
    entry = request_store.get(url)
    nodeLog(f"📅 저장됨: [{action}]:entry - {entry}")

    token = get_token()
    store_id = get_store_id()

    # delete_mobile 은 요청 매칭 없이도 처리
    if action == 'delete_mobile':
        nodeLog(f"📦 [{action}] 단독 응답 처리")
        await dispatch_action(action, {'request': None, 'response': response_data}, token, store_id)
        return

    # 나머지는 요청-응답 매칭 필요
    if not entry or entry['action'] != action:
        return

    nodeLog(f"✅ 요청-응답 매칭됨: [{action}] - {url}")
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
                nodeLog("📦 register payload:", json.dumps(payload, ensure_ascii=False, indent=2))
                await patch(token, store_id, payload)

        elif action == 'edit':
            reserve_no = request.get('reserveNo')
            booking_number = request.get('bookingNumber')
            machine_number = request.get('machineNumber') or []
            entities = response.get('entitys', [])

            # 모바일에서 2개 이상 수정 시 기존 예약 삭제
            if reserve_no and isinstance(machine_number, list) and len(machine_number) > 0:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '모바일 예약 변경 취소',
                    'externalGroupId': str(reserve_no),
                }
                nodeLog("📦 delete 고객 payload:", json.dumps(payload, ensure_ascii=False, indent=2))
                await api_delete(token, store_id, payload, 'g')

            # 웹에서 예약수 2 이상이면 기존 예약 모두 삭제
            elif len(entities) > 0:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '수정 취소',
                    'externalId': str(booking_number),
                }
                nodeLog("📦 delete 운영자 payload:", json.dumps(payload, ensure_ascii=False, indent=2))
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
                    nodeLog("📦 edit payload:", json.dumps(payload, ensure_ascii=False, indent=2))
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
                nodeLog("📦 edit payload:", json.dumps(payload, ensure_ascii=False, indent=2))
                await patch(token, store_id, payload)

        elif action == 'edit_move':
            payload = compact({
                'externalId': str(request.get('bookingNumber')),
                'roomId': str(request.get('machineNumber')),
                'startDate': to_iso_kst_format(request.get('bookingStartDt')),
                'endDate': to_iso_kst_format(request.get('bookingEndDt')),
                'crawlingSite': CRAWLING_SITE,
            })
            nodeLog("📦 edit_move payload:", json.dumps(payload, ensure_ascii=False, indent=2))
            await patch(token, store_id, payload, 'm')

        elif action == 'delete':
            reserve_no = request.get('reservation.reserveNo')
            if reserve_no:
                payload = {
                    'crawlingSite': CRAWLING_SITE,
                    'reason': '모바일 고객 예약을 운영자가 취소',
                    'externalGroupId': str(reserve_no),
                }
                nodeLog("📦 delete 고객:", json.dumps(payload, ensure_ascii=False, indent=2))
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
                    nodeLog("📦 delete 운영자:", json.dumps(payload, ensure_ascii=False, indent=2))
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
                    nodeLog("📦 delete 모바일 고객:", json.dumps(payload, ensure_ascii=False, indent=2))
                    await api_delete(token, store_id, payload, 'g')

        else:
            nodeLog(f"⚠️ 알 수 없는 액션: {action}")
    except Exception as e:
        nodeError(f"❌ dispatch 처리 실패 [{action}]: {e}")
