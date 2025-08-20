from __future__ import annotations

import datetime

from beanie import Document, Link
from bson.int64 import Int64

from models.User import User


class CryptoTransaction(Document):
    binanceWithdrawalId: str
    cryptoSymbol: str
    networkName: str
    address: str
    tag: str = ""
    amountKRW: Int64
    amountCrypto: float
    user: Link[User]
    revenue: Int64
    createdAt: datetime.datetime

    model_config = {"arbitrary_types_allowed": True}