from typing import List, Optional

import aiohttp
import discord
import requests
from discord import Webhook

from modules.nh_client import Transaction
from modules.utils import get_env_config

config = get_env_config()

BRAND_NAME = config.brand_name
ERROR_LOG_WEBHOOK = config.error_log_webhook
OWNER_DISCORD_IDS = config.owner_discord_ids
SUSPICIOUS_DEPOSIT_LOG_WEBHOOK = config.suspicious_deposit_log_webhook

def send_webhook_log(webhook_url: str, message: str):
    """Discord Webhook으로 에러 메시지 전송"""
    if not webhook_url:
        print("webhook_url이 잘못되었습니다!")
        return
    data = {"content": message}
    try:
        requests.post(webhook_url, json=data, timeout=5)
    except Exception as e:
        print("디스코드 로그 전송 실패:", e)

def _make_embed(
    content: str,
    title: Optional[str] = None,
    color: int = 0xFF0000,
    level: Optional[str] = None
) -> discord.Embed:
    embed = discord.Embed(
        title=title or f"[LOG{ '(' + level + ')' if level else ''}]",
        description=content,
        color=color
    )
    embed.set_footer(text="자동 생성 로그")
    embed.timestamp = discord.utils.utcnow()
    return embed

async def send_discord_log(
    discord_user_id: Optional[int] = None,
    *,
    content: Optional[str] = None,
    embed: Optional[discord.Embed] = None,
    embeds: Optional[List[discord.Embed]] = None,
    title: Optional[str] = None,
    level: Optional[str] = None,
    color: Optional[int] = None,
    webhook_url: Optional[str] = ERROR_LOG_WEBHOOK
) -> None:
    try:
        if not embeds:
            embeds = []

        if not webhook_url:
            return

        if embed is None and embeds.__len__() == 0:
            embed = _make_embed(
                content=content or "----------------",
                title=title,
                color=color or (0xFF0000 if level == "ERROR" else 0x00FF00),
                level=level
            )
        
        if embed:
            embeds.append(embed)

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhook_url, session=session)
            await webhook.send(
                content=content or "----------------",
                embeds=embeds,
                username=f"{BRAND_NAME} - Logs"
            )
    except Exception as e:
        print(e, "Error sending log.")

async def send_suspicious_deposit_log(suspicious_deposits: List[Transaction]):
    sus_embeds = []

    # check suspicious deposits
    for suspiciousDeposit in suspicious_deposits:
        log_embed = discord.Embed(
            title = "⚠️ 의심스러운 입금이 감지되었어요",
            description = f"알 수 없는 출처로부터의 입금이 감지되었어요.",
            color = 0xffffff
        )
        log_embed.add_field(
            name = "입금자명", value = suspiciousDeposit["name"]
        )
        log_embed.add_field(
            name = "입금 금액", value = f"{suspiciousDeposit['amount']:,}원"
        )
        log_embed.add_field(
            name = "입금 시각",
            value = f"<t:{round(suspiciousDeposit['date'] / 1000)}:F>"
        )

        log_embed.set_footer(text=f"TxID: {suspiciousDeposit['id']}")

        sus_embeds.append(log_embed)

    for i in range(0, len(sus_embeds), 8):
        batch = sus_embeds[i:i + 8]
        await send_discord_log(content="@everyone", embeds=batch, webhook_url=SUSPICIOUS_DEPOSIT_LOG_WEBHOOK)