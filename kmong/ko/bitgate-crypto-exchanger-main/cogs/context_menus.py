import discord
from beanie.odm.operators.update.general import Set
from discord import app_commands

from interfaces.admin_management_menu import (AdminMenuMainContainer,
                                              InfoMainView)
from models.User import User
from modules.bot import CryptoExchangeBot
from modules.database import Database
from modules.utils import get_env_config

config = get_env_config()

OWNER_DISCORD_IDS = config.owner_discord_ids

@app_commands.context_menu(name="1. 유저 일반 정보")
@app_commands.check(lambda i: i.user.id in OWNER_DISCORD_IDS)
async def user_default_info(
    interaction: discord.Interaction,
    user: discord.User
) -> None:
    if interaction.user.id not in OWNER_DISCORD_IDS:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ 권한 부족",
                description="사용자님은 해당 명령어를 사용할 권한이 부족해요.",
                color=0xe74c3c
            ), ephemeral=True
        )
        return

    user_data = await Database.get_user_info(str(user.id), True)
    if not user_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ 조회 실패",
                description="봇에 가입이 완료된 유저만 조회하실 수 있어요.",
                color=0xffffff
            ), ephemeral=True
        )
        return

    userRank = await Database.get_user_rank(user_data.discordId)
    transactions = await Database.get_recent_crypto_transactions(user_data.discordId)
    container = AdminMenuMainContainer(user_data, userRank, transactions)
    await interaction.response.send_message(view=InfoMainView(container), ephemeral=True)


@app_commands.context_menu(name="2. 유저 인증 정보")
@app_commands.check(lambda i: i.user.id in OWNER_DISCORD_IDS)
async def user_verify_info(
    interaction: discord.Interaction,
    user: discord.User
) -> None:
    if interaction.user.id not in OWNER_DISCORD_IDS:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ 권한 부족",
                description="사용자님은 해당 명령어를 사용할 권한이 부족해요.",
                color=0xe74c3c
            ), ephemeral=True
        )
        return

    user_data = await Database.get_user_info(str(user.id))
    if not user_data or not user_data.verificationData:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ 조회 실패",
                description="봇에 가입이 완료된 유저만 조회하실 수 있어요.",
                color=0xffffff
            ), ephemeral=True
        )
        return

    embed = discord.Embed(title="유저 인증 정보", color=0xFFFFFF)

    embed.add_field(name="이름", value=user_data.verificationData.name)
    embed.add_field(name="생년월일", value=str(user_data.verificationData.birthdate).split()[0])
    embed.add_field(name="전화번호", value=user_data.verificationData.phone)
    embed.add_field(name="성별", value=user_data.verificationData.gender)
    embed.add_field(name="통신사", value=user_data.verificationData.carrier)
    embed.add_field(name="CI", value=user_data.verificationData.ci[:11] + "...")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.context_menu(name="3. 가입 제한 해제")
@app_commands.check(lambda i: i.user.id in OWNER_DISCORD_IDS)
async def remove_verification_restriction(
    interaction: discord.Interaction,
    user: discord.User
) -> None:
    if interaction.user.id not in OWNER_DISCORD_IDS:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ 권한 부족",
                description="사용자님은 해당 명령어를 사용할 권한이 부족해요.",
                color=0xe74c3c
            ), ephemeral=True
        )
        return

    uesr_data = await Database.get_user_info(str(user.id), True)

    if not uesr_data:
        uesr_data = await Database.register_user(str(user.id))

    if not uesr_data:
        return

    await uesr_data.update(Set({User.bypassAdultVerification: True}))
    
    await interaction.response.send_message(
        embed=discord.Embed(
            title="유저 업데이트 성공",
            description="해당 유저의 성인 가입 제한이 해제되었어요.",
            color=0xffffff
        ), ephemeral=True
    )

async def setup(bot: CryptoExchangeBot):
    bot.tree.add_command(user_default_info)
    bot.tree.add_command(user_verify_info)
    bot.tree.add_command(remove_verification_restriction)