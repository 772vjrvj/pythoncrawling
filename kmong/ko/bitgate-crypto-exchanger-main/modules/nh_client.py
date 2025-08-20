import asyncio
import time
import traceback
from typing import List, Literal, Union, overload

import discord
import httpx
from typing_extensions import TypedDict

from modules.utils import generate_uuid_log_id, get_env_config

config = get_env_config()

ERROR_LOG_WEBHOOK = config.error_log_webhook

NH_API_URL = "https://ac.swasd.net/api/v2"

# --- TypedDict 정의 ---

class DateRange(TypedDict):
    start: str  # "YYYY-MM-DD" format
    end: str    # "YYYY-MM-DD" format

class AccountInfo(TypedDict):
    number: str
    bankCode: str

class BankCredentials(TypedDict):
    id: str
    password: str

class BankResponseData(TypedDict):
    taskId: str
    senderName: str
    bank: str
    amount: int
    accountInfo: AccountInfo

class Transaction(TypedDict):
    type: Literal["입금", "출금"]
    name: str
    date: int
    balanceAfterTransaction: int
    amount: int
    id: str

class BankResponseSuccess(TypedDict):
    success: Literal[True]
    message: str
    data: BankResponseData
    newSuspiciousDeposits: List[Transaction]

class BankResponseFailure(TypedDict):
    success: Literal[False]
    message: str

class TaskStatusResponseSuccess(TypedDict):
    success: Literal[True]
    message: str
    transaction: Transaction
    newSuspiciousDeposits: List[Transaction]

class TaskStatusResponseFailure(TypedDict):
    success: Literal[False]
    message: str


class RecentTransactionsData(TypedDict):
    transactions: List[Transaction]
    account: AccountInfo
    range: DateRange
    totalCount: int

class RecentTransactionsResponseSuccess(TypedDict):
    success: Literal[True]
    message: str
    data: RecentTransactionsData

class RecentTransactionsResponseFailure(TypedDict):
    success: Literal[False]
    message: str


# --- NHChargeClient 구현 ---

class NHChargeClient:
    def __init__(self, auth: str):
        self.client: httpx.AsyncClient = httpx.AsyncClient(
            headers={"Authorization": auth}, timeout=40
        )
        self.taskId: str

    # --- requestCharge overloads ---
    @overload
    async def requestCharge(
        self,
        amount: int,
        senderName: str,
        account: AccountInfo,
        bankCredentials: BankCredentials
    ) -> BankResponseSuccess: ...
    @overload
    async def requestCharge(
        self,
        amount: int,
        senderName: str,
        account: AccountInfo,
        bankCredentials: BankCredentials
    ) -> BankResponseFailure: ...

    async def requestCharge(
        self,
        amount: int,
        senderName: str,
        account: AccountInfo,
        bankCredentials: BankCredentials
    ) -> Union[BankResponseSuccess, BankResponseFailure]:
        resp = await self.client.post(
            f"{NH_API_URL}/nonghyup/new",
            json={
                "bank": "NH농협",
                "amount": amount,
                "senderName": senderName,
                "account": account,
                "bankCredentials": bankCredentials,
            },
        )
        result = resp.json()
        if not result.get("success"):
            return BankResponseFailure(
                success=False,
                message=result.get("message", ""),
            )
        self.taskId = result["data"]["taskId"]
        return BankResponseSuccess(
            success=True,
            message=result["message"],
            data=result["data"],
            newSuspiciousDeposits=result.get("newSuspiciousDeposits", []),
        )

    # --- checkStatus overloads ---
    @overload
    async def checkStatus(self, interval: int, timeout: int) -> TaskStatusResponseSuccess: ...
    @overload
    async def checkStatus(self, interval: int, timeout: int) -> TaskStatusResponseFailure: ...

    async def checkStatus(
        self, interval: int, timeout: int
    ) -> Union[TaskStatusResponseSuccess, TaskStatusResponseFailure]:
        from modules.log import send_discord_log
        start = time.time()
        errors = 0
        while True:
            try:
                resp = await self.client.get(
                    f"{NH_API_URL}/nonghyup/tasks/{self.taskId}", timeout=50.0
                )
                result = resp.json()
                errors = 0
                if result.get("success"):
                    return TaskStatusResponseSuccess(
                        success=True,
                        message=result["message"],
                        transaction=result["transaction"],
                        newSuspiciousDeposits=result.get("newSuspiciousDeposits", []),
                    )
            except httpx.TimeoutException:
                pass
            except Exception as error:
                print("NH Client Error:", error)
                tb = traceback.format_exc()
                log_id = generate_uuid_log_id()

                admin_embed = discord.Embed(
                    title="🚨 [RecentTransactionSelect] Unexpected Error",
                    description=f"로그 ID: `{log_id}`",
                    color=0xE74C3C
                )
                admin_embed.add_field(
                    name="Stack Trace",
                    value=f"```\n" + (tb if len(tb) <= 1000 else tb[:1000] + "\n... (truncated)") + "\n```",
                    inline=False
                )

                await send_discord_log(
                    embed=admin_embed,
                    webhook_url=ERROR_LOG_WEBHOOK
                )
                errors += 1
                if errors > 8:
                    return TaskStatusResponseFailure(
                        success=False,
                        message="서버에 오류가 발생했어요.\n-# 문의해주세요.",
                    )
            if time.time() - start > timeout:
                return TaskStatusResponseFailure(
                    success=False,
                    message=f"입금 내역이 확인되지 않았어요. ({timeout})",
                )
            await asyncio.sleep(interval)

    async def deleteTask(self) -> None:
        await self.client.delete(f"{NH_API_URL}/nonghyup/tasks/{self.taskId}")

    # --- fetchRecentTransactions overloads ---
    @overload
    async def fetchRecentTransactions(
        self,
        account: AccountInfo,
        bankCredentials: BankCredentials,
        range: DateRange | None = None
    ) -> RecentTransactionsResponseSuccess: ...
    @overload
    async def fetchRecentTransactions(
        self,
        account: AccountInfo,
        bankCredentials: BankCredentials,
        range: DateRange | None = None
    ) -> RecentTransactionsResponseFailure: ...

    async def fetchRecentTransactions(
        self,
        account: AccountInfo,
        bankCredentials: BankCredentials,
        range: DateRange | None = None
    ) -> Union[RecentTransactionsResponseSuccess, RecentTransactionsResponseFailure]:
        request_data = {
            "account": account,
            "bankCredentials": bankCredentials,
        }
        if range is not None:
            request_data["startDate"] = range
        
        resp = await self.client.post(
            f"{NH_API_URL}/nonghyup/recent-transactions",
            json=request_data,
        )
        result = resp.json()
        if not result.get("success"):
            return RecentTransactionsResponseFailure(
                success=False,
                message=result.get("message", ""),
            )
        return RecentTransactionsResponseSuccess(
            success=True,
            message=result["message"],
            data=result["data"],
        )