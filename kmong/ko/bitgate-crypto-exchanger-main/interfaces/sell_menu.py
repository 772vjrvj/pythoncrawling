import datetime
import traceback
from decimal import Decimal
from typing import List, Literal, Optional

import discord
from beanie import Link
from bson import DBRef
from bson.int64 import Int64

from models.User import KRWAccount, User, CryptoWallet
from modules.database import Database
from modules.kebhana import get_usd_price
from modules.kimp import get_kimp
from modules.log import send_discord_log
from modules.utils import (generate_uuid_log_id, get_crypto_by_symbol,
                           get_env_config, get_bankname_by_bankcode)
                        
config = get_env_config()

class DefaultView(discord.ui.LayoutView):
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

class SellMenuMainContainer(discord.ui.Container):
    def __init__(self, user_data: User):
        title = discord.ui.TextDisplay(f"### 어느 계좌로 매입을 진행하시겠어요?")

        sep1 = discord.ui.Separator()

        description = discord.ui.TextDisplay(f"### 원화를 받으실 계좌를 골라주세요.\n- 만약 등록된 계좌가 없다면, 계좌 등록하기를 눌러주세요.")
        selectRow = discord.ui.ActionRow(KRWAccountSelect(user_data.krwAccounts))

        sep2 = discord.ui.Separator()
        sellSettingsRow = discord.ui.ActionRow() # add setting row (KRWAccount Manage, User's Crypto Wallet Manage.. etc)

        super().__init__(accent_color=0xffffff)

        self.add_item(title)
        self.add_item(sep1)
        self.add_item(description)
        self.add_item(selectRow)
        self.add_item(sep2)
        self.add_item(sellSettingsRow)

class KRWAccountSelect(discord.ui.Select):
    def __init__(self, KRWAccounts: Optional[List[KRWAccount]] = None):
        options = []
        if KRWAccounts:
            for account in KRWAccounts:
                options.append(
                    discord.SelectOption(
                        label=f"{account.alias}",
                        description=f"{get_bankname_by_bankcode(account.bankCode)} {account.accountNumber}",
                        value=f"{account.bankCode}|{account.accountNumber}",
                        emoji="💳"
                    )
                )
        
        else:
            options.append(
                discord.SelectOption(
                    label="계좌 등록하기",
                    value="add_account",
                )
            )
        
        super().__init__(
            custom_id="account_select",
            placeholder="계좌를 선택해주세요.",
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        user_data = await Database.get_user_info(str(interaction.user.id))

        if not user_data:
            await interaction.response.edit_message(
                view=DefaultView("### 매입 진행에 실패했어요", "### 원화 계좌 선택하기", "비정상적인 유저 데이터가 발견되었어요. 관리자에게 문의해주세요.")
            )
            return

        if choice == "add_account":
            return # send account add modal to user
    
        bankCode, accountNumber = choice.split("|")[0], choice.split("|")[1]

        await interaction.response.edit_message(
            view=CryptoWalletSelectView(accountNumber, bankCode, cryptoWallets=user_data.sellingWallets)
        )

class AddKRWAccountModal(discord.ui.Modal):
    def __init__(self, user_data: User):
        super().__init__(title='원화 계좌 등록하기')
        self.user_data = user_data
        
        self.accountNumber = discord.ui.TextInput(label='계좌번호', placeholder="특수문자 없이 숫자만 입력해주세요.")
        self.bankName = discord.ui.TextInput(label='은행 이름', placeholder="토스뱅크, 농협 등 은행의 정확한 이름을 입력해주세요.")
        self.alias = discord.ui.TextInput(label='계좌 별명')
    

class CryptoWalletSelectView(discord.ui.LayoutView):
    def __init__(self, accountNumber: str, bankCode: str, cryptoWallets: Optional[List[CryptoWallet]] = None):
        super().__init__(timeout=None)

        self.add_item(CryptoWalletSelectContainer(accountNumber, bankCode, cryptoWallets))

class CryptoWalletSelectContainer(discord.ui.Container):
    def __init__(self, accountNumber: str, bankCode: str, cryptoWallets: Optional[List[CryptoWallet]] = None):
        super().__init__(
            accent_color=0xffffff
        )
        
        self.add_item(discord.ui.TextDisplay(f"### 어느 지갑으로 매입을 진행하시겠어요?"))
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"### 암호화폐를 송금하신 지갑을 골라주세요."))
        self.add_item(discord.ui.ActionRow(CryptoWalletSelect(accountNumber, bankCode, cryptoWallets)))
        self.add_item(discord.ui.Separator())
        self.add_item(discord.ui.TextDisplay(f"-# 🪙 {config.brand_name} - 24시간 코인송금대행"))
    
class CryptoWalletSelect(discord.ui.Select):
    def __init__(self, accountNumber: str, bankCode: str, cryptoWallets: Optional[List[CryptoWallet]] = None):
        options = []
        self.accountNumber, self.bankCode = accountNumber, bankCode
        self.selectedWallet = None

        if cryptoWallets:
            for wallet in cryptoWallets:
                balance = "0.00" # add fetch
                options.append(
                    discord.SelectOption(
                        label=f"{wallet.crypto} 지갑",
                        description=f"{balance} {wallet.crypto}",
                        value=f"{wallet.publicKey}",
                        emoji=get_crypto_by_symbol(wallet.crypto).get('emoji')
                    )
                )
        
        else:
            # to-do: 생성로직 만들기
            pass
    
    async def callback(self, interaction: discord.Interaction):
        pass
        # TO-DO:
        # self.selectedWallet 변수에 선택한 코인 지갑 할당하기
        # 지갑에 코인 몇개 있는지 확인하고, 없다면 코인 없다고 반환하는 로직 구성
        # 지갑에 코인이 있다면 -> 1. 원화 금액으로 변환 -> 2. 수수료 제외 -> 3. 하나API에 등록된 계좌로 송금 요청