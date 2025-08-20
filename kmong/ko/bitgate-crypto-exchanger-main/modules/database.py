import datetime
from decimal import ROUND_DOWN, Decimal
from operator import attrgetter
from typing import List, Optional

from beanie import Link, init_beanie
from beanie.odm.enums import SortDirection
from beanie.odm.operators.update.array import Push
from beanie.odm.operators.update.general import Inc, Set
from beanie.odm.queries.update import UpdateResponse
from bson import DBRef
from bson.int64 import Int64
from motor.motor_asyncio import AsyncIOMotorClient

from models.CryptoTransaction import CryptoTransaction
from models.KRWChargeLog import KRWChargeLog
from models.Rank import Rank
from models.User import (Balance, CryptoAddress, FetchedUser, KRWAccount,
                         Limit, Statistics, User, VerificationData)
from modules.constants import DEFAULT_RANK_OBJECT
from modules.utils import generate_referral_code, get_env_config

config = get_env_config()

DEFAULT_DAILY_CHARGE_LIMIT = config.default_daily_charge_limit
DEFAULT_DAILY_SELLING_LIMIT = config.default_daily_selling_limit
REFERRAL_PAYBACK_PERCENT = config.referral_payback_percent
DATABASE_NAME = config.database_name

class Database:
    @staticmethod
    async def init_db(mongo_uri: str) -> None:
        client = AsyncIOMotorClient(mongo_uri)
        db = client[DATABASE_NAME]
        await init_beanie(
            database=db,
            document_models=[Rank, User, CryptoTransaction, KRWChargeLog],
        )

    @staticmethod
    async def get_user_info(discord_id: str, forced: bool = False) -> Optional[FetchedUser]:
        """discord_id 로 User + rank 조회. verification 이 없으면 None 리턴."""
        user: Optional[User] = await User.find_one(User.discordId == discord_id)
        if not user or not user.verificationData:
            if not forced:
                return None

        if user:
            await user.fetch_all_links()

        fetched_user: FetchedUser | None = user # type: ignore[arg-type]

        return fetched_user

    @staticmethod
    async def register_user(
        discord_id: str,
        verificationData: Optional[VerificationData] = None,
        invitedBy: Optional[User] = None,
    ) -> User:
        """새로운 유저 등록 (이미 존재/중복 CI 체크 포함)"""

        # 같은 CI로 이미 가입된 계정이 있는지 확인
        if verificationData:
            other = await User.find_one(
                User.verificationData.ci == verificationData.ci  # type: ignore[arg-type]
            )
            if other:
                raise ValueError(f"<@{discord_id}>(`{discord_id}`)님의 가입 시도: <@{other.discordId}>(`{other.discordId}`) 계정에서 CI `{verificationData.ci}` 로 이미 가입된 계정이 있습니다.")

        # 동일 Discord ID 존재하면 verificationData 만 갱신
        existing = await Database.get_user_info(discord_id, True)
        if existing:
            existing.verificationData = verificationData
            await existing.save()
            return existing

        user_ref = DBRef(collection=User.get_collection_name(), id=invitedBy.id) if invitedBy else None
        link_to_invited_user = Link(user_ref, User) if user_ref else None

        user = User(
            discordId=discord_id,
            verificationData=verificationData,
            balances=Balance(KRW=Int64(0)),
            cryptoAddresses=[],
            krwAccounts=[],
            statistics=Statistics(totalKRWCharge=Int64(0)),
            invitedBy=link_to_invited_user,
            referralCode=generate_referral_code(discord_id),
            limits=Limit(
                dailyChargeLimit=Int64(DEFAULT_DAILY_CHARGE_LIMIT),
                dailySellingLimit=Int64(DEFAULT_DAILY_SELLING_LIMIT),
            ),
        )
        await user.insert()

        return user

    @staticmethod
    async def get_user_rank(discord_id: str) -> Rank:
        user = await User.find_one(User.discordId == discord_id)
        if not user:
            raise LookupError("User not found")

        eligible_ranks: list[Rank] = await Rank.find(
            Rank.minimumKRWChargeRequirement <= user.statistics.totalKRWCharge
        ).to_list()

        if not eligible_ranks:
            return await Database.get_default_rank()

        highest_rank = max(eligible_ranks, key=attrgetter("minimumKRWChargeRequirement"))

        return highest_rank
    
    @staticmethod
    async def get_default_rank() -> Rank:
        """가장 낮은 Rank (없으면 DEFAULT_RANK_OBJECT upsert)"""
        lowest = await Rank.find({}, sort=[("minimumKRWChargeRequirement", SortDirection.ASCENDING)]).first_or_none()
        if lowest:
            return lowest

        # upsert -----------------------------------------------------------
        return await Rank.find_one(Rank.name == DEFAULT_RANK_OBJECT["name"]).upsert( # type: ignore[arg-type]
            Set({}),
            on_insert=Rank(**DEFAULT_RANK_OBJECT),
            response_type=UpdateResponse.NEW_DOCUMENT,
        )

    @staticmethod
    async def get_referral_owner(code: str) -> Optional[User]:
        return await User.find_one(User.referralCode == code)
    
    @staticmethod
    async def add_referral_code(discord_id: str, code: str) -> bool:
        """리퍼럴 코드 연결"""
        try:
            owner = await Database.get_referral_owner(code)
            if not owner:
                return False

            user = await Database.get_user_info(discord_id)
            if not user or user.invitedBy:  # 이미 등록된 경우 방지
                return False

            user_ref = DBRef(collection=User.get_collection_name(), id=owner.id)
            link_to_owner = Link(user_ref, User)

            await user.update(Set({User.invitedBy: link_to_owner}))
            return True
        except Exception:
            return False

    @staticmethod
    async def add_crypto_address(discord_id: str, cryptoAddress: CryptoAddress) -> bool:
        """User.cryptoAddresses 배열에 주소 push"""
        try:
            user = await Database.get_user_info(discord_id)
            if not user:
                return False

            await user.update(
                Push({User.cryptoAddresses: cryptoAddress}) # type: ignore[arg-type]
            )
            return True
        except Exception:
            return False
        
    @staticmethod
    async def create_charge_log(
        discord_id: str, amount: Int64, senderName: str
    ) -> KRWChargeLog | None:
        user = await Database.get_user_info(discord_id)

        if not user:
            return None
        
        user_ref = DBRef(collection=User.get_collection_name(), id=user.id)
        link_to_user = Link(user_ref, User)

        chargeLog = KRWChargeLog(
            state="PENDING",
            amount=amount,
            senderName=senderName,
            user=link_to_user,
            createdAt=datetime.datetime.now(),
        )
        await chargeLog.insert()
        return chargeLog

    @staticmethod
    async def change_charge_status(
        log: KRWChargeLog, success: bool, txid: str | None = None, depositTime: Int64 | None = None
    ) -> bool:
        try:
            if success:
                log.state = "COMPLETED"
                log.txid = txid
                log.depositTime = depositTime
            else:
                log.state = "FAILED"
            await log.save()
            return True
        except Exception:
            return False

    @staticmethod
    async def get_crypto_address(discord_id: str, crypto: str, network: str) -> List[CryptoAddress]:
        user = await Database.get_user_info(discord_id)
        if not user:
            return []

        return [
            addr
            for addr in user.cryptoAddresses
            if addr.crypto.upper() == crypto.upper() and addr.network.upper() == network.upper()
        ]
    
    @staticmethod
    async def pay_referral_payback(discord_id: str, amount: Int64) -> tuple[User, Int64] | None:
        user = await Database.get_user_info(discord_id)
        if not user or not user.invitedBy:
            return None

        calc = Database.calc_fee(int(amount), Decimal(REFERRAL_PAYBACK_PERCENT))
        payback: Int64 = calc["fee"]

        await user.invitedBy.update(Inc({User.balances.KRW: payback}))
        return user.invitedBy, payback

    @staticmethod
    def calc_fee(amount: int, percent: str | Decimal) -> dict[str, Int64]:
        amount_dec = Decimal(amount)
        rate = Decimal(str(percent)) / Decimal("100")
        fee = (amount_dec * rate).quantize(Decimal("1."), rounding=ROUND_DOWN)
        final = (amount_dec - fee).quantize(Decimal("1."), rounding=ROUND_DOWN)
        return {"fee": Int64(int(fee)), "final": Int64(int(final))}

    @staticmethod
    async def is_user_over_charge_limit(discord_id: str, amount: Int64) -> bool:
        user = await Database.get_user_info(discord_id)
        if not user:
            return True

        daily_limit = int(user.limits.dailyChargeLimit) if user.limits else 0

        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + datetime.timedelta(days=1)

        logs: List[KRWChargeLog] = await KRWChargeLog.find(
            KRWChargeLog.user.ref == user.id,
            KRWChargeLog.state == "COMPLETED",
            KRWChargeLog.createdAt >= today_start,
            KRWChargeLog.createdAt < tomorrow_start,
        ).to_list()

        today_total = sum(int(log.amount) for log in logs)
        return (today_total + int(amount)) > daily_limit

    @staticmethod
    async def get_recent_crypto_transactions(
        discord_id: str, limit: int = 5
    ) -> List[CryptoTransaction] | None:
        user = await Database.get_user_info(discord_id)
        if not user:
            return None

        return (
            await CryptoTransaction.find(CryptoTransaction.user.id == user.id, fetch_links=True) # type: ignore[arg-type]
                .sort("-_id")
                .limit(limit)
                .to_list()
        )
    
    @staticmethod
    async def edit_user_balances(discord_id: str, amount: Int64) -> None:
        user = await Database.get_user_info(discord_id)
        if not user:
            return

        await user.update(Inc({User.balances.KRW: amount}))

    @staticmethod
    async def update_user_total_charge(discord_id: str, amount: Int64) -> None:
        user = await Database.get_user_info(discord_id)
        if not user:
            return

        await user.update(Inc({User.statistics.totalKRWCharge: amount}))

    @staticmethod
    async def is_shuffle_address(discord_id: str, crypto: str, network: str, address: str) -> bool:
        user = await Database.get_user_info(discord_id)
        if not user:
            return False

        for crypto_address in user.cryptoAddresses:
            if crypto_address.crypto == crypto and crypto_address.network == network and crypto_address.address == address:
                return getattr(crypto_address, "isShuffleAddress", False)

        return False
    
    @staticmethod
    async def edit_user_charge_limit(discord_id: str, dailyChargeLimit: Int64, dailySellingLimit: Optional[Int64] = None):
        user = await Database.get_user_info(discord_id, True)
        if not user:
            return False
        
        if dailySellingLimit is not None:
            new_selling = dailySellingLimit
        else:
            new_selling = user.limits.dailySellingLimit

        await user.update(Set({User.limits.dailyChargeLimit: dailyChargeLimit, User.limits.dailySellingLimit: new_selling }))

        return True
    
    @staticmethod
    async def migrate_user(discord_id: str, new_discord_id: str) -> bool:
        user = await Database.get_user_info(discord_id, True)
        if not user:
            return False
        existing_new_user = await User.find_one(User.discordId == new_discord_id)

        try:
            await user.update(
                Set({
                    User.discordId: new_discord_id,
                    User.referralCode: generate_referral_code(new_discord_id),
                    User.balances.KRW: Int64(user.balances.KRW + (existing_new_user.balances.KRW if existing_new_user else Int64(0))),
                    User.statistics.totalKRWCharge: Int64(user.statistics.totalKRWCharge + (existing_new_user.statistics.totalKRWCharge if existing_new_user else Int64(0))),
                    User.limits.dailyChargeLimit: max(user.limits.dailyChargeLimit, existing_new_user.limits.dailyChargeLimit if existing_new_user else Int64(DEFAULT_DAILY_CHARGE_LIMIT)),
                    User.limits.dailySellingLimit: max(user.limits.dailySellingLimit, existing_new_user.limits.dailySellingLimit if existing_new_user else Int64(DEFAULT_DAILY_SELLING_LIMIT)),
                })
            )

            if existing_new_user:
                await existing_new_user.delete()
        except Exception as e:
            print(f"Error migrating user {discord_id} to {new_discord_id}: {e}")
            return False
     
        return True
    
    @staticmethod
    async def add_krw_account(discord_id: str, krw_account: KRWAccount):
        user = await Database.get_user_info(discord_id, True)
        if not user:
            return False
        
        user.krwAccounts.append(krw_account)

        await user.save()

        return True

    @staticmethod
    async def delete_krw_account(discord_id: str, krw_account: KRWAccount):
        user = await Database.get_user_info(discord_id, True)
        if not user:
            return False
        
        user.krwAccounts.remove(krw_account)

        await user.save()

        return True

    @staticmethod
    async def get_charge_logs_by_date_range(start_date: datetime.datetime, end_date: datetime.datetime) -> List[KRWChargeLog]:
        """지정된 날짜 범위의 충전 내역 조회"""
        return await KRWChargeLog.find(
            KRWChargeLog.state == "COMPLETED",
            KRWChargeLog.createdAt >= start_date,
            KRWChargeLog.createdAt <= end_date
        ).to_list()

    @staticmethod
    async def get_crypto_transactions_by_date_range(start_date: datetime.datetime, end_date: datetime.datetime) -> List[CryptoTransaction]:
        """지정된 날짜 범위의 암호화폐 거래 내역 조회"""
        return await CryptoTransaction.find(
            CryptoTransaction.createdAt >= start_date,
            CryptoTransaction.createdAt <= end_date
        ).to_list()

    @staticmethod
    async def get_statistics_by_date_range(start_date: datetime.datetime, end_date: datetime.datetime) -> dict:
        """지정된 날짜 범위의 통계 정보 조회"""
        charge_logs = await Database.get_charge_logs_by_date_range(start_date, end_date)
        crypto_transactions = await Database.get_crypto_transactions_by_date_range(start_date, end_date)

        # 충전 통계
        total_charge_amount = sum(int(log.amount) for log in charge_logs)
        charge_count = len(charge_logs)

        # print(crypto_transactions, "crypto_transactions", charge_logs, "charge_logs", start_date, end_date, "start_date, end_date")

        # 거래 통계
        total_transaction_amount = sum(int(tx.amountKRW) for tx in crypto_transactions)
        total_revenue = sum(int(tx.revenue) for tx in crypto_transactions)
        transaction_count = len(crypto_transactions)

        # 암호화폐별 거래량
        crypto_stats = {}
        for tx in crypto_transactions:
            symbol = tx.cryptoSymbol
            if symbol not in crypto_stats:
                crypto_stats[symbol] = {
                    'count': 0,
                    'total_krw': 0,
                    'total_crypto': 0.0,
                    'revenue': 0
                }
            crypto_stats[symbol]['count'] += 1
            crypto_stats[symbol]['total_krw'] += int(tx.amountKRW)
            crypto_stats[symbol]['total_crypto'] += tx.amountCrypto
            crypto_stats[symbol]['revenue'] += int(tx.revenue)

        return {
            'charge_logs': charge_logs,
            'crypto_transactions': crypto_transactions,
            'total_charge_amount': total_charge_amount,
            'charge_count': charge_count,
            'total_transaction_amount': total_transaction_amount,
            'total_revenue': total_revenue,
            'transaction_count': transaction_count,
            'crypto_stats': crypto_stats
        }