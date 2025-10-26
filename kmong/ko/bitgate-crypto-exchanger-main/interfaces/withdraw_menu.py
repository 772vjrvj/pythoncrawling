import datetime
import traceback
from decimal import Decimal
from typing import List, Literal, Optional

import discord
from beanie import Link
from bson import DBRef
from bson.int64 import Int64

from models.CryptoTransaction import CryptoTransaction
from models.User import CryptoAddress, User
from modules.binance import Binance, BinanceError, NetworkError
from modules.constants import SUPPORTED_CRYPTO_CURRENCIES
from modules.database import Database
from modules.kebhana import get_usd_price
from modules.kimp import get_kimp
from modules.log import send_discord_log
from modules.utils import (generate_uuid_log_id, get_crypto_by_symbol,
                           get_env_config)

config = get_env_config()

class LoadingView(discord.ui.LayoutView):
    def __init__(self, title: str, subTitle: str, description: str):
        super().__init__()

        container = DefaultContainer(
            title, subTitle, description
        )
        container.accent_color = 0xffffff

        self.add_item(container)

class DefaultContainer(discord.ui.Container):
    def __init__(self, title: str, sub_title: str, description: str, rows: Optional[list] = None):
        super().__init__()

        title_text_display = discord.ui.TextDisplay(title)
        subTitle_text_display = discord.ui.TextDisplay(sub_title)
        description_text_display = discord.ui.TextDisplay(description)


        self.add_item(title_text_display)
        
        self.add_item(discord.ui.Separator())

        self.add_item(subTitle_text_display)
        self.add_item(description_text_display)

        self.add_item(discord.ui.Separator())

        if rows:
            for row in rows:
                self.add_item(row)

            self.add_item(discord.ui.Separator())

        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {config.brand_name} - 24시간 코인송금대행"))

class SelectCoin(discord.ui.LayoutView):
    def __init__(self, binance: Binance):
        super().__init__()
        self.binance = binance
        self.selected_crypto_symbol: Optional[str] = None
        self.selected_network: Optional[str] = None

        self.selectCryptoInput = discord.ui.Select(
            placeholder="송금하실 암호화폐를 선택해주세요.",
            options=[
                discord.SelectOption(
                    label=f"{crypto['name']} ({crypto['symbol']})",
                    value=crypto["symbol"],
                    emoji=crypto["emoji"]
                )
                for crypto in SUPPORTED_CRYPTO_CURRENCIES
            ]
        )
        self.selectCryptoInput.callback = self.cryptoCallback

        self.selectNetworkInput = discord.ui.Select(
            placeholder="네트워크를 선택해주세요.",
            options=[discord.SelectOption(label="암호화폐를 먼저 선택해주세요.")],
            disabled=True
        )
        self.selectNetworkInput.callback = self.networkCallback

    async def create(self, interaction: discord.Interaction):
        try:
            stock = await self.binance.get_stock()
            kimp  = await get_kimp()
        except NetworkError as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=config.error_log_webhook
            )
            return
        except BinanceError as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=config.error_log_webhook
            )
            return
        except Exception:
            tb = traceback.format_exc()
            log_id = generate_uuid_log_id()

            await interaction.response.send_message("예기치 못한 오류가 발생했어요.", ephemeral=True)

            admin_embed = discord.Embed(
                title="🚨 [SelectCoin.create] Unexpected Error",
                description=f"로그 ID: `{log_id}`",
                color=0xE74C3C
            )
            admin_embed.add_field(
                name="User",
                value=f"{interaction.user} (`{interaction.user.id}`)",
                inline=False
            )
            channel = interaction.channel
            admin_embed.add_field(
                name="Channel",
                value=f"{getattr(channel, 'name', 'DM')} (`{getattr(channel, 'id', 'N/A')}`)",
                inline=False
            )
            if interaction.guild:
                admin_embed.add_field(
                    name="Guild",
                    value=f"{interaction.guild.name} (`{interaction.guild.id}`)",
                    inline=False
                )
            admin_embed.add_field(
                name="Stack Trace",
                value=f"```\n" + (tb if len(tb) <= 1000 else tb[:1000] + "\n... (truncated)") + "\n```",
                inline=False
            )

            await send_discord_log(
                embed=admin_embed,
                webhook_url=config.error_log_webhook
            )
            return

        initialDesc = f"실시간 재고: `{stock['KRW']:,}`원 (≈ `${round(stock['USD'], 2)}`)\n김프: `{kimp}%`"
        container = DefaultContainer(
            "### 🚀 암호화폐 선택",
            "### 송금",
            initialDesc,
            rows=[discord.ui.ActionRow(self.selectCryptoInput), discord.ui.ActionRow(self.selectNetworkInput)]
        )
        container.accent_color = 0xffffff
        self.clear_items()
        self.add_item(container)

    async def cryptoCallback(self, interaction: discord.Interaction):
        self.selected_crypto_symbol = self.selectCryptoInput.values[0]

        for opt in self.selectCryptoInput.options:
            opt.default = (opt.value == self.selected_crypto_symbol)
        networks = get_crypto_by_symbol(self.selected_crypto_symbol).get("networks", [])
        self.selectNetworkInput.options = [
            discord.SelectOption(label=n['name'], value=n['name'], emoji=n['emoji'])
            for n in networks
        ]
        self.selectNetworkInput.disabled = False
        await interaction.response.edit_message(view=self)

    async def networkCallback(self, interaction: discord.Interaction):
        if not self.selected_crypto_symbol:
            return

        await interaction.response.edit_message(
            view=LoadingView(
                "### ⌛ 로딩 중",
                "### 송금",
                "> 정보를 불러오는 중이에요."
            )
        )
        self.selected_network = self.selectNetworkInput.values[0]

        confirm = ConfirmView(self.selected_crypto_symbol, self.selected_network)
        ok = await confirm.create(interaction, str(interaction.user.id))
        if ok:
            await interaction.edit_original_response(
                view=confirm
            )

class WithdrawSuccessView(discord.ui.LayoutView):
    def __init__(self, transaction: CryptoTransaction):
        super().__init__()

        container = DefaultContainer(
            f"### {get_crypto_by_symbol(transaction.cryptoSymbol).get('emoji')} ${transaction.cryptoSymbol} 송금에 성공했어요",
            "### 암호화폐 송금",
            f"${transaction.cryptoSymbol} 송금에 성공했어요.\n더 자세한 출금 정보는, 내 정보 버튼을 누르셔서 확인하실 수 있어요."
        )
        container.accent_color = 0xffffff

        self.add_item(container)

class WithdrawFailView(discord.ui.LayoutView):
    def __init__(self, crypto, description: str):
        super().__init__()

        container = DefaultContainer(
            f"### {get_crypto_by_symbol(crypto).get('emoji')} ${crypto} 송금에 실패했어요",
            f"### 암호화폐 송금하기",
            description
        )
        container.accent_color = 0xffffff

        self.add_item(container)

class WithdrawPendingView(discord.ui.LayoutView):
    def __init__(self, crypto):
        super().__init__()

        container = DefaultContainer(
            f"### {get_crypto_by_symbol(crypto).get('emoji')} ${crypto} 송금을 진행하는 중이에요",
            f"### 암호화폐 송금하기",
            "송금을 진행하는 중이에요. 잠시만 기다려주세요."
        )
        container.accent_color = 0xffffff

        self.add_item(container)

class WithdrawInfoModal(discord.ui.Modal):
    def __init__(
        self,
        modal_type: Literal["MANUAL", "QUICK"],
        crypto: str,
        network: str,
        address: Optional[str] = None,
        tag: Optional[str] = None
    ):
        super().__init__(title=f"{crypto} 송금 정보 입력하기", timeout=180)
        self.crypto = crypto
        self.network = network
        self.address = address
        self.tag = tag
        self.modal_type = modal_type
        if modal_type == "MANUAL":
            self.addrInput = discord.ui.TextInput(
                label="받는 지갑 주소",
                placeholder="",
                required=True,
            )
            self.tagInput = discord.ui.TextInput(
                label="Destination Tag",
                placeholder="XRP 송금 시에만 입력해주세요",
                required=False,
            )
            self.amtInput = discord.ui.TextInput(
                label="보낼 금액 (원화)",
                placeholder="숫자만 입력해주세요.",
                required=True,
                max_length=10,
            )
            self.add_item(self.addrInput)
            self.add_item(self.tagInput)
            self.add_item(self.amtInput)
        else:
            self.amtInput = discord.ui.TextInput(
                label="보낼 금액 (원화)",
                placeholder="숫자만 입력해주세요.",
                required=True,
                max_length=10,
            )
            self.add_item(self.amtInput)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=WithdrawPendingView(self.crypto))
        try:
            amount_KRW = int(self.amtInput.value.replace(",", ""))
        except ValueError:
            return await interaction.edit_original_response(
                view=WithdrawFailView(self.crypto, "금액을 정확히 입력해주세요.")
            )
    
        if amount_KRW < Int64(config.minimum_crypto_purchase_krw_amount):
            return await interaction.edit_original_response(
                view=WithdrawFailView(self.crypto, f"최소 {config.minimum_crypto_purchase_krw_amount}원 이상 구매해야 합니다.")
            )

        addr = (self.addrInput.value if self.modal_type == "MANUAL" else self.address) or ""
        tagv = (self.tagInput.value if self.modal_type == "MANUAL" else self.tag) or ""

        user = await Database.get_user_info(str(interaction.user.id))

        if not user or user.balances.KRW < Int64(amount_KRW):
            return await interaction.edit_original_response(
                view=WithdrawFailView(self.crypto, "잔액이 부족해요. 충전 후 다시 시도해주세요.")
            )

        stock = await Binance().get_stock()

        if Int64(stock["KRW"]) < Int64(amount_KRW):
            return await interaction.edit_original_response(
                view = WithdrawFailView(self.crypto, "현재 재고가 부족해요. 재입고 후 다시 시도해주세요.")
            )

        actual_kimp = await get_kimp()
        kimp = max(actual_kimp, 0)

        update_amount_krw = Int64((-1 * amount_KRW))

        await Database.edit_user_balances(str(interaction.user.id), update_amount_krw)

        userRank = await Database.get_user_rank(str(interaction.user.id))

        isShuffleAddress = await Database.is_shuffle_address(str(interaction.user.id), self.crypto, self.network, addr)

        if isShuffleAddress:
            fee = kimp
        else:
            fee = userRank.cryptoPurchasingFee + kimp

        calcResult = Database.calc_fee(amount_KRW, Decimal(fee))

        revenue, finalAmount = calcResult["fee"], calcResult["final"]

        try:
            if self.crypto == "USDT":
                info = await Binance().send_usdt(int(finalAmount), addr, self.network)
            else:
                info = await Binance().send_coin(int(finalAmount), addr, self.crypto, self.network, tag=tagv)
        except NetworkError as e:
            await Database.edit_user_balances(str(interaction.user.id), Int64(amount_KRW))

            await interaction.edit_original_response(
                view=WithdrawFailView(self.crypto, e.user_msg)
            )
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=config.error_log_webhook
            )
            return
        except BinanceError as e:
            await Database.edit_user_balances(str(interaction.user.id), Int64(amount_KRW))

            await interaction.edit_original_response(
                view=WithdrawFailView(self.crypto, e.user_msg)
            )
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=config.error_log_webhook
            )
            return
        except Exception as e:
            await Database.edit_user_balances(str(interaction.user.id), Int64(amount_KRW))

            tb = traceback.format_exc()
            log_id = generate_uuid_log_id()

            await interaction.edit_original_response(
                view=WithdrawFailView(self.crypto, "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            )

            admin_embed = discord.Embed(
                title="🚨 [WithdrawInfoModal] Unexpected Error",
                description=f"로그 ID: `{log_id}`",
                color=0xE74C3C
            )
            admin_embed.add_field(
                name="User",
                value=f"{interaction.user} (`{interaction.user.id}`)",
                inline=False
            )
            channel = interaction.channel
            admin_embed.add_field(
                name="Channel",
                value=f"{getattr(channel, 'name', 'DM')} (`{getattr(channel, 'id', 'N/A')}`)",
                inline=False
            )
            if interaction.guild:
                admin_embed.add_field(
                    name="Guild",
                    value=f"{interaction.guild.name} (`{interaction.guild.id}`)",
                    inline=False
                )
            admin_embed.add_field(
                name="Stack Trace",
                value=f"```\n" + (tb if len(tb) <= 1000 else tb[:1000] + "\n... (truncated)") + "\n```",
                inline=False
            )

            await send_discord_log(
                embed=admin_embed,
                webhook_url=config.error_log_webhook
            )
            return

        user_ref = DBRef(collection=User.get_collection_name(), id=user.id)
        link_to_user = Link(user_ref, User)

        tx = CryptoTransaction(
            binanceWithdrawalId=info['id'],
            cryptoSymbol=self.crypto,
            networkName=self.network,
            address=addr,
            tag=tagv,
            amountKRW=Int64(amount_KRW),
            amountCrypto=float(info.get('amount', 0)),
            user=link_to_user,
            revenue=Int64(revenue),
            createdAt=datetime.datetime.now()
        )
        await tx.insert()

        log_embed = discord.Embed(
            title = "💸 출금 성공",
            description = f"{interaction.user.mention}님이 출금에 성공하셨어요.",
            color = 0xffffff
        )
        log_embed.add_field(
            name = "바이낸스 출금 ID", value = info['id']
        )
        log_embed.add_field(
            name = "사용자", value = f"{interaction.user} (`{interaction.user.id}`)"
        )
        log_embed.add_field(
            name = "지갑 주소", value = addr
        )
        log_embed.add_field(
            name = "대상 태그 (Destination Tag)", value = tagv if tagv else "없음"
        )
        log_embed.add_field(
            name = "사용자 등급", value = f"{userRank.name} ({userRank.id})"
        )
        log_embed.add_field(
            name = "암호화폐/네트워크", value = f"{self.crypto}/{self.network}"
        )
        log_embed.add_field(
            name = "출금 금액 (KRW/Amount)", value = f"{amount_KRW:,}원 / {info['amount']} {self.crypto}"
        )
        log_embed.add_field(
            name = "총 대행 수수료(총이익)", value = f"{revenue}원 (대행 수수료: {fee}%, 적용된 김프: {kimp}%, 실제 김프: {actual_kimp}%)"
        )
        log_embed.add_field(
            name = "셔플 주소 여부", value = f"{'예' if isShuffleAddress else '아니오'}"
        )
        log_embed.add_field(
            name = "사용자 잔액 차감 전", value = f"{user.balances.KRW:,}원"
        )
        log_embed.add_field(
            name = "사용자 잔액 차감 후", value = f"{user.balances.KRW - amount_KRW:,}원"
        )
        await send_discord_log(
            discord_user_id=interaction.user.id,
            embed=log_embed,
            webhook_url=config.buy_log_webhook
        )

        await interaction.edit_original_response(
            view=WithdrawSuccessView(tx)
        )


class ManualWithdrawButton(discord.ui.Button):
    def __init__(self, crypto: str, network: str):
        super().__init__(
            label="송금 정보 직접 입력",
            style=discord.ButtonStyle.green,
            emoji="✍️",
        )
        self.crypto, self.network = crypto, network

    async def callback(self, interaction: discord.Interaction):
        modal = WithdrawInfoModal(
            modal_type="MANUAL",
            crypto=self.crypto,
            network=self.network,
        )
        await interaction.response.send_modal(modal)

class QuickWithdrawByAddresses(discord.ui.Select):
    def __init__(self, addresses: Optional[List[CryptoAddress]] = None):
        super().__init__(
            placeholder="출금하실 주소를 선택해주세요.",
            options=self._build_options(addresses)
        )
        self.addresses = addresses or []

    def _build_options(self, addresses: Optional[List[CryptoAddress]]):
        options = []
        if addresses:
            for addr in addresses:
                options.append(
                    discord.SelectOption(
                        label=addr.alias,
                        value=f"{addr.crypto}|{addr.network}|{addr.address}",
                        description=f"{addr.crypto} - {addr.network} | {'셔플 제휴가 적용 중이에요.' if addr.isShuffleAddress else '셔플 제휴가 적용되지 않는 주소에요.'}",
                        emoji=get_crypto_by_symbol(addr.crypto).get('emoji')
                    )
                )

        return options

    async def callback(self, interaction: discord.Interaction):
        try:
            crypto, network, addr_value = self.values[0].split("|", 2)
        except ValueError:
            embed = discord.Embed(
                title="⚠️ 오류",
                description="알 수 없는 오류가 발생했어요.",
                color=0xE67E22
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected = next(
            (a for a in self.addresses
             if a.crypto == crypto and a.network == network and a.address == addr_value),
            None
        )
        if not selected:
            embed = discord.Embed(
                title="⚠️ 오류",
                description="알 수 없는 오류가 발생했어요.",
                color=0xE67E22
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # 주소록 기반이므로 주소·태그는 고정, 금액만 입력받는 모달
        modal = WithdrawInfoModal(
            modal_type="QUICK",
            crypto=selected.crypto,
            network=selected.network,
            address=selected.address,
            tag=selected.tag
        )
        await interaction.response.send_modal(modal)

class ConfirmContainer(discord.ui.Container):
    def __init__(self, crypto, network, KRWPrice, USDPrice, addresses: List[CryptoAddress]):
        super().__init__()

        title = discord.ui.TextDisplay(f"### {get_crypto_by_symbol(crypto).get('emoji')} ${crypto} - {network} 송금을 진행하시겠어요?")
        subTitle = discord.ui.TextDisplay(f"### 현재 {crypto} 가격")
        description = discord.ui.TextDisplay(f"> 1 {crypto} = {KRWPrice:,}원 (≈ ${USDPrice})")

        self.add_item(title)
        self.add_item(discord.ui.Separator())
        self.add_item(subTitle)
        self.add_item(description)
        self.add_item(discord.ui.Separator())

        if addresses and len(addresses) > 0:
            self.add_item(discord.ui.TextDisplay(f"### 주소록으로 빠른 출금\n> - 주소록에 등록된 주소로 간편하게 송금할 수 있어요."))

            self.add_item(discord.ui.ActionRow(QuickWithdrawByAddresses(addresses)))

            self.add_item(discord.ui.Separator())

        self.add_item(discord.ui.Section(f"### 원하는 주소로 직접 출금\n> - 원하는 주소를 직접 입력해서 송금할 수 있어요.", accessory=ManualWithdrawButton(crypto, network)))

        self.add_item(discord.ui.Separator())

        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {config.brand_name} - 24시간 코인송금대행"))

class ConfirmView(discord.ui.LayoutView):
    def __init__(self, crypto: str, network: str):
        super().__init__(timeout=None)
        self.crypto = crypto
        self.network = network

    async def create(self, interaction: discord.Interaction, discord_id: str) -> bool:
        # 1) 실시간 가격·김프·환율 조회
        try:
            price = await Binance().get_price(self.crypto)
            kimp  = await get_kimp()
            usd_rate = await get_usd_price()
        except NetworkError as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=config.error_log_webhook
            )
            return False
        except BinanceError as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=config.error_log_webhook
            )
            return False
        except Exception:
            tb = traceback.format_exc()
            log_id = generate_uuid_log_id()

            await interaction.response.send_message("예기치 못한 오류가 발생했어요.", ephemeral=True)

            admin_embed = discord.Embed(
                title="🚨 [ConfirmView] Unexpected Error",
                description=f"로그 ID: `{log_id}`",
                color=0xE74C3C
            )
            admin_embed.add_field(
                name="User",
                value=f"{interaction.user} (`{interaction.user.id}`)",
                inline=False
            )
            channel = interaction.channel
            admin_embed.add_field(
                name="Channel",
                value=f"{getattr(channel, 'name', 'DM')} (`{getattr(channel, 'id', 'N/A')}`)",
                inline=False
            )
            if interaction.guild:
                admin_embed.add_field(
                    name="Guild",
                    value=f"{interaction.guild.name} (`{interaction.guild.id}`)",
                    inline=False
                )
            admin_embed.add_field(
                name="Stack Trace",
                value=f"```\n" + (tb if len(tb) <= 1000 else tb[:1000] + "\n... (truncated)") + "\n```",
                inline=False
            )

            await send_discord_log(
                embed=admin_embed,
                webhook_url=config.error_log_webhook
            )

            return False

        # 2) 김프 적용 최종 가격 계산
        krw_base = price["KRW"]
        fee      = Database.calc_fee(krw_base, Decimal(kimp))["fee"]
        final_krw = krw_base + fee
        final_usd = final_krw / usd_rate

        # 3) 사용자 주소록 필터링
        user = await Database.get_user_info(discord_id)
        if not user:
            await interaction.response.send_message("유저 정보를 불러올 수 없어요.", ephemeral=True)
            return False

        addresses = [
            addr for addr in user.cryptoAddresses
            if addr.crypto == self.crypto and addr.network == self.network
        ]

        # 4) ConfirmContainer 세팅
        container = ConfirmContainer(
            crypto=self.crypto,
            network=self.network,
            KRWPrice=final_krw,
            USDPrice=final_usd,
            addresses=addresses
        )
        container.accent_color = 0xffffff

        # 뷰 초기화 후 추가
        self.clear_items()
        self.add_item(container)
        return True