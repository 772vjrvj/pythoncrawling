from typing import Annotated, Optional

from beanie import Document, Indexed
from bson.int64 import Int64


class Rank(Document):
    name: str
    discordRoleId: Annotated[
        Optional[str],
        Indexed(unique=True, sparse=True)
    ] = None
    minimumKRWChargeRequirement: Int64
    cryptoPurchasingFee: float
    cryptoSellingFee: float

    class Settings:
        name = "rank"

    model_config = {"arbitrary_types_allowed": True}

Rank.model_rebuild()