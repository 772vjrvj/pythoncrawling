import traceback
from typing import List, Optional

import discord
from beanie.odm.operators.update.array import Pull
from beanie.odm.operators.update.general import Set
from discord import ui

from interfaces.crypto_address_menu import AddressRegisterView
from interfaces.withdraw_menu import DefaultContainer
from models.CryptoTransaction import CryptoTransaction
from models.Rank import Rank
from models.User import CryptoAddress, User
from modules.binance import Binance, BinanceError, NetworkError
from modules.database import Database
from modules.log import send_discord_log
from modules.utils import (generate_uuid_log_id, get_crypto_by_symbol,
                           get_env_config)

config = get_env_config()

BRAND_NAME = config.brand_name
ERROR_LOG_WEBHOOK = config.error_log_webhook
REFERRAL_LOG_WEBHOOK = config.referral_log_webhook
REFERRAL_PAYBACK_PERCENT = config.referral_payback_percent

class InfoMainView(discord.ui.LayoutView):
    def __init__(self, container):
        super().__init__()
        container.accent_color = 0xffffff
        
        self.add_item(container)

class UserMenuMainContainer(discord.ui.Container):
    def __init__(self, user_data: User, default_rank: Rank, recentTransactions: Optional[List[CryptoTransaction]] = None):
        super().__init__()
        
        title = discord.ui.TextDisplay(f"### 👋 반가워요, {user_data.verificationData.name if user_data.verificationData else 'UNKNOWN'}님.")

        sep1 = discord.ui.Separator()
        
        balanceText = discord.ui.TextDisplay(f"- 사용 가능 잔액\n> **{user_data.balances.KRW:,}원**")
        usedText = discord.ui.TextDisplay(f"- 누적 사용 금액\n> **{user_data.statistics.totalKRWCharge:,}원**")
        feeText = discord.ui.TextDisplay(f"- 적용된 수수료\n> 구매: **{default_rank.cryptoPurchasingFee}%**, 매입: **{default_rank.cryptoSellingFee}%**")
        limitText = discord.ui.TextDisplay(f"- 일일 원화 한도\n> 충전: **{user_data.limits.dailyChargeLimit:,}원**, 매입: **{user_data.limits.dailySellingLimit:,}원**")

        sep2 = discord.ui.Separator()
        
        recentTransactionRow = discord.ui.ActionRow(RecentTransactionSelect(recentTransactions))

        sep3 = discord.ui.Separator()

        utilRow = discord.ui.ActionRow(ReferralButton(user_data=user_data), AddressBookButton(user_data=user_data))

        for item in (title, sep1, usedText, balanceText, feeText, limitText, sep2, recentTransactionRow, sep3, utilRow):
            self.add_item(item)

class RecentTransactionSelect(ui.Select):
    def __init__(self, transactions: Optional[List[CryptoTransaction]] = None):
        options = []
        if transactions:
            for tx in transactions:
                options.append(
                    discord.SelectOption(
                        label=f"{tx.address}",
                        description=f"{tx.amountCrypto} {tx.cryptoSymbol} ({tx.networkName}) | {tx.createdAt}",
                        value=tx.binanceWithdrawalId,
                        emoji=get_crypto_by_symbol(tx.cryptoSymbol).get('emoji')
                    )
                )
        else:
            options.append(
                discord.SelectOption(
                    label="최근 거래 내역이 존재하지 않아요.",
                    value="no_history",
                    default=True
                )
            )
        super().__init__(
            custom_id="recent_transaction_selection",
            placeholder="최근 거래 내역",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        if choice == "no_history":
            return

        try:
            info = await Binance().get_withdrawal_info(choice)
        except NetworkError as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=ERROR_LOG_WEBHOOK
            )
            return
        except BinanceError as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,level="ERROR",
                webhook_url=ERROR_LOG_WEBHOOK
            )
            return
        except Exception as e:
            tb = traceback.format_exc()
            log_id = generate_uuid_log_id()

            user_embed = discord.Embed(
                title="❌ 알 수 없는 오류",
                description=(
                    "알 수 없는 오류가 발생했어요. 관리자에게 문의해주세요.\n"
                    f"로그 ID: `{log_id}`"
                ),
                color=0xE74C3C
            ).set_footer(text="문의 시 로그 ID를 알려주세요")

            await interaction.response.send_message(embed=user_embed, ephemeral=True)

            admin_embed = discord.Embed(
                title="🚨 [RecentTransactionSelect] Unexpected Error",
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
                webhook_url=ERROR_LOG_WEBHOOK
            )

            return

        embed = discord.Embed(
            title="출금 정보 조회하기",
            description="> 출금하신 정보를 조회하실 수 있어요.",
            color=0x00FF00
        )
        embed.add_field(name="지갑 주소", value=info.get("address", "—"))
        embed.add_field(name="코인/체인", value=f"{info.get('coin','—')} ({info.get('network','—')})")
        embed.add_field(name="수량", value=f"{info.get('amount','—')} {info.get('coin','—')}")
        embed.add_field(name="TxID", value=info.get('txId','—'))
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ReferralSuccessRegister(discord.ui.Container):
    title = discord.ui.TextDisplay("### ✅ 레퍼럴 코드 등록에 성공했어요")
    sep1 = discord.ui.Separator()
    subTitle = discord.ui.TextDisplay("### 레퍼럴 코드 등록")
    description = discord.ui.TextDisplay("> 신규 레퍼럴 코드가 등록되었어요!")

    def __init__(self, referralCode: str, codeOwner: User):
        super().__init__()
        
        desc = f"`{referralCode}` 코드가 사용자님에게 적용되었어요. (코드 주인: <@{codeOwner.discordId}> )"

        applyedReferralCodeDesc = discord.ui.TextDisplay(desc)

        self.add_item(applyedReferralCodeDesc)
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행"))

class ReferralSuccessView(discord.ui.LayoutView):
    def __init__(self, referralCode: str, codeOwner: User):
        super().__init__()
        container = ReferralSuccessRegister(referralCode, codeOwner)
        container.accent_color = 0xffffff
        self.add_item(container)

class InputReferralCodeModal(discord.ui.Modal):
    def __init__(self, user_data: User):
        super().__init__(title = "레퍼럴 코드 등록하기")
        self.user_data = user_data
    
        self.referralCode = discord.ui.TextInput(
            label = "레퍼럴 코드",
            placeholder = "24735BE03A58",
            min_length = 12, max_length = 12
        )
        
        self.add_item(self.referralCode)

    async def on_submit(self, interaction: discord.Interaction):
        codeOwner = await Database.get_referral_owner(self.referralCode.value)

        if not codeOwner: return await interaction.response.send_message(
            embed = discord.Embed(
                title = "❌ 레퍼럴 등록에 실패했어요",
                description = "존재하지 않는 레퍼럴 코드예요.",
                color = 0xffffff
            ), ephemeral = True
        )
        
        if str(self.user_data.id) == str(codeOwner.id): return await interaction.response.send_message(
            embed = discord.Embed(
                title = "❌ 레퍼럴 등록에 실패했어요",
                description = "자기 자신의 레퍼럴 코드는 등록할 수 없어요.",
                color = 0xffffff
            ), ephemeral = True
        )

        await self.user_data.update(Set({User.invitedBy: codeOwner}))
        
        # self.user_data.invitedBy = codeOwner
        # await self.user_data.save()

        await interaction.response.send_message(
            view = ReferralSuccessView(self.referralCode.value, codeOwner), ephemeral = True
        )

        log_embed = discord.Embed(
            title = "🔗 레퍼럴이 활성화되었어요",
            color = 0xffffff
        )
        log_embed.add_field(
            name = "적용한 유저", value = f"<@{self.user_data.discordId}> ({self.user_data.discordId})"
        )
        log_embed.add_field(
            name = "적용된 코드", value = f"`{self.referralCode.value}`"
        )
        log_embed.add_field(
            name = "코드 소유자", value = f"<@{codeOwner.discordId}> ({codeOwner.discordId})"
        )
        await send_discord_log(
            discord_user_id=interaction.user.id,
            embed=log_embed,
            webhook_url=REFERRAL_LOG_WEBHOOK
        )

class RegisterReferralCodeButton(discord.ui.Button):
    def __init__(self, user_data, isReferralEnabled: bool):
        super().__init__(
            label =  "코드 등록하기",
            style = discord.ButtonStyle.green,
            emoji = "🔗"
        )
        self.disabled = isReferralEnabled
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(InputReferralCodeModal(user_data=self.user_data))

class ReferralView(discord.ui.LayoutView):
    def __init__(self, user: User):
        super().__init__()
        container = ReferralContainer(user)
        container.accent_color = 0xffffff
        self.add_item(container)

class ReferralContainer(discord.ui.Container):
    title = discord.ui.TextDisplay("### 🧑‍🤝‍🧑 레퍼럴 코드 확인하기")
    sep1 = discord.ui.Separator()
    subTitle = discord.ui.TextDisplay("### 레퍼럴")
    description = discord.ui.TextDisplay(f"> 누군가 내 레퍼럴 코드를 적용하면, 적용하신 분이 사용한 수수료의 **{REFERRAL_PAYBACK_PERCENT}%가 잔액으로 지급돼요.**")

    def __init__(self, user_data: User):
        super().__init__()

        myReferralCodeDesc = discord.ui.TextDisplay(
            f"내 레퍼럴 코드: `{user_data.referralCode}` (클릭해서 복사하세요!)"
        )

        if user_data.invitedBy:
            isReferralEnabled = True
            # Link가 fetch된 상태인지 확인하고 안전하게 접근
            try:
                invited_by_user = user_data.invitedBy
                referral_code = getattr(invited_by_user, 'referralCode', None)
                discord_id = getattr(invited_by_user, 'discordId', None)
                
                if referral_code and discord_id:
                    discord_mention = f"<@{discord_id}>"
                    desc = f"적용된 레퍼럴 코드: `{referral_code}` ({discord_mention})"
                else:
                    desc = "적용된 레퍼럴 코드: ✅ (적용됨, 상세 정보 로딩 중)"
            except (AttributeError, TypeError):
                desc = "적용된 레퍼럴 코드: ✅ (적용됨, 상세 정보 로딩 중)"
        else:
            isReferralEnabled = False
            desc = "적용된 레퍼럴 코드: ❌ (아직 적용되지 않았어요.)"

        applyedReferralCodeDesc = discord.ui.TextDisplay(desc)

        referralSection = discord.ui.Section(
            applyedReferralCodeDesc,
            accessory=RegisterReferralCodeButton(user_data, isReferralEnabled)
        )

        self.add_item(myReferralCodeDesc)
        self.add_item(referralSection)
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행"))

class ReferralButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(
            label = "초대 · 레퍼럴",
            style = discord.ButtonStyle.primary,
            emoji = "🔗"
        )
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        user =  await Database.get_user_info(self.user_data.discordId, True)

        if not user:
            return
        
        self.user_data = user

        await interaction.response.send_message(
            view = ReferralView(self.user_data),
            ephemeral = True
        )

# --------------------- Address Views ------------------------------ #

class ChangeAddressToShuffle(discord.ui.Button):
    def __init__(self, user: User, address: CryptoAddress):
        super().__init__(
            label="해당 주소를 셔플 주소로 변경하기",
            style=discord.ButtonStyle.primary,
            emoji="💲"
        )
        self.user = user
        self.address = address

    async def callback(self, interaction: discord.Interaction):
        self.address.isShuffleAddress = not self.address.isShuffleAddress
        addressOwner = self.user

        for idx, addr in enumerate(addressOwner.cryptoAddresses):
            if addr.address == self.address.address and addr.network == self.address.network:
                addressOwner.cryptoAddresses[idx] = self.address
                break

        await addressOwner.save()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="수정 완료",
                description="셔플 할인 설정이 변경되었어요.",
                color=0xffffff
            ),
            ephemeral=True
        )

class DeleteSuccessView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        container = DefaultContainer(
            "### 📗 주소록 관리",
            "### 주소록 삭제",
            "해당 주소록 삭제가 완료되었어요."
        )
        container.accent_color = 0xffffff

        self.add_item(container)

class AddressDeleteButton(discord.ui.Button):
    def __init__(self, user: User, address: CryptoAddress):
        self.user = user
        self.address = address
        super().__init__(
            label="주소 삭제하기",
            style=discord.ButtonStyle.red
        )

    async def callback(self, interaction: discord.Interaction):
        await self.user.update(Pull({User.cryptoAddresses: self.address})) # type: ignore[arg-type]
 
        await interaction.response.edit_message(
            view = DeleteSuccessView()
        )

class AddressInfoContainer(discord.ui.Container):
    def __init__(self, user: User, address: CryptoAddress):
        super().__init__()
        title = discord.ui.TextDisplay(
            f"### {get_crypto_by_symbol(address.crypto).get('emoji')} {address.crypto} 주소록 ({address.alias})"
        )

        walletInformation = (
            f"> - **지갑 주소**: {address.address}"
            + (f" (태그: {address.tag})" if address.crypto == "XRP" else "")
            + f"\n> - **지갑 별명**: {address.alias}"
            + f"\n> - **코인 & 네트워크**: {address.crypto} - {address.network}"
            + f"\n> - **셔플 제휴 할인 적용**: {'✅' if address.isShuffleAddress else '❌'}"
        )
        self.add_item(title)
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay("### 주소록 정보"))
        self.add_item(discord.ui.TextDisplay(walletInformation))
        self.add_item(discord.ui.ActionRow(AddressDeleteButton(user, address)))
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행"))
        

class AddressInfoView(discord.ui.LayoutView):
    def __init__(self, user: User, address: CryptoAddress):
        super().__init__()
        container = AddressInfoContainer(user, address)
        container.accent_color = 0xffffff
        self.add_item(container)


class AddressBookSelect(discord.ui.Select):
    addresses: List[CryptoAddress] = []

    def __init__(
        self,
        user: User,
        addresses: Optional[List[CryptoAddress]] = None
    ):
        self.addresses = addresses or []
        super().__init__(
            custom_id="address_book_select",
            placeholder="주소를 선택해주세요.",
            options=self._build_options(self.addresses)
        )
        self.user = user

    def _build_options(self, addresses: List[CryptoAddress]):
        options = []
        if addresses:
            for addr in addresses:
                desc = (
                    f"{addr.crypto} - {addr.network} | "
                    + ("셔플 제휴가 적용 중이에요." if addr.isShuffleAddress else "셔플 제휴가 적용되지 않는 주소에요.")
                )
                options.append(discord.SelectOption(
                    label=addr.alias,
                    value=f"{addr.crypto}|{addr.network}|{addr.address}",
                    description=desc,
                    emoji=get_crypto_by_symbol(addr.crypto).get('emoji')
                ))
        else:
            options.append(discord.SelectOption(
                label="주소록에 등록된 주소가 아직 없어요.",
                value="no_history",
                emoji="❌",
                default=True
            ))
        options.append(discord.SelectOption(
            label="주소 추가하기",
            value="add_address",
            emoji="➕"
        ))
        return options

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]

        if choice == "no_history":
            embed = discord.Embed(
                title="📭 주소록",
                description="등록된 주소가 없어요. 등록 후 이용해주세요.",
                color=0xE74C3C
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if choice == "add_address":
            return await interaction.response.edit_message(view=AddressRegisterView())

        try:
            crypto, network, addr_value = choice.split("|", 2)
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

        return await interaction.response.send_message(
            view=AddressInfoView(self.user, selected),
            ephemeral=True
        )

class AddressBookContainer(discord.ui.Container):
    def __init__(
        self,
        user: User,
        addressbookList: Optional[List[CryptoAddress]] = None
    ):
        super().__init__()
        select = AddressBookSelect(user, addressbookList)
        self.add_item(discord.ui.ActionRow(select))
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행"))

class AddressBookView(discord.ui.LayoutView):
    def __init__(
        self,
        user: User,
        addressbookList: Optional[List[CryptoAddress]] = None
    ):
        super().__init__()
        container = AddressBookContainer(user, addressbookList)
        container.accent_color = 0xffffff
        self.add_item(container)

class AddressBookButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(
            label="편의 · 주소록",
            style=discord.ButtonStyle.green,
            emoji="📝"
        )
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        user = await Database.get_user_info(self.user_data.discordId, True)

        if not user:
            return
        
        self.user_data = user

        await interaction.response.send_message(
            view=AddressBookView(user, user.cryptoAddresses),
            ephemeral=True
        )