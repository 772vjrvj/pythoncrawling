from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from beanie import Document, Link
from bson.int64 import Int64

from models.User import User


class KRWChargeLog(Document):
    state: Literal["PENDING", "COMPLETED", "FAILED"]
    txid: Optional[str] = None
    amount: Int64
    user: Link[User]
    senderName: str
    depositTime: Optional[Int64] = None
    createdAt: datetime

    model_config = {"arbitrary_types_allowed": True}
