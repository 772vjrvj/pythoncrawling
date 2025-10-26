import discord

from modules.binance import Binance
from modules.database import Database
from modules.kimp import get_kimp

DEFAULT_USD_PRICE: float = 1390.0  # Default USD price if API fails

usd_price = DEFAULT_USD_PRICE
last_usd_price_update = 0

class InputKRWAmountModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="계산 금액 입력하기")
        self.KRWInput = discord.ui.TextInput(
            label = "원화 금액 (₩)",
            placeholder = "숫자만 입력해주세요."
        )
        self.add_item(self.KRWInput)
    
    async def on_submit(self, interaction: discord.Interaction):
        if not self.KRWInput.value.isdigit():
            return await interaction.response.send_message(
                embed = discord.Embed(
                    title = "❌ 계산에 실패했어요",
                    description = "> 숫자만 입력해주세요.",
                    color = 0xffffff
                ), 
                ephemeral = True
            )

        await interaction.response.send_message(
            embed = discord.Embed(
                title = "⌛ 잠시만 기다려주세요",
                description = "> 수수료를 계산하는 중이에요.",
                color = 0xffffff
            ),
            ephemeral = True
        )

        KRWAmount = int(self.KRWInput.value)
        binance = Binance()
        rank = await Database.get_user_rank(str(interaction.user.id))

        kimp = await get_kimp()
        purchasingFee = rank.cryptoPurchasingFee
        feePercent = kimp + purchasingFee

        calcResult = Database.calc_fee(KRWAmount, str(feePercent))
        feeAmount = calcResult["fee"]

        embed = discord.Embed(
            title = "💲 계산에 성공했어요",
            color = 0xffffff
        )
        embed.add_field(
            name = f"💰 {KRWAmount:,}원을 송금하시면", value = f"{(KRWAmount - int(feeAmount)):,}원을 받으실 수 있어요."
        )
        embed.add_field(
            name = f"💸 {KRWAmount:,}원을 받으시려면", value = f"{(KRWAmount + int(feeAmount)):,}원을 충전하셔야 해요."
        )

        await interaction.edit_original_response(embed=embed)
