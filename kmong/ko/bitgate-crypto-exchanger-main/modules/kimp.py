from modules.binance import Binance
from modules.kebhana import get_usd_price

KIMP_STANDARD_SYMBOL = "BTC"

async def get_kimp() -> float:
    binance = Binance()
    # 바이낸스 가격
    binance_price = await binance._request("GET", "/api/v3/ticker/price", params={"symbol": f"{KIMP_STANDARD_SYMBOL}USDT"})
    # 업비트 가격
    try:
        upbit_response = await binance.client.get("https://api.upbit.com/v1/ticker", params={"markets": f"KRW-{KIMP_STANDARD_SYMBOL}"})
        upbit_data = upbit_response.json()[0]
        upbit_price = float(upbit_data.get("trade_price", 0))
    except Exception as e:
        raise RuntimeError(f"업비트 가격 조회 실패: {e}")
    price_bin = float(binance_price.get("price", 0))
    rate = await get_usd_price()
    premium = ((upbit_price / (price_bin * rate)) - 1) * 100
    return round(premium, 2)