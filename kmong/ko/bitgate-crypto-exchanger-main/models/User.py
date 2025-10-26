from __future__ import annotations

from datetime import datetime
from typing import Annotated, List, Literal, Optional

from beanie import Document, Indexed, Link
from bson.int64 import Int64
from pydantic import BaseModel, Field

class VerificationData(BaseModel):
    phone: str
    name: str
    birthdate: datetime
    gender: Literal["MAN", "WOMAN"]
    carrier: str
    ci: Annotated[
        str,
        Indexed()
    ]

    model_config = {"arbitrary_types_allowed": True}

class Limit(BaseModel):
    dailyChargeLimit: Int64
    dailySellingLimit: Int64

    model_config = {"arbitrary_types_allowed": True}

class Balance(BaseModel):
    KRW: Int64

    model_config = {"arbitrary_types_allowed": True}

class Statistics(BaseModel):
    totalKRWCharge: Int64

    model_config = {"arbitrary_types_allowed": True}

class CryptoAddress(BaseModel):
    crypto: str
    network: str
    address: str
    tag: str = ""
    alias: str
    isShuffleAddress: bool

    model_config = {"arbitrary_types_allowed": True}

class CryptoWallet(BaseModel):
    crypto: str
    network: str
    publicKey: str
    mnemonic: str

class KRWAccount(BaseModel):
    accountNumber: str
    bankCode: str
    alias: str

    model_config = {"arbitrary_types_allowed": True}

class User(Document):
    discordId: Annotated[
        str,
        Indexed(unique=True)
    ]
    
    verificationData: Optional[VerificationData] = None
    
    balances: Balance
    statistics: Statistics
    limits: Limit

    cryptoAddresses: List[CryptoAddress] = Field(default_factory=list)
    sellingWallets: List[CryptoWallet] = Field(default_factory=list)
    krwAccounts: List[KRWAccount] = Field(default_factory=list)

    invitedBy: Optional[Link["User"]] = None
    referralCode: Annotated[
        str,
        Indexed()
    ]

    bypassAdultVerification: Optional[bool] = False

    class Settings:
        name = "user"
        indexes = [
            "discordId",
            [("verificationData.ci", 1)],
            "referralCode"
        ]

    model_config = {"arbitrary_types_allowed": True}

class FetchedUser(User):
    invitedBy: Optional[User] = None

User.model_rebuild()