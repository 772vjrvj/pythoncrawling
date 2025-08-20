import asyncio
import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

from modules.kebhana import get_usd_price

BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET_KEY: str = os.getenv("BINANCE_API_SECRET_KEY", "")

class BinanceError(Exception):
    """Base class for Binance API errors."""
    def __init__(self, user_msg: str, admin_msg: Optional[str] = None):
        super().__init__(admin_msg or user_msg)
        self.user_msg = user_msg
        self.admin_msg = admin_msg or user_msg

class NetworkError(BinanceError):
    """Raised for network or HTTP client errors."""


class APIError(BinanceError):
    """Raised for Binance API errors (bad symbol, insufficient balance, etc)."""

def _build_signature(secret: str, qs: str) -> str:
    return hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()

class Binance:
    base_url = "https://api.binance.com"
    timeout = httpx.Timeout(10.0, read=20.0)

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or BINANCE_API_KEY
        self.api_secret = api_secret or BINANCE_API_SECRET_KEY
        if not self.api_key or not self.api_secret:
            raise BinanceError(
                user_msg="서버 설정 오류: API 키가 없어요. 관리자에게 문의해주세요.",
                admin_msg="BINANCE_API_KEY 또는 BINANCE_API_SECRET_KEY가 설정되지 않았습니다."
            )
        self.client = client or httpx.AsyncClient(
            timeout=self.timeout,
            headers={"X-MBX-APIKEY": self.api_key}
        )

    async def _request(
        self,
        method: str,
        path: str,
        signed: bool = False,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        params = params or {}
        data = data or {}
        if signed:
            timestamp = await self.get_server_time()
            params["timestamp"] = timestamp
            data["timestamp"] = timestamp
            signature_for_params = _build_signature(self.api_secret, urlencode(params))
            signature_for_data = _build_signature(self.api_secret, urlencode(data))
            params["signature"] = signature_for_params
            data["signature"] = signature_for_data
        url = f"{self.base_url}{path}"
        try:
            # if method == "GET":
            #     resp = await self.client.get(url, params=params)
            # else:
            #     resp = await self.client.post(url, data=data)
            if method == "GET":
                resp = await self.client.get(url, params=params)
            else:
                resp = await self.client.post(url, params=data)
        except httpx.HTTPError as e:
            raise NetworkError(
                user_msg="알 수 없는 오류로 인해 서버와 통신할 수 없어요. 나중에 다시 시도해주세요.",
                admin_msg=str(e)
            )
        try:
            result = resp.json()
        except ValueError:
            raise APIError(
                user_msg="서버 응답이 올바르지 않아요. 관리자에게 문의해주세요.",
                admin_msg=f"Non-JSON response: {resp.text[:200]}"
            )
        # HTTP 상태 코드 또는 API 에러 필드
        if resp.status_code != 200 or (isinstance(result, dict) and result.get('code', 0) != 0):
            code = result.get('code', resp.status_code)
            msg = result.get('msg', resp.text)
            raise APIError(
                user_msg=f"오류가 발생했어요: {msg}",
                admin_msg=json.dumps({"path": path, "params": params, "data": data, "response": result}, ensure_ascii=False)
            )
        return result

    async def get_server_time(self) -> int:
        data = await self._request("GET", "/api/v3/time")
        return int(data.get("serverTime", 0))

    async def get_stock(self) -> Dict[str, Any]:
        data = await self._request("GET", "/api/v3/account", signed=True)
        balances = data.get("balances", [])
        usdt = next((b for b in balances if b.get("asset") == "USDT"), {})
        free = float(usdt.get("free", 0))
        if free <= 0:
            return {"USD": 0.0, "KRW": 0}
        rate = await get_usd_price()
        return {"USD": free, "KRW": int(free * rate)}

    async def get_price(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        if symbol == "USDT":
            rate = await get_usd_price()
            return {"USD": 1.0, "KRW": int(rate)}
        data = await self._request("GET", "/api/v3/ticker/price", params={"symbol": f"{symbol}USDT"})
        price_usd = float(data.get("price", 0))
        rate = await get_usd_price()
        return {"USD": round(price_usd, 6), "KRW": int(price_usd * rate)}

    async def get_withdrawal_info(self, wid: str) -> Dict[str, Any]:
        data = await self._request("GET", "/sapi/v1/capital/withdraw/history", signed=True)
        entry = next((d for d in data if str(d.get("id")) == str(wid)), None)
        if not entry:
            raise APIError("출금 정보를 찾을 수 없어요.")
        return entry

    async def get_withdrawals(self, start_timestamp: Optional[int] = None, end_timestamp: Optional[int] = None) -> Dict[str, Any]:
        """지정된 기간의 모든 출금 내역 조회
        
        Args:
            start_timestamp: 시작 시간 (밀리초 단위 타임스탬프, 선택사항)
            end_timestamp: 종료 시간 (밀리초 단위 타임스탬프, 선택사항)
        
        Returns:
            Dict with structure:
            {
                "success": bool,
                "data": [
                    {
                        "id": str,                    # Withdrawal id in Binance
                        "amount": str,                # withdrawal amount  
                        "transactionFee": str,        # transaction fee
                        "coin": str,                  # coin symbol
                        "status": int,                # 0:Email Sent, 2:Awaiting Approval, 3:Rejected, 4:Processing, 6:Completed
                        "address": str,               # withdrawal address
                        "txId": str,                  # withdrawal transaction id
                        "applyTime": str,             # apply time in "YYYY-MM-DD HH:MM:SS" format (UTC)
                        "network": str,               # network (ETH, BSC, etc.)
                        "transferType": int,          # 1 for internal transfer, 0 for external transfer
                        "withdrawOrderId": str,       # client side id (optional)
                        "info": str,                  # failure reason (if any)
                        "confirmNo": int,             # confirm times for withdraw
                        "walletType": int,            # 1: Funding Wallet, 0: Spot Wallet  
                        "txKey": str,                 # transaction key
                        "completeTime": str,          # complete time when status = 6 (UTC)
                    },
                    ...
                ],
                "error": str (only if success=False)
            }
        """
        try:
            params = {"limit": 1000}
            
            # 날짜 범위가 지정된 경우 파라미터에 추가
            if start_timestamp is not None:
                params["startTime"] = start_timestamp
            if end_timestamp is not None:
                params["endTime"] = end_timestamp
            
            withdrawals = await self._request(
                "GET",
                "/sapi/v1/capital/withdraw/history",
                signed=True,
                params=params
            )
            
            # 바이낸스 API는 직접 배열을 반환함
            if isinstance(withdrawals, list):
                return {"success": True, "data": withdrawals}
            else:
                # 예상과 다른 형식이면 오류 처리
                return {"success": False, "error": f"Unexpected response format: {type(withdrawals)}"}
                
        except APIError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def _apply_withdraw(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = await self._request("POST", "/sapi/v1/capital/withdraw/apply", signed=True, data=params)
        wid = data.get("id")
        for _ in range(5):
            await asyncio.sleep(2)
            try:
                return await self.get_withdrawal_info(wid)
            except APIError:
                continue
        raise APIError("출금 대기 중 오류가 발생했어요.")

    async def send_usdt(self, amount_krw: int, address: str, network: str = "BSC") -> Dict[str, Any]:
        rate = await get_usd_price()
        usdt_amt = round(amount_krw / rate, 6)
        if usdt_amt < 10:
            raise APIError("10 USDT 이하 금액은 송금할 수 없어요.")
        return await self._apply_withdraw({"coin": "USDT", "address": address, "amount": f"{usdt_amt:.6f}", "network": network})

    async def send_coin(
        self,
        amount_krw: int,
        address: str,
        coin: str,
        network: str,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        rate = await get_usd_price()
        usd_amt = amount_krw / rate
        order = await self._request(
            "POST",
            "/api/v3/order",
            signed=True,
            data={"symbol": f"{coin.upper()}USDT", "side": "BUY", "type": "MARKET", "quoteOrderQty": f"{usd_amt:.6f}"},
        )
        fills = order.get("fills", [])
        coin_qty = sum(float(f.get("qty", 0)) - float(f.get("commission", 0)) for f in fills)
        await asyncio.sleep(1.5)
        params: Dict[str, Any] = {"coin": coin.upper(), "address": address, "amount": f"{coin_qty:.6f}", "network": network}
        if coin.upper() == "XRP" and tag:
            params["addressTag"] = tag
        return await self._apply_withdraw(params)

    async def get_pnl_by_date_range(self, start_timestamp: int, end_timestamp: int) -> Dict[str, Any]:
        """지정된 기간의 PNL 정보 조회 (입출금, 컨버트만 포함)"""
        try:
            total_deposits = 0.0  # 입금액 (USDT 기준)
            total_withdrawals = 0.0  # 출금액 (USDT 기준)
            total_convert_fees = 0.0  # 컨버트 수수료
            
            # 1. 입금 내역 조회 (소유자가 외부에서 구매한 코인들)
            try:
                deposits = await self._request(
                    "GET",
                    "/sapi/v1/capital/deposit/hisrec",
                    signed=True,
                    params={
                        "startTime": start_timestamp,
                        "endTime": end_timestamp,
                        "limit": 1000
                    }
                )
                
                for deposit in deposits:
                    if deposit.get('status') == 1:  # 성공한 입금만
                        amount = float(deposit.get('amount', 0))
                        coin = deposit.get('coin', '')
                        
                        # USDT로 변환 (간단하게 처리)
                        if coin == 'USDT':
                            total_deposits += amount
                        elif coin in ['BUSD', 'USDC']:
                            total_deposits += amount  # 스테이블코인은 1:1
                        # 다른 코인들은 입금 당시 가격으로 변환해야 하지만 간단히 현재 가격 사용
                        else:
                            try:
                                price_info = await self.get_price(coin)
                                total_deposits += amount * price_info['USD']
                            except:
                                pass  # 가격 조회 실패시 스킵
                        
            except APIError:
                pass  # 입금 내역이 없거나 권한 없음
            
            # 2. 출금 내역 조회 (사용자에게 전송한 코인들)
            try:
                withdrawals = await self._request(
                    "GET",
                    "/sapi/v1/capital/withdraw/history",
                    signed=True,
                    params={
                        "startTime": start_timestamp,
                        "endTime": end_timestamp,
                        "limit": 1000
                    }
                )
                
                for withdrawal in withdrawals:
                    if withdrawal.get('status') == 6:  # 성공한 출금만
                        amount = float(withdrawal.get('amount', 0))
                        transaction_fee = float(withdrawal.get('transactionFee', 0))
                        coin = withdrawal.get('coin', '')
                        
                        # USDT로 변환 (출금 당시 가격)
                        if coin == 'USDT':
                            total_withdrawals += (amount + transaction_fee)
                        elif coin in ['BUSD', 'USDC']:
                            total_withdrawals += (amount + transaction_fee)
                        else:
                            try:
                                price_info = await self.get_price(coin)
                                total_withdrawals += (amount + transaction_fee) * price_info['USD']
                            except:
                                pass  # 가격 조회 실패시 스킵
                            
            except APIError:
                pass  # 출금 내역이 없거나 권한 없음
            
            # 3. 컨버트 내역 조회 (USDT → 다른 코인 변환 수수료)
            try:
                convert_history = await self._request(
                    "GET",
                    "/sapi/v1/convert/tradeFlow",
                    signed=True,
                    params={
                        "startTime": start_timestamp,
                        "endTime": end_timestamp,
                        "limit": 1000
                    }
                )
                
                for convert in convert_history.get('list', []):
                    # 컨버트 수수료 계산
                    fee = float(convert.get('fee', 0))
                    fee_asset = convert.get('feeAsset', '')
                    
                    if fee_asset == 'USDT':
                        total_convert_fees += fee
                    elif fee_asset in ['BUSD', 'USDC']:
                        total_convert_fees += fee
                    else:
                        try:
                            price_info = await self.get_price(fee_asset)
                            total_convert_fees += fee * price_info['USD']
                        except:
                            pass
                        
            except APIError:
                pass  # 컨버트 내역이 없거나 권한 없음
            
            # 4. 현재 포트폴리오 가치 조회 (USDT 기준)
            try:
                account_info = await self._request("GET", "/api/v3/account", signed=True)
                current_portfolio_value = 0.0
                
                for balance in account_info.get('balances', []):
                    asset = balance.get('asset', '')
                    free = float(balance.get('free', 0))
                    locked = float(balance.get('locked', 0))
                    total_balance = free + locked
                    
                    if total_balance > 0:
                        if asset == 'USDT':
                            current_portfolio_value += total_balance
                        elif asset in ['BUSD', 'USDC']:
                            current_portfolio_value += total_balance
                        else:
                            # 다른 자산들의 USDT 가치 계산
                            try:
                                price_info = await self.get_price(asset)
                                current_portfolio_value += total_balance * price_info['USD']
                            except:
                                pass  # 가격 조회 실패시 스킵
                                
            except APIError:
                current_portfolio_value = 0.0
            
            # 5. PNL 계산
            # PNL = 현재 포트폴리오 가치 + 총 출금액 - 총 입금액 - 컨버트 수수료
            net_pnl = current_portfolio_value + total_withdrawals - total_deposits - total_convert_fees
            
            # USD to KRW 변환
            usd_rate = await get_usd_price()
            
            return {
                'total_pnl_usd': round(net_pnl, 6),
                'total_pnl_krw': int(net_pnl * usd_rate),
                'total_convert_fees_usd': round(total_convert_fees, 6),
                'total_convert_fees_krw': int(total_convert_fees * usd_rate),
                'total_deposits_usd': round(total_deposits, 6),
                'total_deposits_krw': int(total_deposits * usd_rate),
                'total_withdrawals_usd': round(total_withdrawals, 6),
                'total_withdrawals_krw': int(total_withdrawals * usd_rate),
                'current_portfolio_usd': round(current_portfolio_value, 6),
                'current_portfolio_krw': int(current_portfolio_value * usd_rate),
                'trade_count': 0,  # 현물 거래 없음
                'futures_trades': 0,
                'spot_trades': 0
            }

        except APIError as e:
            return {
                'total_pnl_usd': 0.0,
                'total_pnl_krw': 0,
                'total_convert_fees_usd': 0.0,
                'total_convert_fees_krw': 0,
                'total_deposits_usd': 0.0,
                'total_deposits_krw': 0,
                'total_withdrawals_usd': 0.0,
                'total_withdrawals_krw': 0,
                'current_portfolio_usd': 0.0,
                'current_portfolio_krw': 0,
                'trade_count': 0,
                'futures_trades': 0,
                'spot_trades': 0,
                'error': str(e)
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()