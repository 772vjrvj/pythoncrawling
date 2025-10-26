import asyncio
import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

import httpx
import json

DEFAULT_USD_PRICE: float = 1390.0

usd_price = DEFAULT_USD_PRICE
last_usd_price_update = 0

def parse_decimal(s: str) -> Decimal:
    try:
        return Decimal(s.replace(",", "").strip())
    except (AttributeError, InvalidOperation):
        raise ValueError(f"숫자 파싱 실패: {s!r}")

async def fetch_price_from_naver(
    amount: str,
    from_code: str,
    to_code: str,
    *,
    retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: float = 10.0,
    client: Optional[httpx.AsyncClient] = None,
) -> Decimal:
    """
    비동기식으로 네이버 환율 렌더러에서 환율을 가져와 amount를 변환.
    amount: "100" 또는 "1,000.50" 같은 문자열.
    from_code: 예: "USD"
    to_code: 예: "KRW"
    반환: Decimal로 변환된 금액 (소수 둘째 자리 반올림)
    """

    url = "https://m.search.naver.com/p/csearch/content/qapirender.nhn"
    params = {
        "key": "calculator",
        "pkid": "141",
        "q": "환율",
        "where": "m",
        "u1": "keb",
        "u6": "standardUnit",
        "u7": "0",
        "u3": from_code,
        "u4": to_code,
        "u8": "down",
        "u2": "1",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Python async script)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    owns_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout)
        owns_client = True

    last_exc = None
    try:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                countries = data.get("country", [])
                if len(countries) < 2:
                    raise RuntimeError(f"환율 정보 부족: {countries!r}")
                base = countries[0]
                target = countries[1]

                base_val = parse_decimal(base["value"])
                target_val = parse_decimal(target["value"])

                if base_val == 0:
                    raise ZeroDivisionError("기준 통화 값이 0입니다.")

                rate = target_val / base_val  # 1 from_code = rate of to_code
                amt = parse_decimal(amount)
                converted = (amt * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return converted

            except (httpx.HTTPError, ValueError, KeyError, IndexError, ZeroDivisionError, RuntimeError) as e:
                last_exc = e
                if attempt == retries:
                    raise e
            
                await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
        
        raise RuntimeError(f"환율 조회/변환 실패: {last_exc}")
    
    finally:
        if owns_client:
            await client.aclose()

async def fetch_price_from_kebhana(
    currencyCode: str,
    *,
    retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: float = 10.0,
    client: Optional[httpx.AsyncClient] = None,
) -> Decimal:
    url = "https://mbp.hanabank.com/BFXD/BFXD02/BFXD020100101.do"
    payload = {
        "strDt": datetime.datetime.now().strftime("%Y-%m-%d")
    }

    async with httpx.AsyncClient(
        headers={
            "User-Agent": '{"platform":"Android","brand":"samsung","model":"SM-S523N","version":"23","deviceId":"","phoneNumber":"","countryIso":"","telecom":"","simSerialNumber":"","subscriberId":"","appVersion":"","phoneName":"","appName":"","deviceWidth":,"deviceHeight":,"uid":"","hUid":"","terminalInfoId":"","etcStr":"","userAgent":""}'
        }
    ) as client:
        for attempt in range(1, retries + 1):
            try:
                response = await client.post(url, data=payload)
                responseJSON = response.json()

                data = responseJSON["data"]["contMsg1"]

                price = 0
                for entry in data:
                    if entry.get("curCd") == currencyCode:
                        price = entry.get("dealBascRt")

                if price == 0:
                    raise ZeroDivisionError("기준 통화 값이 0입니다.")

                price = Decimal(price)
                return price

            except (httpx.HTTPError, ValueError, KeyError, IndexError, ZeroDivisionError, RuntimeError) as e:
                last_exc = e
                if attempt == retries:
                    raise e
                
                await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
        
        raise RuntimeError(f"환율 조회 실패")

async def get_usd_price() -> float:
    global usd_price, last_usd_price_update
    try:
        if usd_price and (datetime.datetime.now().timestamp() - last_usd_price_update < 3600):
            return usd_price
        #usd_price = float(await fetch_price_from_naver("1", "USD", "KRW"))
        usd_price = float(await fetch_price_from_kebhana("USD"))

        if usd_price <= 0:
            raise ValueError("환율이 0 이하입니다. API 응답을 확인해주세요.")
        last_usd_price_update = datetime.datetime.now().timestamp()
        return usd_price
    except Exception as e:
        # raise NetworkError(
        #     user_msg="알 수 없는 오류로 인해 환율 정보를 가져오지 못했어요. 나중에 다시 시도해주세요.",
        #     admin_msg=str(e)
        # )
        print(f"Error fetching USD price: {e}")
        return usd_price # Fallback to default if API fails