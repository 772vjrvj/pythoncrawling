import datetime
import os
import traceback

import discord
import dotenv
from discord import ButtonStyle, ui

from interfaces.charge_menu import ChargeAmountModal
from interfaces.fee_calculator import InputKRWAmountModal
from interfaces.identity_verification_menu import SelectCarrierView
from interfaces.user_management_menu import InfoMainView, UserMenuMainContainer
from interfaces.withdraw_menu import SelectCoin
from modules.binance import Binance, BinanceError, NetworkError
from modules.database import Database
from modules.log import send_discord_log
from modules.utils import generate_uuid_log_id, get_env_config

config = get_env_config()

ERROR_LOG_WEBHOOK = config.error_log_webhook

class ChargeButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="충전하기",
            style=ButtonStyle.success,
            custom_id="charge_button"
        )

    async def callback(self, interaction: discord.Interaction):
        now = datetime.datetime.now()
        now_time = now.time()

        if (now_time >= datetime.time(23, 50)) or (now_time < datetime.time(0, 20)):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⚠️ 점검 안내",
                    description="23:50부터 00:20까지는 은행 점검으로 인해 충전이 불가능해요.\n잠시 후 다시 시도해주세요.",
                    color=0xFFCC00
                ),
                ephemeral=True
            )

        user_data = await Database.get_user_info(str(interaction.user.id))
        if not user_data:
            return await interaction.response.send_message(
                view=SelectCarrierView(),
                ephemeral=True
            )

        await interaction.response.send_modal(ChargeAmountModal())

class PurchaseButton(ui.Button):
    def __init__(self):
        super().__init__(label="구매하기", style=discord.ButtonStyle.primary, custom_id="purchase_button")

    async def callback(self, interaction: discord.Interaction):
        user_data = await Database.get_user_info(str(interaction.user.id))
    
        if not user_data:
            await interaction.response.send_message(
                view=SelectCarrierView(),
                ephemeral=True
            )
            return None

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            view = SelectCoin(Binance())
            await view.create(interaction)
        except NetworkError as e:
            await interaction.followup.send(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=ERROR_LOG_WEBHOOK
            )
            return
        except BinanceError as e:
            await interaction.followup.send(e.user_msg, ephemeral=True)
            await send_discord_log(
                discord_user_id=interaction.user.id,
                content=e.admin_msg,
                level="ERROR",
                webhook_url=ERROR_LOG_WEBHOOK
            )
            return
        except Exception:
            tb = traceback.format_exc()
            log_id = generate_uuid_log_id()

            user_embed = discord.Embed(
                title="❌ 알 수 없는 오류",
                description=f"알 수 없는 오류가 발생했어요. 관리자에게 문의해주세요.\n로그 ID: `{log_id}`",
                color=0xE74C3C
            ).set_footer(text="문의 시 로그 ID를 알려주세요")

            await interaction.followup.send(embed=user_embed, ephemeral=True)

            admin_embed = discord.Embed(
                title="🚨 [PurchaseButton] Unexpected Error",
                description=f"로그 ID: `{log_id}`",
                color=0xE74C3C
            )
            admin_embed.add_field(name="User", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
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
            admin_embed.add_field(name="Stack Trace", value=f"```\n" + (tb if len(tb) <= 1000 else tb[:1000] + "\n... (truncated)") + "\n```", inline=False)

            await send_discord_log(
                embed=admin_embed,
                webhook_url=ERROR_LOG_WEBHOOK
            )

            return
        await interaction.followup.send(view=view)

class SellButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="판매하기",
            style=ButtonStyle.primary,
            custom_id="sell_button"
        )

    async def callback(self, interaction: discord.Interaction):
        user_data = await Database.get_user_info(str(interaction.user.id))
    
        if not user_data:
            await interaction.response.send_message(
                view=SelectCarrierView(),
                ephemeral=True
            )
            return None

        userKRWAccList = []

class InfoButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="내 정보", 
            style=ButtonStyle.secondary,
            custom_id="info_button"
        )

    async def callback(self, interaction: discord.Interaction):
        user_data = await Database.get_user_info(str(interaction.user.id))
    
        if not user_data:
            await interaction.response.send_message(
                view=SelectCarrierView(),
                ephemeral=True
            )
            return None

        userRank = await Database.get_user_rank(user_data.discordId)
        transactions = await Database.get_recent_crypto_transactions(user_data.discordId)

        conatiner = UserMenuMainContainer(user_data, userRank, transactions)

        await interaction.response.send_message(
            view = InfoMainView(conatiner),
            ephemeral = True
        )

class CalcuateKRWFeeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="KRW (₩)", style=discord.ButtonStyle.green, custom_id="KRWCalcButton")

    async def callback(self, interaction: discord.Interaction):
        user_data = await Database.get_user_info(str(interaction.user.id))
    
        if not user_data:
            await interaction.response.send_message(
                view=SelectCarrierView(),
                ephemeral=True
            )
            return None
        
        await interaction.response.send_modal(InputKRWAmountModal())