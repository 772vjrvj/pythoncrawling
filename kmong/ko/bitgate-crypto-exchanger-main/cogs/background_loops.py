import random

from discord.ext import commands, tasks

from interfaces.user_startup_menu import VendingView
from modules.bot import CryptoExchangeBot
from modules.log import send_suspicious_deposit_log
from modules.nh_client import NHChargeClient
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

class TaskCog(commands.Cog):
    def __init__(self, bot: CryptoExchangeBot):
        self.bot = bot
        self.deposit_monitor.start()
        self.panel_message_editor.start()

    @tasks.loop(minutes=5)
    async def deposit_monitor(self):
        try:
            client = NHChargeClient(AUTO_CHARGE_API_KEY)
            resp = await client.requestCharge(
                random.randint(1, 1_000_000),
                str(random.randint(1, 100_000)),
                {"bankCode": CHARGE_BANK_CODE, "number": CHARGE_BANK_NUMBER},
                {"id": NH_LOGIN_ID, "password": NH_LOGIN_PW}
            )

            if not resp.get("success"):
                print("충전 요청 실패:", resp.get("message"))
                return

            await client.deleteTask()

            await send_suspicious_deposit_log(resp["newSuspiciousDeposits"])
        except Exception as e:
            print("수상한 입금 목록을 가져오는 중 오류가 발생함:", e)

    @tasks.loop(minutes=1)
    async def panel_message_editor(self):
        for msg in self.bot.panel_messages:
            try:
                view = VendingView()
                await view.create()
                await msg.edit(view=view)
            except Exception as e:
                print("메시지 수정 에러:", e)

async def setup(bot: CryptoExchangeBot):
    await bot.add_cog(TaskCog(bot))