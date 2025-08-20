import datetime
from typing import Literal, Union, overload

import httpx
from typing_extensions import TypedDict

from models.User import VerificationData

IDENTIFICATI0N_API_URL = "https://api.identificati0n.com/v1"

# --- 1) 공통: verificationContext 타입 정의 ---

class VerificationContextRequest(TypedDict):
    mobileCarrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]
    identificationType: Literal["SMS"]
    name: str
    phone: str
    birthdate: str      # ISO8601 e.g. "2010-09-07T00:00:00.000Z"
    gender: Literal["MAN", "WOMAN"]
    isForeigner: bool

# --- 2) /request 응답용 TypedDict ---

class SendRequestResponseSuccess(TypedDict):
    success: Literal[True]
    message: str
    expirationTime: int
    taskId: str
    verificationContext: VerificationContextRequest
    identifierAlias: str

class SendRequestResponseFailure(TypedDict):
    success: Literal[False]
    message: str

# --- 3) /verify 응답용 TypedDict ---

class VerifyResponseSuccess(TypedDict):
    success: Literal[True]
    message: str
    verificationData: VerificationData
    verificationContext: VerificationContextRequest
    identifierAlias: str
    userCi: str

class VerifyResponseFailure(TypedDict):
    success: Literal[False]
    message: str


# --- 4) Verify 클래스 구현 with overloads ---

class Verify:
    def __init__(self, api_key: str):
        self.client = httpx.AsyncClient(
            headers={"Authorization": api_key}, timeout=10
        )
        self.taskId: str

    # --- sendRequest overloads ---
    @overload
    async def sendRequest(
        self,
        name: str,
        birthdate: str,
        phone: str,
        carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"],
        userId: int
    ) -> SendRequestResponseSuccess: ...
    @overload
    async def sendRequest(
        self,
        name: str,
        birthdate: str,
        phone: str,
        carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"],
        userId: int
    ) -> SendRequestResponseFailure: ...

    async def sendRequest(
        self,
        name: str,
        birthdate: str,
        phone: str,
        carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"],
        userId: int
    ) -> Union[SendRequestResponseSuccess, SendRequestResponseFailure]:
        resp = await self.client.post(
            f"{IDENTIFICATI0N_API_URL}/NICE4/request",
            json={
                "identificationType": "SMS",
                "name": name,
                "birthdate": birthdate[:6],
                "gender": birthdate[6:7],
                "phone": phone,
                "carrier": carrier,
                "identifierAlias": str(userId),
            },
        )
        j = resp.json()
        if not j.get("success", False):
            return SendRequestResponseFailure(success=False, message=j.get("message", ""))
        # 성공 케이스
        self.taskId = j["taskId"]
        return SendRequestResponseSuccess(
            success=True,
            message=j["message"],
            expirationTime=j["expirationTime"],
            taskId=j["taskId"],
            verificationContext=j["verificationContext"],
            identifierAlias=j["identifierAlias"],
        )

    # --- verify overloads ---
    @overload
    async def verify(
        self, otp: str
    ) -> VerifyResponseSuccess: ...
    @overload
    async def verify(
        self, otp: str
    ) -> VerifyResponseFailure: ...

    async def verify(self, otp: str) -> Union[VerifyResponseSuccess, VerifyResponseFailure]:
        resp = await self.client.post(
            f"{IDENTIFICATI0N_API_URL}/verify",
            json={"smsCode": otp, "taskId": self.taskId},
        )
        j = resp.json()
        if not j.get("success", False):
            return VerifyResponseFailure(success=False, message=j.get("message", ""))
        # 성공 케이스: VerificationData 모델로 매핑
        ctx = j["verificationContext"]
        verificationData = VerificationData(
            phone=ctx["phone"],
            name=ctx["name"],
            birthdate=datetime.datetime.fromisoformat(ctx["birthdate"]),
            gender=ctx["gender"],
            carrier=ctx["mobileCarrier"],
            ci=j["userCi"],
        )
        return VerifyResponseSuccess(
            success=True,
            message=j["message"],
            verificationContext=ctx,
            verificationData=verificationData,
            identifierAlias=j["identifierAlias"],
            userCi=j["userCi"],
        )
