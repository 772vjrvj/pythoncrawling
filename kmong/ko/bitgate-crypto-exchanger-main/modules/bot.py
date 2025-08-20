import traceback
from typing import List

import discord
from discord.ext import commands

from interfaces.user_startup_menu import VendingView
from modules.log import send_webhook_log
from modules.utils import get_env_config

config = get_env_config()

ERROR_LOG_WEBHOOK = config.error_log_webhook

VENDING_MAIN_CONTAINER_CHANNEL_ID = config.vending_main_container_channel_id
VENDING_MAIN_CONTAINER_MESSAGE_ID = config.vending_main_container_message_id

NH_LOGIN_ID = config.nh_login_id
NH_LOGIN_PW = config.nh_login_pw

CHARGE_BANK_CODE = config.charge_bank_code
CHARGE_BANK_NUMBER = config.charge_bank_number

AUTO_CHARGE_API_KEY = config.auto_charge_api_key

class CryptoExchangeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('!@#$'), intents=discord.Intents.all())
        self.panel_messages: List[discord.Message] = []

    async def setup_hook(self):
        self.add_view(VendingView())

        for ext in ("cogs.commands", "cogs.context_menus", "cogs.background_loops"):
            await self.load_extension(ext)
        await self.tree.sync()
        print("✅ All commands are synced.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id if self.user else 'None'})")
        try:
            channel = await self.fetch_channel(int(VENDING_MAIN_CONTAINER_CHANNEL_ID))
            if not isinstance(channel, discord.TextChannel):
                raise Exception("패널 메시지 수정은 길드의 일반 텍스트 채널에서만 실행할 수 있어요.")
            message = await channel.fetch_message(int(VENDING_MAIN_CONTAINER_MESSAGE_ID))
        except Exception as e:
            print("메시지 수정 초기화 도중 오류 발생: ", e)
            return
        self.panel_messages.append(message)
        print("Initialized message updater.")

    async def on_error(self, event, *args, **kwargs):
        error_info = traceback.format_exc()
        if error_info:
            send_webhook_log(ERROR_LOG_WEBHOOK, f"[discord.py on_error] 이벤트: {event}\n```python\n{error_info}\n```")

    async def on_command_error(self, ctx, error):
        tb_str = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        send_webhook_log(
            ERROR_LOG_WEBHOOK,
            f"[discord.py on_command_error]\n명령어: {getattr(ctx, 'command', None)}\n"
            f"사용자: {getattr(ctx.author, 'id', None)}\n"
            f"채널: {getattr(ctx.channel, 'id', None)}\n"
            f"```python\n{tb_str}\n```"
        )

    async def on_app_command_error(self, inter, error):
        tb_str = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        send_webhook_log(
            ERROR_LOG_WEBHOOK,
            f"[discord.py on_app_command_error]\n명령어: {getattr(inter, 'command', None)}\n"
            f"사용자: {getattr(inter.user, 'id', None)}\n"
            f"채널: {getattr(inter.channel, 'id', None)}\n"
            f"```python\n{tb_str}\n```"
        )
