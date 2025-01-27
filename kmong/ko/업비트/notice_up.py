import asyncio
import logging
import random
import re
import requests
import time
from binance import AsyncClient
from binance.enums import *
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 키와 시크릿 키 (실제 값으로 교체해야 합니다)
api_key = 
api_secret = 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,imgwebp,*/*;q=0.8"
}

LAST_NOTICE_ID = 0  # 최근 공지 ID 값
purchase_records = []  # 구매한 코인 정보를 저장할 리스트
client = None  # 클라이언트 글로벌 선언

# 정규식 컴파일
RE_BRACKETS = re.compile(r'\((.*?)\)')
RE_KOREAN = re.compile(r'[가-힣]')

USDT = "USDT"
# 프록시 리스트
PROXIES = [
10개 이상의 프록시 사용중
]

# 요청 회수 제한
REQUEST_LIMIT = 150

# 요청 시간 기록을 위한 deque
request_times = deque(maxlen=REQUEST_LIMIT)
requests_cnt = 0


async def create_client():
    global client
    client = await AsyncClient.create(api_key, api_secret)

async def maintain_client_health():
    global client
    while True:
        try:
            # 클라이언트의 상태를 확인하기 위해 계정 정보를 요청
            await client.get_account()
            logging.info("클라이언트 상태 양호")
        except Exception as e:
            logging.error(f"클라이언트 상태 확인 중 오류 발생: {e}")
            # 클라이언트를 다시 생성
            await create_client()
            logging.info("클라이언트 재생성 완료")

        # 5분마다 상태 확인
        await asyncio.sleep(300)

def is_time_difference_more_than_one_second(first_listed_at):
    try:
        # 문자열을 datetime 객체로 변환 (오프셋 포함)
        first_listed_time = datetime.fromisoformat(first_listed_at)

        # 현재 시간을 오프셋 포함된 datetime 객체로 변환
        current_time = datetime.now(timezone.utc).astimezone(first_listed_time.tzinfo)

        # 시간 차이 계산
        time_difference = current_time - first_listed_time
        logging.info(f"{time_difference} 초 차이 발생")

        # 1초 이상 차이나는지 확인
        return time_difference > timedelta(seconds=5)
    except ValueError as e:
        logging.error(f"날짜 형식 변환 중 에러 발생: {e}")
        return False

def check_string_conditions(title):
    required_keywords = ['KRW', '마켓']
    optional_keywords = ['디지털 자산 추가', '신규 거래지원 안내']

    for keyword in required_keywords:
        if keyword not in title:
            return False

    contains_optional = any(keyword in title for keyword in optional_keywords)
    return contains_optional

def extract_coin_symbols(title):
    coin_symbols = []
    matches = RE_BRACKETS.findall(title)
    for match in matches:
        if RE_KOREAN.search(match):
            continue
        coin_symbols.extend([name.strip() for name in match.split(',')])

    return coin_symbols

async def get_usdt_balance():
    global client
    try:
        balance = await client.get_asset_balance(asset='USDT')
        return float(balance['free'])
    except Exception as e:
        logging.error(f"잔액 조회 중 오류 발생: {e}")
        return 0.0

async def order_buy(symbol, quantity):
    global client
    try:
        order = await client.create_order(
            symbol=symbol,
            side="BUY",
            type='MARKET',
            quantity=Decimal(quantity).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        )

        logging.info(f"구매 주문: {order}")
        return order

    except Exception as e:
        logging.error(f"주문 중 오류 발생: {e}")
        return None

async def order_sell(symbol, quantity):
    global client
    try:
        order = await client.create_order(
            symbol=symbol,
            side="SELL",
            type='MARKET',
            quantity=Decimal(quantity).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        )

        logging.info(f"판매 주문: {order}")
        return order

    except Exception as e:
        logging.error(f"판매 주문 중 오류 발생: {e}")
        return None

async def buy_coins(coin_symbols):
    # TODO 이부분 그냥 USDT 구매가격 고정해놓는게 더 낫지않을까?
    usdt_balance = await get_usdt_balance()
    if usdt_balance == 0:
        logging.info("사용 가능한 USDT 잔액이 없습니다.")
        return

    tasks = []
    for symbol in coin_symbols:
        symbol = symbol + USDT
        # symbol의 현재 가격을 조회하여 quantity를 계산
        ticker = await client.get_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])
        quantity = usdt_balance / price
        task = asyncio.create_task(order_buy(symbol, quantity))
        tasks.append(task)

    orders = await asyncio.gather(*tasks)
    for order in orders:
        if order:
            purchase_time = datetime.now()
            total_qty = Decimal(0)
            for fill in order['fills']:
                qty = Decimal(fill['qty'])
                commission = Decimal(fill['commission'])
                net_qty = qty - commission
                total_qty += net_qty
            purchase_records.append((purchase_time, order['symbol'], float(total_qty)))

def fetch_notices(session, proxy, loop):
    global LAST_NOTICE_ID
    url = "https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=1&category=trade"

    # 프록시 설정
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        if proxies:
            response = session.get(url, headers=HEADERS, proxies=proxies, verify=False)
        else:
            response = session.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        time.sleep(5)
        logging.error(f"HTTP 요청 중 에러 발생: {e}")
        return

    if data is None or not data or data['success'] == 'false':
        logging.error("데이터가 null이거나 빈 값이거나 data['success']가 False입니다.")
        return

    notices = data.get('data', {}).get('notices', [])
    if not notices:
        logging.info("공지사항이 없습니다.")
        return

    notice = notices[0]
    current_notice_id = int(notice['id'])

    if current_notice_id <= LAST_NOTICE_ID:
        logging.info("새로운 공지사항이 없습니다.")
        return

    LAST_NOTICE_ID = current_notice_id  # ID 값 갱신
    title = notice['title']
    logging.info(f"제목: {title}")

    if check_string_conditions(title) and not is_time_difference_more_than_one_second(notice['first_listed_at']):
        coin_symbols = extract_coin_symbols(title)
        # 실제 코인을 구매하는 부분
        logging.info(f"코인 목록: {coin_symbols}")
        asyncio.run_coroutine_threadsafe(buy_coins(coin_symbols), loop)

def main(loop):
    global requests_cnt

    with requests.Session() as session:
        session.headers.update(HEADERS)
        while True:
            current_time = time.time()

            # 1분 내의 요청 시간을 유지
            while request_times and current_time - request_times[0] > 60:
                request_times.popleft()

            # 요청 횟수가 제한을 초과하면 대기
            if len(request_times) >= REQUEST_LIMIT:
                logging.info(f"{REQUEST_LIMIT}회 요청 후 잠시 대기합니다.")
                time.sleep(5)  # 제한 시간까지 대기

            # 프록시를 순차적으로 선택
            proxy = PROXIES[requests_cnt % len(PROXIES)]

            fetch_notices(session, proxy, loop)
            requests_cnt += 1
            request_times.append(current_time)

            # PROXIES 길이보다 길어질 경우 requests_cnt 초기화
            if requests_cnt >= len(PROXIES):
                requests_cnt = 0

            # 랜덤한 대기 시간 설정
            sleep_time = random.uniform(0.2, 0.4)
            time.sleep(sleep_time)

async def monitor_and_sell():
    global client
    while True:
        now = datetime.now()
        for record in purchase_records[:]:
            purchase_time, symbol, quantity = record
            if (now - purchase_time).total_seconds() >= 5:
                await order_sell(symbol, quantity)
                purchase_records.remove(record)
        await asyncio.sleep(1)

if __name__ == "__main__":
    # 클라이언트 생성 및 유지
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_client())

    # 멀티스레딩 설정
    executor = ThreadPoolExecutor(max_workers=3)
    loop.run_in_executor(executor, main, loop)
    loop.create_task(monitor_and_sell())
    loop.create_task(maintain_client_health())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()