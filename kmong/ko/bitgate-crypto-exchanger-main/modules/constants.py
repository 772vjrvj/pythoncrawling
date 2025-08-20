from typing import List, Optional, TypedDict

from bson.int64 import Int64


class Network(TypedDict):
    name: str
    symbol: str
    emoji: str
    minimumAmountInKRW: Optional[int]
    minimumAmountInCrypto: Optional[float]

class Crypto(TypedDict):
    name: str
    symbol: str
    emoji: str
    networks: List[Network]

SUPPORTED_CRYPTO_CURRENCIES: List[Crypto] = [
    {
        "name": "비트코인",
        "symbol": "BTC",
        "emoji": "<:BTC:1384192333838417941>",
        "networks": [
            {
                "name": "BTC",
                "symbol": "BTC",
                "emoji": "<:BTC:1384192333838417941>",
                "minimumAmountInCrypto": 0.002,
                "minimumAmountInKRW": 327340
            }
        ]
    },
    {
        "name": "이더리움",
        "symbol": "ETH",
        "emoji": "<:ETH:1384192352096358562>",
        "networks": [
            {
                "name": "ETH",
                "symbol": "ETH",
                "emoji": "<:ETH:1384192352096358562>",
                "minimumAmountInCrypto": 0.002,
                "minimumAmountInKRW": 10507
            },
            {
                "name": "BSC",
                "symbol": "ETH",
                "emoji": "<:BNB:1384192398489419908>",
                "minimumAmountInCrypto": 0.002,
                "minimumAmountInKRW": 10507
            }
        ]
    },
    {
        "name": "바이낸스코인",
        "symbol": "BNB",
        "emoji": "<:BNB:1384192398489419908>",
        "networks": [
            {
                "name": "BSC",
                "symbol": "BNB",
                "emoji": "<:BNB:1384192398489419908>",
                "minimumAmountInCrypto": 0.012,
                "minimumAmountInKRW": 13112
            }
        ]
    },
    {
        "name": "라이트코인",
        "symbol": "LTC",
        "emoji": "<:LTC:1384128878552813619>",
        "networks": [
            {
                "name": "LTC",
                "symbol": "LTC",
                "emoji": "<:LTC:1384128878552813619>",
                "minimumAmountInCrypto": 0.0003,
                "minimumAmountInKRW": 45
            }
        ]
    },
    {
        "name": "리플",
        "symbol": "XRP",
        "emoji": "<:XRP:1384192306642550924>",
        "networks": [
            {
                "name": "XRP",
                "symbol": "XRP",
                "emoji": "<:XRP:1384192306642550924>",
                "minimumAmountInCrypto": 0.96,
                "minimumAmountInKRW": 4150
            }
        ]
    },
    {
        "name": "테더",
        "symbol": "USDT",
        "emoji": "<:USDT:1384128943464124527>",
        "networks": [
            {
                "name": "ETH",
                "symbol": "USDT",
                "emoji": "<:ETH:1384192352096358562>",
                "minimumAmountInCrypto": 10.0,
                "minimumAmountInKRW": 13810
            },
            {
                "name": "BSC",
                "symbol": "USDT",
                "emoji": "<:BNB:1384192398489419908>",
                "minimumAmountInCrypto": 10.0,
                "minimumAmountInKRW": 13810
            },
            {
                "name": "TRX",
                "symbol": "USDT",
                "emoji": "<:TRX:1384128912862478356>",
                "minimumAmountInCrypto": 10.0,
                "minimumAmountInKRW": 13810
            },
            {
                "name": "SOL",
                "symbol": "USDT",
                "emoji": "<:SOL:1390583014156668988>",
                "minimumAmountInCrypto": 10.0,
                "minimumAmountInKRW": 13810
            }
        ]
    },
    {
        "name": "트론",
        "symbol": "TRX",
        "emoji": "<:TRX:1384128912862478356>",
        "networks": [
            {
                "name": "TRX",
                "symbol": "TRX",
                "emoji": "<:TRX:1384128912862478356>",
                "minimumAmountInCrypto": 8.9,
                "minimumAmountInKRW": 4012
            }
        ]
    },
    {
        "name": "솔라나",
        "symbol": "SOL",
        "emoji": "<:SOL:1390583014156668988>",
        "networks": [
            {
                "name": "SOL",
                "symbol": "SOL",
                "emoji": "<:SOL:1390583014156668988>",
                "minimumAmountInCrypto": 0.1,
                "minimumAmountInKRW": 24759
            }
        ]
    }
]

# Do not Edit
BANK_CODE_MAPPING = {
    "002": "KDB산업은행",
    "003": "IBK기업은행",
    "004": "KB국민은행",
    "007": "수협은행",
    "011": "NH농협은행",
    "012": "지역농축협",
    "020": "우리은행",
    "023": "SC제일은행",
    "027": "한국씨티은행",
    "031": "대구은행",
    "032": "부산은행",
    "034": "광주은행",
    "035": "제주은행",
    "037": "전북은행",
    "039": "경남은행",
    "045": "새마을금고",
    "048": "신협중앙회",
    "050": "저축은행중앙회",
    "064": "산림조합중앙회",
    "071": "우체국",
    "081": "하나은행",
    "088": "신한은행",
    "089": "케이뱅크",
    "090": "카카오뱅크",
    "092": "토스뱅크",
    "209": "유안타증권",
    "218": "KB증권",
    "230": "미래에셋증권",
    "238": "대신증권",
    "240": "삼성증권",
    "243": "한국투자증권",
    "247": "NH투자증권",
    "261": "교보증권",
    "262": "하이투자증권",
    "263": "현대차증권",
    "264": "키움증권",
    "265": "이베스트투자증권",
    "266": "SK증권",
    "267": "대신증권",
    "269": "한화투자증권",
    "270": "하나증권",
    "278": "신한투자증권",
}

class RankJSON(TypedDict):
    name: str
    discordRoleId: Optional[str]
    minimumKRWChargeRequirement: Int64
    cryptoPurchasingFee: float
    cryptoSellingFee: float

DEFAULT_RANK_OBJECT: RankJSON = {
    "name": "기본",
    "discordRoleId": None,
    "minimumKRWChargeRequirement": Int64(0),
    "cryptoPurchasingFee": 4.0,
    "cryptoSellingFee": 4.0
}

MAX_RESTARTS = 6