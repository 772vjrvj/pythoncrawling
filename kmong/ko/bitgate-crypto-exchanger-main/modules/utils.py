import datetime
import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from typing import List, Union

import dotenv

from modules.constants import (BANK_CODE_MAPPING, SUPPORTED_CRYPTO_CURRENCIES,
                               Crypto, Network)

dotenv.load_dotenv()

EnvValue = Union[int, float, bool, str]
EnvConfig = Union[EnvValue, List[EnvValue]]

def parse_date(date_str: str) -> datetime.datetime:
    """다양한 날짜 형식을 지원하는 파싱 함수 (년도 필수)"""
    if not date_str:
        raise ValueError("날짜가 입력되지 않았습니다")
    
    # 지원하는 날짜 형식들 (년도 포함만)
    formats = [
        "%Y%m%d",      # 20250807
        "%Y-%m-%d",    # 2025-08-07
        "%Y.%m.%d",    # 2025.08.07
        "%Y/%m/%d",    # 2025/08/07
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # 모든 형식이 실패하면 ValueError 발생
    raise ValueError(f"지원하지 않는 날짜 형식: {date_str}")

def parse_date_to_string(date_str: str) -> str:
    """날짜를 YYYY-MM-DD 형식 문자열로 파싱"""
    return parse_date(date_str).strftime("%Y-%m-%d")

def parse_binance_apply_time(withdrawal):
    """바이낸스 출금의 applyTime을 UTC 타임스탬프로 변환"""
    apply_time = withdrawal.get("applyTime", "")
    if not apply_time:
        return 0
    try:
        # "YYYY-MM-DD HH:MM:SS" 형식을 UTC 타임스탬프로 변환
        dt = datetime.datetime.strptime(apply_time, "%Y-%m-%d %H:%M:%S")
        # UTC 시간으로 처리
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return 0

def format_utc_time_to_kst(utc_time_str: str) -> str:
    """바이낸스 UTC 시간을 한국 시간으로 변환하여 표시용 문자열 반환"""
    if not utc_time_str:
        return "N/A"
    try:
        # UTC 시간으로 파싱
        utc_dt = datetime.datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
        utc_dt = utc_dt.replace(tzinfo=datetime.timezone.utc)
        # 한국 시간으로 변환 (UTC+9)
        kst_dt = utc_dt.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
        return kst_dt.strftime("%Y-%m-%d %H:%M:%S KST")
    except (ValueError, TypeError):
        return utc_time_str

def is_successful_withdrawal(withdrawal) -> bool:
    """바이낸스 출금이 성공했는지 확인
    
    Binance Withdrawal Status:
    - 0: Email Sent
    - 1: Cancelled 
    - 2: Awaiting Approval
    - 3: Rejected
    - 4: Processing
    - 5: Failure
    - 6: Completed (성공)
    
    참고: status=6이면서 info에 메시지가 있는 경우 경고성 정보로 표시
    """
    status = withdrawal.get("status", 0)
    return status == 6

def get_network_by_name(crypto: Crypto, network_name: str) -> Network:
    for network in crypto["networks"]:
        if network["name"].upper() == network_name.upper():
            return network
    return crypto["networks"][0]


def get_bankcode_by_bankname(bankname: str, fuzzy: bool = True):
    for code, name in BANK_CODE_MAPPING.items():
        if name == bankname:
            return code
    
    if not fuzzy:
        return None
    
    bankname_clean = bankname.strip().upper()
    
    aliases = {
        "토스": ["토스뱅크"],
        "토뱅": ["토스뱅크"],
        "카카오": ["카카오뱅크"],
        "카뱅": ["카카오뱅크"],
        "케이": ["케이뱅크"],
        "케뱅": ["케이뱅크"],
        "국민": ["KB국민은행"],
        "신한": ["신한은행"],
        "하나": ["하나은행"],
        "우리": ["우리은행"],
        "농협": ["NH농협은행"],
        "기업": ["IBK기업은행"],
        "산업": ["KDB산업은행"],
        "수협": ["수협은행"],
        "씨티": ["한국씨티은행"],
        "SC": ["SC제일은행"],
        "우체국": ["우체국"],
        "새마을": ["새마을금고"],
        "신협": ["신협중앙회"],
        "저축": ["저축은행중앙회"],
        "산림": ["산림조합중앙회"],
        "대구": ["대구은행"],
        "부산": ["부산은행"],
        "광주": ["광주은행"],
        "제주": ["제주은행"],
        "전북": ["전북은행"],
        "경남": ["경남은행"],
    }
    
    for alias, full_names in aliases.items():
        if alias in bankname_clean or bankname_clean in alias:
            for full_name in full_names:
                for code, name in BANK_CODE_MAPPING.items():
                    if name == full_name:
                        return code
    
    pattern = re.compile(re.escape(bankname), re.IGNORECASE)
    for code, name in BANK_CODE_MAPPING.items():
        if pattern.search(name):
            return code
    
    for code, name in BANK_CODE_MAPPING.items():
        clean_name = re.sub(r'[은행|뱅크|금고|조합|회|증권]', '', name)
        if clean_name and clean_name in bankname:
            return code
    
    return None

def get_crypto_by_symbol(symbol: str) -> Crypto:
    for crypto in SUPPORTED_CRYPTO_CURRENCIES:
        if crypto["symbol"].upper() == symbol.upper():
            return crypto
    return SUPPORTED_CRYPTO_CURRENCIES[0]

def get_bankname_by_bankcode(bankCode):
    bankname = BANK_CODE_MAPPING.get(str(bankCode))
    if not bankname:
        raise Exception("Not Valid bankCode.")

def generate_uuid_log_id() -> str:
    return uuid.uuid4().hex

def generate_referral_code(user_id: str) -> str:
    return hashlib.sha256(user_id.encode() + uuid.uuid4().hex.encode()).hexdigest()[:12].upper()

def _parse_value(raw: str) -> EnvValue:
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    if raw.isdigit():
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return raw

_WEBHOOK_PATTERN = re.compile(
    r"^https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]+$"
)
_MONGODB_URI_PATTERN = re.compile(r"^mongodb(?:\+srv)?:\/\/\S+$")


@dataclass(frozen=True)
class Config:
    brand_name: str
    owner_discord_ids: List[int]
    command_supported_guild_ids: List[int]
    token: str
    auto_charge_api_key: str
    id_verification_api_key: str
    binance_api_key: str
    binance_api_secret_key: str
    nh_login_id: str
    nh_login_pw: str
    charge_bank_code: str
    charge_bank_number: str
    charge_interval: int
    register_log_webhook: str
    charge_log_webhook: str
    buy_log_webhook: str
    referral_log_webhook: str
    error_log_webhook: str
    suspicious_deposit_log_webhook: str
    referral_payback_percent: int
    default_daily_charge_limit: int
    default_daily_selling_limit: int
    mongodb_uri: str
    database_name: str
    minimum_crypto_purchase_krw_amount: int
    vending_main_container_channel_id: int
    vending_main_container_message_id: int


def get_env_config() -> Config:
    def _require(key: str) -> str:
        val = os.getenv(key)
        if val is None or val == "":
            raise KeyError(f"Environment variable '{key}' is required but not set.")
        return val

    brand_name = _require("BRAND_NAME")
    token = _require("TOKEN")
    auto_charge_api_key = _require("AUTO_CHARGE_API_KEY")
    identify_api_key = _require("IDENTIFY_API_KEY")
    binance_api_key = _require("BINANCE_API_KEY")
    binance_api_secret_key = _require("BINANCE_API_SECRET_KEY")
    nh_login_id = _require("NH_LOGIN_ID")
    nh_login_pw = _require("NH_LOGIN_PW")
    charge_bank_code = _require("CHARGE_BANK_CODE")
    charge_bank_number = _require("CHARGE_BANK_NUMBER")
    database_name = _require("DATABASE_NAME")

    owner_discord_ids = [
        int(x) for x in _require("OWNER_DISCORD_IDS").split(",") if x.strip()
    ]
    command_supported_guild_ids = [
        int(x) for x in _require("COMMAND_SUPPORTED_GUILD_IDS").split(",") if x.strip()
    ]

    charge_interval = int(_require("CHARGE_INTERVAL"))
    referral_payback_percent = int(_require("REFERRAL_PAYBACK_PERCENT"))
    default_daily_charge_limit = int(_require("DEFAULT_DAILY_CHARGE_LIMIT"))
    default_daily_selling_limit = int(_require("DEFAULT_DAILY_SELLING_LIMIT"))
    minimum_crypto_purchase_krw_amount = int(_require("MINIMUM_CRYPTO_PURCHASE_KRW_AMOUNT"))
    vending_main_container_channel_id = int(_require("VENDING_MAIN_CONTAINER_CHANNEL_ID"))
    vending_main_container_message_id = int(_require("VENDING_MAIN_CONTAINER_MESSAGE_ID"))

    register_log_webhook = _require("REGISTER_LOG_WEBHOOK")
    if not _WEBHOOK_PATTERN.match(register_log_webhook):
        raise ValueError(f"Invalid Discord webhook URL: {register_log_webhook}")
    charge_log_webhook = _require("CHARGE_LOG_WEBHOOK")
    if not _WEBHOOK_PATTERN.match(charge_log_webhook):
        raise ValueError(f"Invalid Discord webhook URL: {charge_log_webhook}")
    buy_log_webhook = _require("BUY_LOG_WEBHOOK")
    if not _WEBHOOK_PATTERN.match(buy_log_webhook):
        raise ValueError(f"Invalid Discord webhook URL: {buy_log_webhook}")
    referral_log_webhook = _require("REFERRAL_LOG_WEBHOOK")
    if not _WEBHOOK_PATTERN.match(referral_log_webhook):
        raise ValueError(f"Invalid Discord webhook URL: {referral_log_webhook}")
    error_log_webhook = _require("ERROR_LOG_WEBHOOK")
    if not _WEBHOOK_PATTERN.match(error_log_webhook):
        raise ValueError(f"Invalid Discord webhook URL: {error_log_webhook}")
    suspicious_deposit_log_webhook = _require("SUSPICIOUS_DEPOSIT_LOG_WEBHOOK")
    if not _WEBHOOK_PATTERN.match(suspicious_deposit_log_webhook):
        raise ValueError(f"Invalid Discord webhook URL: {suspicious_deposit_log_webhook}")
    
    mongodb_uri = _require("MONGODB_URI")
    if not _MONGODB_URI_PATTERN.match(mongodb_uri):
        raise ValueError(f"Invalid MongoDB URI: {mongodb_uri}")

    return Config(
        brand_name=brand_name,
        owner_discord_ids=owner_discord_ids,
        command_supported_guild_ids=command_supported_guild_ids,
        token=token,
        auto_charge_api_key=auto_charge_api_key,
        id_verification_api_key=identify_api_key,
        binance_api_key=binance_api_key,
        binance_api_secret_key=binance_api_secret_key,
        nh_login_id=nh_login_id,
        nh_login_pw=nh_login_pw,
        charge_bank_code=charge_bank_code,
        charge_bank_number=charge_bank_number,
        charge_interval=charge_interval,
        register_log_webhook=register_log_webhook,
        charge_log_webhook=charge_log_webhook,
        buy_log_webhook=buy_log_webhook,
        referral_log_webhook=referral_log_webhook,
        error_log_webhook=error_log_webhook,
        suspicious_deposit_log_webhook=suspicious_deposit_log_webhook,
        referral_payback_percent=referral_payback_percent,
        default_daily_charge_limit=default_daily_charge_limit,
        default_daily_selling_limit=default_daily_selling_limit,
        mongodb_uri=mongodb_uri,
        database_name=database_name,
        minimum_crypto_purchase_krw_amount=minimum_crypto_purchase_krw_amount,
        vending_main_container_channel_id=vending_main_container_channel_id,
        vending_main_container_message_id=vending_main_container_message_id,
    )