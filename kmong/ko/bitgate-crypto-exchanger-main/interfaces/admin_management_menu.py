import traceback
from typing import List, Optional

import discord
from bson.int64 import Int64
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


class InfoMainView(discord.ui.LayoutView):
    def __init__(self, container):
        super().__init__()
        container.accent_color = 0xffffff
        self.add_item(container)

class AdminMenuMainContainer(discord.ui.Container):
    def __init__(self, user_data: User, default_rank: Rank, recentTransactions: Optional[List[CryptoTransaction]] = None):
        super().__init__()
        
        title = discord.ui.TextDisplay(f"### 👤 {user_data.verificationData.name if user_data.verificationData else 'UNKNOWN'}님의 정보 (Admin Inspect)")
        
        sep1 = discord.ui.Separator()
       
        balanceText = discord.ui.TextDisplay(f"- 사용 가능 잔액\n> **{user_data.balances.KRW:,}원**")
        usedText = discord.ui.TextDisplay(f"- 누적 사용 금액\n> **{user_data.statistics.totalKRWCharge:,}원**")
        feeText = discord.ui.TextDisplay(f"- 적용된 수수료\n> 구매: **{default_rank.cryptoPurchasingFee}%**, 매입: **{default_rank.cryptoSellingFee}%**")
        limitText = discord.ui.TextDisplay(f"- 일일 원화 한도\n> 충전: **{user_data.limits.dailyChargeLimit:,}원**, 매입: **{user_data.limits.dailySellingLimit:,}원**")

        sep2 = discord.ui.Separator()
        
        recentTransactionRow = discord.ui.ActionRow(RecentTransactionSelect(recentTransactions))
        
        sep3 = discord.ui.Separator()
        
        utilRow = discord.ui.ActionRow(
            ReferralButton(user_data=user_data),
            AddressBookButton(user_data=user_data),
            EditLimitationButton(user_data=user_data),
            RevealUserIdentityInfoButton(user_data=user_data)
        )
        
        for item in (title, sep1, usedText, balanceText, feeText, limitText, sep2, recentTransactionRow, sep3, utilRow):
            self.add_item(item)
        
        self.add_item(discord.ui.ActionRow(
            editBalanceButton(user_data),
            editBalanceButton2(user_data)
        ))

class editBalanceModal(discord.ui.Modal):
    def __init__(self, user: User):
        super().__init__(title='잔액 추가하기')
        self.user = user
        self.balance = discord.ui.TextInput(label='금액 (누적 금액에도 똑같이 반영됩니다.)', placeholder='10000 / -10000')
        self.add_item(self.balance)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.balance.value.replace('.', '').replace('-', '').isnumeric():
            return await interaction.response.send_message(
                embed=discord.Embed(title='❌ 실패', description='잘못된 숫자에요.', color=0xffffff),
                ephemeral=True
            )
        bf_balance = self.user.balances.KRW
        bf_total = self.user.statistics.totalKRWCharge
        await self.user.update({
            '$inc': {
                'balances.KRW': Int64(self.balance.value),
                'statistics.totalKRWCharge': Int64(self.balance.value)
            }
        })
        await interaction.response.send_message(
            embed=discord.Embed(
                title='변경 사항이 저장되었어요',
                description=(
                    f'변경 전 잔액: `{bf_balance:,}`원\n'
                    f'변경 후 잔액: `{self.user.balances.KRW:,}`원\n\n'
                    f'변경 전 누적 충전 금액: `{bf_total:,}`원\n'
                    f'변경 후 누적 충전 금액: `{self.user.statistics.totalKRWCharge:,}`원'
                ),
                color=0xffffff
            ),
            ephemeral=True
        )

class editBalanceModal2(discord.ui.Modal):
    def __init__(self, user: User):
        super().__init__(title='잔액 수정하기')
        self.user = user
        self.balance = discord.ui.TextInput(label='사용 가능 잔액', placeholder='10000', default=str(self.user.balances.KRW))
        self.totalCharge = discord.ui.TextInput(label='누적 충전 금액', placeholder='10000', default=str(self.user.statistics.totalKRWCharge))
        self.add_item(self.balance)
        self.add_item(self.totalCharge)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.balance.value.replace('.', '').replace('-', '').isnumeric() or not self.totalCharge.value.replace('.', '').replace('-', '').isnumeric():
            return await interaction.response.send_message(
                embed=discord.Embed(title='❌ 실패', description='잘못된 숫자에요.', color=0xffffff),
                ephemeral=True
            )
        bf_balance = self.user.balances.KRW
        bf_total = self.user.statistics.totalKRWCharge
        await self.user.update({
            '$set': {
                'balances.KRW': Int64(self.balance.value),
                'statistics.totalKRWCharge': Int64(self.totalCharge.value)
            }
        })
        await interaction.response.send_message(
            embed=discord.Embed(
                title='변경 사항이 저장되었어요',
                description=(
                    f'변경 전 잔액: `{bf_balance:,}`원\n'
                    f'변경 후 잔액: `{self.user.balances.KRW:,}`원\n\n'
                    f'변경 전 누적 충전 금액: `{bf_total:,}`원\n'
                    f'변경 후 누적 충전 금액: `{self.user.statistics.totalKRWCharge:,}`원'
                ),
                color=0xffffff
            ),
            ephemeral=True
        )

class editBalanceButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='잔액 수정 (추천)', style=discord.ButtonStyle.primary, emoji='🪙')
        self.user = user_data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(editBalanceModal(self.user))

class editBalanceButton2(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='잔액 직접 수정 (위험)', style=discord.ButtonStyle.danger, emoji='🪙')
        self.user = user_data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(editBalanceModal2(self.user))

class RecentTransactionSelect(ui.Select):
    def __init__(self, transactions: Optional[List[CryptoTransaction]] = None):
        options = []
        
        if transactions:
            for tx in transactions:
                options.append(
                    discord.SelectOption(
                        label=f'{tx.address}',
                        description=f'{tx.amountCrypto} {tx.cryptoSymbol} ({tx.networkName}) | {tx.createdAt}',
                        value=tx.binanceWithdrawalId,
                        emoji=get_crypto_by_symbol(tx.cryptoSymbol).get('emoji')
                    )
                )
        
        else:
            options.append(discord.SelectOption(label='최근 거래 내역이 존재하지 않아요.', value='no_history', default=True))
        
        super().__init__(custom_id='RecentTransactionSelect', placeholder='최근 거래 내역', options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        if choice == 'no_history':
            return
        try:
            info = await Binance().get_withdrawal_info(choice)
        
        except (NetworkError, BinanceError) as e:
            await interaction.response.send_message(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level='ERROR',
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
            channel_name = getattr(channel, "name", "DM")
            channel_id = getattr(channel, "id", "N/A")
            admin_embed.add_field(
                name="Channel",
                value=f"{channel_name} (`{channel_id}`)",
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
                content=None,
                webhook_url=ERROR_LOG_WEBHOOK
            )
            
            return
        
        embed = discord.Embed(title='출금 정보 조회하기', description='> 출금하신 정보를 조회하실 수 있어요.', color=0x00FF00)
        
        embed.add_field(name='지갑 주소', value=info.get('address', '—'))
        embed.add_field(name='코인/체인', value=f"{info.get('coin','—')} ({info.get('network','—')})")
        embed.add_field(name='수량', value=f"{info.get('amount','—')} {info.get('coin','—')}")
        embed.add_field(name='TxID', value=info.get('txId','—'))
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ReferralSuccessRegister(discord.ui.Container):
    title = discord.ui.TextDisplay('### ✅ 레퍼럴 코드 등록에 성공했어요 (관리자)')
    sep1 = discord.ui.Separator()
    subTitle = discord.ui.TextDisplay('### 레퍼럴 코드 등록 (관리자)')

    def __init__(self, referralCode: str, codeOwner: User):
        super().__init__()
        desc = f"`{referralCode}` 코드가 사용자에게 적용되었어요. (코드 주인: <@{codeOwner.discordId}>)"
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
        super().__init__(title='레퍼럴 코드 등록하기')
        self.user_data = user_data
        self.referralCode = discord.ui.TextInput(label='레퍼럴 코드', placeholder='24735BE03A58', min_length=12, max_length=12)
        self.add_item(self.referralCode)

    async def on_submit(self, interaction: discord.Interaction):
        codeOwner = await Database.get_referral_owner(self.referralCode.value)
        if not codeOwner:
            return await interaction.response.send_message(
                embed=discord.Embed(title='❌ 레퍼럴 등록에 실패했어요', description='존재하지 않는 레퍼럴 코드예요.', color=0xffffff),
                ephemeral=True
            )
        if str(self.user_data.id) == str(codeOwner.id):
            return await interaction.response.send_message(
                embed=discord.Embed(title='❌ 레퍼럴 등록에 실패했어요', description='해당 사용자의 자신의 레퍼럴 코드는 등록할 수 없어요.', color=0xffffff),
                ephemeral=True
            )
        await self.user_data.update({'$set': {'invitedBy': codeOwner}})
        await interaction.response.send_message(view=ReferralSuccessView(self.referralCode.value, codeOwner), ephemeral=True)
        
        log_embed = discord.Embed(title='🔗 레퍼럴이 활성화되었어요 (관리자 등록)', color=0xffffff)
        log_embed.add_field(name='적용된 유저', value=f"<@{self.user_data.discordId}> ({self.user_data.discordId})")
        log_embed.add_field(name='적용된 코드', value=f"`{self.referralCode.value}`")
        log_embed.add_field(name='코드 소유자', value=f"<@{codeOwner.discordId}> ({codeOwner.discordId})")
        await send_discord_log(
discord_user_id=interaction.user.id,
            embed=log_embed,
            webhook_url=REFERRAL_LOG_WEBHOOK
        )

class RegisterReferralCodeButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='해당 사용자로 코드 등록하기 (관리자)', style=discord.ButtonStyle.green, emoji='🔗')
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(InputReferralCodeModal(self.user_data))

class ReferralView(discord.ui.LayoutView):
    def __init__(self, user: User):
        super().__init__()
        container = ReferralContainer(user)
        container.accent_color = 0xffffff
        self.add_item(container)

class ReferralContainer(discord.ui.Container):
    title = discord.ui.TextDisplay('### 🧑‍🤝‍🧑 레퍼럴 코드 확인하기')
    sep1 = discord.ui.Separator()
    subTitle = discord.ui.TextDisplay('### 레퍼럴')

    def __init__(self, user_data: User):
        super().__init__()
        myReferralCodeDesc = discord.ui.TextDisplay(f"해당 유저의 레퍼럴 코드: `{user_data.referralCode}`")

        if user_data.invitedBy:
            # Link가 fetch된 상태인지 확인하고 안전하게 접근
            try:
                # Link가 fetch된 상태라면 실제 User 객체로 접근 가능
                invited_by_user = user_data.invitedBy
                referral_code = getattr(invited_by_user, 'referralCode', None)
                discord_id = getattr(invited_by_user, 'discordId', None)
                
                if referral_code and discord_id:
                    discord_mention = f"<@{discord_id}>"
                    desc = f"적용된 레퍼럴 코드: `{referral_code}` ({discord_mention})"
                else:
                    desc = "적용된 레퍼럴 코드: ✅ (적용됨, 상세 정보 로딩 중)"
            except (AttributeError, TypeError):
                # Link가 fetch되지 않은 상태
                desc = "적용된 레퍼럴 코드: ✅ (적용됨, 상세 정보 로딩 중)"
        else:
            desc = "적용된 레퍼럴 코드: ❌ (아직 적용되지 않았어요.)"
        applyedReferralCodeDesc = discord.ui.TextDisplay(desc)
        self.add_item(myReferralCodeDesc)
        self.add_item(discord.ui.Section(applyedReferralCodeDesc, accessory=RegisterReferralCodeButton(user_data)))
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행"))

class ReferralButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='사용자 레퍼럴 관리', style=discord.ButtonStyle.secondary, emoji='🔗')
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        user = await Database.get_user_info(self.user_data.discordId, True)

        if user == None:
            await interaction.response.send_message(
                #view = 
            )
            return

        await interaction.response.send_message(view=ReferralView(user), ephemeral=True)

class ChangeAddressToShuffle(discord.ui.Button):
    def __init__(self, user: User, address: CryptoAddress):
        super().__init__(label='해당 주소를 셔플 주소로 변경하기', style=discord.ButtonStyle.primary, emoji='💲')
        self.user = user
        self.address = address

    async def callback(self, interaction: discord.Interaction):
        self.address.isShuffleAddress = not self.address.isShuffleAddress
        for idx, addr in enumerate(self.user.cryptoAddresses):
            if addr.address == self.address.address and addr.network == self.address.network:
                self.user.cryptoAddresses[idx] = self.address
                break
        await self.user.save()
        await interaction.response.send_message(
            embed=discord.Embed(title='수정 완료', description='셔플 할인 설정이 변경되었어요.', color=0xffffff),
            ephemeral=True
        )

class DeleteSuccessView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        container = DefaultContainer('### 📗 주소록 관리', '### 주소록 삭제', '해당 주소록 삭제가 완료되었어요.')
        container.accent_color = 0xffffff
        self.add_item(container)

class AddressDeleteButton(discord.ui.Button):
    def __init__(self, user: User, address: CryptoAddress):
        super().__init__(label='주소 삭제하기', style=discord.ButtonStyle.red)
        self.user = user
        self.address = address

    async def callback(self, interaction: discord.Interaction):
        await self.user.update({'$pull': {'cryptoAddresses': self.address}})
        await interaction.response.edit_message(view=DeleteSuccessView())

class AddressInfoContainer(discord.ui.Container):
    def __init__(self, user: User, address: CryptoAddress):
        super().__init__()
        title = discord.ui.TextDisplay(f"### {get_crypto_by_symbol(address.crypto).get('emoji')} {address.crypto} 주소록 ({address.alias})")
        walletInformation = (
            f"> - **지갑 주소**: {address.address}"
            + (f" (태그: {address.tag})" if address.crypto == 'XRP' else '')
            + f"\n> - **지갑 별명**: {address.alias}"
            + f"\n> - **코인 & 네트워크**: {address.crypto} - {address.network}"
            + f"\n> - **셔플 제휴 할인 적용**: {'✅' if address.isShuffleAddress else '❌'}"
        )
        self.add_item(title)
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay('### 주소록 정보'))
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
        self.add_item(discord.ui.ActionRow(ChangeAddressToShuffle(user, address)))

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
                options.append(discord.SelectOption(
                    label=addr.alias,
                    value=f"{addr.crypto}|{addr.network}|{addr.address}",
                    description=f"{addr.crypto} - {addr.network} | {'셔플 제휴가 적용 중이에요.' if addr.isShuffleAddress else '셔플 제휴가 적용되지 않는 주소에요.'}",
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
    def __init__(self, user: User, addressbookList: Optional[List[CryptoAddress]] = None):
        super().__init__()
        select = AddressBookSelect(user, addressbookList)
        self.add_item(discord.ui.ActionRow(select))
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행"))

class AddressBookView(discord.ui.LayoutView):
    def __init__(self, user: User, addressbookList: Optional[List[CryptoAddress]] = None):
        super().__init__()
        container = AddressBookContainer(user, addressbookList)
        container.accent_color = 0xffffff
        self.add_item(container)

class AddressBookButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='사용자 주소록 관리', style=discord.ButtonStyle.green, emoji='📝')
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        user = await Database.get_user_info(self.user_data.discordId, True)
        
        if not user:
            return
        
        self.user_data = user
        
        await interaction.response.send_message(view=AddressBookView(user, user.cryptoAddresses), ephemeral=True)

# ---------------------------- Limit Section ---------------------------- #
class EditLimitationButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='일일 충전 한도 설정', style=discord.ButtonStyle.green, emoji='📝')
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        user = await Database.get_user_info(self.user_data.discordId, True)
        
        if not user:
            return
        
        self.user_data = user

        await interaction.response.send_modal(EditLimitModal(user))

class EditLimitModal(discord.ui.Modal):
    def __init__(self, user_data: User):
        super().__init__(title="한도 설정하기 (관리자)")
        self.user_data = user_data

        self.dailyPurchaseLimit = discord.ui.TextInput(
                label = "일일 충전 한도",
                default = user_data.limits.dailyChargeLimit.__str__(),
                placeholder = "숫자만 입력해주세요."
            )
        self.dailySellingLimit = discord.ui.TextInput(
                label = "일일 매입 한도",
                default = user_data.limits.dailySellingLimit.__str__(),
                placeholder = "숫자만 입력해주세요."
            )
        
        self.add_item(self.dailyPurchaseLimit)
        self.add_item(self.dailySellingLimit)

    async def on_submit(self, interaction: discord.Interaction):
        dailyPurchaseLimit, dailySellingLimit = self.dailyPurchaseLimit.value, self.dailySellingLimit.value

        if not dailyPurchaseLimit.isdigit() or not dailySellingLimit.isdigit():
            return await interaction.response.send_message(
                embed = discord.Embed(
                    title = "❌ 한도 변경 실패",
                    description = "숫자만 입력해주세요.",
                    color = 0xffffff
                ), ephemeral=True
            )

        dailyPurchaseLimit, dailySellingLimit = Int64(dailyPurchaseLimit), Int64(dailySellingLimit)
        await Database.edit_user_charge_limit(self.user_data.discordId, dailyPurchaseLimit, dailySellingLimit)

        user = await Database.get_user_info(self.user_data.discordId, True)
        
        if not user:
            return
        
        self.user_data = user

        await interaction.response.send_message(
            view = EditLimitSuccessView(self.user_data),
            ephemeral = True
        )

class EditLimitSuccessView(discord.ui.LayoutView):
    def __init__(self, user_data: User):
        super().__init__()
        self.user_data = user_data
        container = DefaultContainer(
            "### ✅ 한도 변경 성공",
            "### 한도 변경하기",
            f"> 해당 유저의 일일 충전 한도가 `{user_data.limits.dailyChargeLimit:,}`원, 일일 매입 한도가 `{user_data.limits.dailySellingLimit:,}`원 으로 설정되었어요."
        )
        container.accent_color = 0xffffff

        self.add_item(container)

class RevealUserIdentityInfoButton(discord.ui.Button):
    def __init__(self, user_data: User):
        super().__init__(label='사용자 인증 정보 보기', style=discord.ButtonStyle.secondary, emoji='🪪')
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        user = await Database.get_user_info(self.user_data.discordId, True)
        
        if not user:
            return
        
        self.user_data = user

        if not self.user_data.verificationData:
            return await interaction.response.send_message(
                embed = discord.Embed(
                title = "❌ 조회 실패",
                    description = "봇에 가입이 완료된 유저만 조회하실 수 있어요.",
                    color = 0xffffff
                ), ephemeral = True
            )

        embed = discord.Embed(
            title = "사용자 인증 정보",
            color = 0xffffff
        )
        embed.add_field(name = "이름", value = self.user_data.verificationData.name)
        embed.add_field(name = "생년월일", value = str(self.user_data.verificationData.birthdate).split(" ")[0])
        embed.add_field(name = "전화번호", value = self.user_data.verificationData.phone)
        embed.add_field(name = "성별", value = self.user_data.verificationData.gender)
        embed.add_field(name = "통신사", value = self.user_data.verificationData.carrier)
        embed.add_field(name = "CI", value = self.user_data.verificationData.ci[:11] + "...")

        await interaction.response.send_message(embed = embed, ephemeral = True)