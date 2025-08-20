import asyncio
from decimal import Decimal

import discord
from bson.int64 import Int64

import modules.constants as constants
from modules.constants import DEFAULT_RANK_OBJECT
from modules.database import Database
from modules.log import send_discord_log, send_suspicious_deposit_log
from modules.nh_client import NHChargeClient
from modules.utils import get_env_config

config = get_env_config()

BRAND_NAME = config.brand_name

AUTO_CHARGE_API_KEY = config.auto_charge_api_key

NH_LOGIN_ID = config.nh_login_id
NH_LOGIN_PW = config.nh_login_pw

CHARGE_BANK_CODE = config.charge_bank_code
CHARGE_BANK_NUMBER = config.charge_bank_number

CHARGE_LOG_WEBHOOK = config.charge_log_webhook

SUSPICIOUS_DEPOSIT_LOG_WEBHOOK = config.suspicious_deposit_log_webhook

class DefaultContainer(discord.ui.Container):
    def __init__(self, title: str, sub_title: str, description: str):
        super().__init__()

        title_display = discord.ui.TextDisplay(content=title)
        sub_title_display = discord.ui.TextDisplay(content=sub_title)
        description_display = discord.ui.TextDisplay(content=description)
        footer_display = discord.ui.TextDisplay(content=f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행")

        self.add_item(title_display)

        self.add_item(discord.ui.Separator())

        self.add_item(sub_title_display)
        self.add_item(description_display)

        self.add_item(discord.ui.Separator())

        self.add_item(footer_display)

class DefaultView(discord.ui.LayoutView):
    def __init__(self, title: str, sub_title: str, description: str):
        super().__init__()

        container = DefaultContainer(title, sub_title, description)
        container.accent_color = 0xffffff

        self.add_item(container)

class ChargePendingView(discord.ui.LayoutView):
    def __init__(self, amount: int, senderName: str):
        super().__init__()
        container = ChargePendingContainer(amount, senderName)
        container.accent_color = 0xffffff
        self.add_item(container)

class ChargePendingContainer(discord.ui.Container):
    title = discord.ui.TextDisplay(f"### ⏳ 입금 대기 중")
    sep1 = discord.ui.Separator()
    sub_title = discord.ui.TextDisplay(f"### 잔액 충전")

    def __init__(self, amount: int, senderName: str):
        super().__init__()

        warning_text = discord.ui.TextDisplay(
        """
        - 충전하실 때 지키셔야 할 사항이에요.
        1. **입금자명**을 꼭 **변경 없이, 인증한 실명으로** 입금해주세요.
        2. 입금 최대 대기 시간은 **3분**이에요. 시간이 지난 이후에는, **입금하셔도 충전되지 않아요.**
        """
        )

        bank_account_text = discord.ui.TextDisplay(
            f"입금 계좌번호: `{constants.BANK_CODE_MAPPING.get(CHARGE_BANK_CODE)} {CHARGE_BANK_NUMBER}`"
        )
        amount_text = discord.ui.TextDisplay(
            f"입금하실 금액: `{amount:,}`원"
        )
        sender_name_text = discord.ui.TextDisplay(
            f"입금자 이름: `{senderName}`"
        )

        footer = discord.ui.TextDisplay(f"-# 🪙 {BRAND_NAME} - 24시간 코인송금대행")

        self.add_item(warning_text)

        self.add_item(bank_account_text)
        self.add_item(amount_text)
        self.add_item(sender_name_text)
        
        self.add_item(discord.ui.Separator())
        self.add_item(footer)

class ChargeAmountModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title = "충전 금액 입력하기")

        self.chargeAmount = discord.ui.TextInput(
            label = "충전 금액 (KRW)",
            placeholder = "숫자만 입력해주세요."
        )

        self.add_item(self.chargeAmount)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        raw_value = self.chargeAmount.value.strip()

        if not raw_value.isdigit() or int(raw_value) <= 0:
            return await interaction.response.send_message(
                view = DefaultView("### ❌ 충전 요청에 실패했어요", "### 잔액 충전", "질못된 값이에요. 0보다 큰 정수만 입력해주세요."),
                ephemeral = True
            )

        chargeAmount = int(raw_value)

        is_over_limit = await Database.is_user_over_charge_limit(
            str(interaction.user.id), Int64(chargeAmount)
        )
        if is_over_limit:
            return await interaction.response.send_message(
                view = DefaultView("### ❌ 충전 요청에 실패했어요", "### 잔액 충전", "일일 충전 한도 이상으로 충전하실 수 없어요.\n한도를 늘리고 싶으시다면, 관리자에게 문의해주세요."),
                ephemeral = True
            )

        await interaction.response.send_message(
            view = DefaultView("### ⏳ 충전 요청을 처리하는 중이에요", "### 잔액 충전", "서버와 통신하고 있어요. 잠시만 기다려주세요."),
            ephemeral = True
        )

        user = await Database.get_user_info(str(interaction.user.id))

        if not user or not user.verificationData:
            return
        
        sender_name = user.verificationData.name

        client = NHChargeClient(AUTO_CHARGE_API_KEY)
        chargeResponse = await client.requestCharge(
            chargeAmount,
            sender_name,
            {"bankCode": CHARGE_BANK_CODE, "number": CHARGE_BANK_NUMBER},
            {"id": NH_LOGIN_ID, "password": NH_LOGIN_PW}
        )

        if not chargeResponse["success"]:
            return await interaction.edit_original_response(
                view = DefaultView("### ❌ 충전 요청에 실패했어요", "### 잔액 충전", f"{chargeResponse['message']}\n\n-# 다시 시도해도 오류가 발생한다면, 문의해주세요.")
            )

        await interaction.edit_original_response(
            view = ChargePendingView(chargeAmount, sender_name)
        )

        log_embed = discord.Embed(
            title = "⌛ 신규 충전 신청이 접수되었어요",
            description = f"{interaction.user.mention}님이 신규 충전을 신청했어요.",
            color = 0xffffff
        )
        log_embed.add_field(
            name = "입금자명", value = sender_name
        )
        log_embed.add_field(
            name = "충전 금액", value = f"{chargeAmount:,}원"
        )
        log_embed.add_field(
            name = "작업 ID", value = f"`{client.taskId}`"
        )
        await send_discord_log(
            discord_user_id=interaction.user.id,
            embed=log_embed,
            webhook_url=CHARGE_LOG_WEBHOOK
        )

        asyncio.create_task(send_suspicious_deposit_log(chargeResponse["newSuspiciousDeposits"]))

        chargeLog = await Database.create_charge_log(str(interaction.user.id), Int64(chargeAmount), sender_name)

        if not chargeLog:
            await client.deleteTask()
            return

        checkResult = await client.checkStatus(2, 300)

        await client.deleteTask()

        if not checkResult["success"]:
            log_embed = discord.Embed(
                title = "❌ 충전 실패",
                description = f"{interaction.user.mention}님이 충전에 실패했어요.\n사용자가 보는 메시지: \n```\n{checkResult['message']}\n```",
                color = discord.Color.red()
            )
            log_embed.add_field(
                name = "입금자명",
                value = sender_name
            )
            log_embed.add_field(
                name = "충전 요청 금액",
                value = f"{chargeAmount:,}원"
            )
            log_embed.add_field(
                name = "작업 ID",
                value = f"`{client.taskId}`"
            )
            
            await send_discord_log(
                discord_user_id=interaction.user.id,
                embed=log_embed,
                webhook_url=CHARGE_LOG_WEBHOOK
            )

            await Database.change_charge_status(chargeLog, False)

            return await interaction.edit_original_response(
                view = DefaultView("### ❌ 충전에 실패했어요", "### 잔액 충전", checkResult["message"])
            )

        asyncio.create_task(send_suspicious_deposit_log(checkResult["newSuspiciousDeposits"]))

        feeResult = Database.calc_fee(chargeAmount, Decimal(DEFAULT_RANK_OBJECT.get('cryptoPurchasingFee')))
        fee = int(feeResult['fee'])

        # edit user balance
        await Database.edit_user_balances(str(interaction.user.id), Int64(chargeAmount))
        await Database.update_user_total_charge(str(interaction.user.id), Int64(chargeAmount))
        result = await Database.pay_referral_payback(str(interaction.user.id), Int64(fee))
        referral_owner, referral_payback_amt = result if result is not None else (None, None)

        # upgrade user role
        rank = await Database.get_user_rank(str(interaction.user.id))
        if rank and rank.discordRoleId and rank.discordRoleId.isdigit():
            try:
                role = await interaction.guild.fetch_role(int(rank.discordRoleId))
                if isinstance(interaction.user, discord.Member):
                    await interaction.user.add_roles(role)
                else:
                    # fallback to fetching the member from the guild
                    member = await interaction.guild.fetch_member(interaction.user.id)
                    await member.add_roles(role)
            except Exception as e:
                print(f"Failed to add role {rank.discordRoleId} to user {interaction.user.id}: {e}")
                pass

        log_embed = discord.Embed(
            title = "✅ 충전 성공",
            description = f"{interaction.user.mention}님이 충전에 성공했어요.",
            color = 0xffffff
        )
        log_embed.add_field(
            name = "입금자명",
            value = sender_name
        )
        log_embed.add_field(
            name = "충전 금액",
            value = f"{chargeAmount:,}원"
        )
        log_embed.add_field(
            name = "입금 시각",
            value = f"<t:{int(int(checkResult['transaction']['date']) / 1000)}:F>"
        )
        log_embed.add_field(
            name = "레퍼럴 페이백 정보",
            value = f"{referral_payback_amt} -> {referral_owner.discordId}" if referral_owner and referral_payback_amt else "적용된 레퍼럴 코드 없음"
        )

        log_embed.set_footer(text=f"TxID: {checkResult['transaction']['id']}")

        await send_discord_log(
            discord_user_id=interaction.user.id,
            embed=log_embed,
            webhook_url=CHARGE_LOG_WEBHOOK
        )

        await Database.change_charge_status(chargeLog, True, checkResult["transaction"]["id"], Int64(Int64(checkResult["transaction"]["date"]) / Int64(1000)))

        await interaction.edit_original_response(
            view = DefaultView("### ✅ 충전에 성공했어요", "### 잔액 충전", f"`{chargeAmount:,}`원 충전에 성공했어요.")
        )