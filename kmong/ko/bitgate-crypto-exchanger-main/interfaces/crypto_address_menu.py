import discord
from discord import ui

from models.User import CryptoAddress
from modules.constants import SUPPORTED_CRYPTO_CURRENCIES
from modules.database import Database
from modules.utils import get_crypto_by_symbol


class AddressRegisterSelect(ui.Select):
    def __init__(self):
        # 초기 코인 선택 옵션
        coin_options = [
            discord.SelectOption(
                label=f"{crypto['name']} ({crypto['symbol']})",
                value=crypto["symbol"],
                emoji=crypto["emoji"]
            )
            for crypto in SUPPORTED_CRYPTO_CURRENCIES
        ]
        super().__init__(
            custom_id="address_register",
            placeholder="코인을 선택하세요",
            options=coin_options,
            min_values=1, max_values=1
        )
        self.stage = "coin"

    async def callback(self, interaction: discord.Interaction):
        if self.stage == "coin":
            # 코인 선택 이후 callback
            crypto_symbol = self.values[0]

            networks = get_crypto_by_symbol(crypto_symbol).get("networks")
            self.options = [discord.SelectOption(label=network.get("name"), value=network.get("name"), emoji=network.get('emoji')) for network in networks]
            self.placeholder = "네트워크를 선택하세요"
            self.stage = "network"
            self.crypto_symbol = crypto_symbol
            await interaction.response.edit_message(view=self.view)
        
        else:
            # 네트워크 선택 이후 callback
            network = self.values[0]
            await interaction.response.send_modal(
                AddressRegisterModal(
                    interaction.user.id,
                    self.crypto_symbol,
                    network
                )
            )

class AddressRegisterModal(ui.Modal):
    def __init__(self, user_id: int, coin: str, network: str):
        super().__init__(title="주소 등록하기", timeout=120)
        self.user_id = user_id
        self.coin = coin
        self.network = network

        self.addressInput = ui.TextInput(
            label="주소",
            placeholder="주소를 입력하세요",
            min_length=10
        )
        self.tagInput = ui.TextInput(
            label="태그 (선택)",
            placeholder="태그가 필요하면 입력하세요",
            required=False
        )
        self.aliasInput = ui.TextInput(
            label="별명",
            placeholder="별명을 입력하세요",
            min_length=1
        )
        
        self.add_item(self.addressInput)
        self.add_item(self.tagInput)
        self.add_item(self.aliasInput)

    async def on_submit(self, interaction: discord.Interaction):
        cryptoAddress = CryptoAddress(
            crypto=self.coin,
            network=self.network,
            address=self.addressInput.value.strip(),
            tag=self.tagInput.value.strip(),
            alias=self.aliasInput.value.strip(),
            isShuffleAddress=False,
        )
        ok = await Database.add_crypto_address(str(self.user_id), cryptoAddress)

        if ok:
            await interaction.response.edit_message(
                view=AddressRegisterSuccessView(self.addressInput.value)
            )
        else:
            await interaction.response.edit_message(
                content="❌ 주소 등록에 실패했습니다. 다시 시도해 주세요.",
                view=None
            )

class AddressRegisterContainer(ui.Container):
    def __init__(self):
        super().__init__()
        self.add_item(ui.TextDisplay("### 📗 주소록 등록하기"))
        self.add_item(ui.Separator())
        self.add_item(ui.TextDisplay(
            "> 주소록을 등록할게요.\n> 클립보드 하이재킹 등 **공격에 노출**될 수 있으니 **디바이스 보안**을 다시 한번 **확인**해주세요."
        ))
        self.add_item(ui.Separator())
        self.add_item(ui.ActionRow(AddressRegisterSelect()))

class AddressRegisterView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = AddressRegisterContainer()
        container.accent_color = 0xffffff
        self.add_item(container)

class AddressRegisterSuccessContainer(ui.Container):
    def __init__(self, address: str):
        super().__init__()
        self.add_item(ui.TextDisplay("### ✅ 주소록 등록 완료"))
        self.add_item(ui.Separator())
        self.add_item(ui.TextDisplay(
            f"> `{address}` 주소가 성공적으로 등록되었어요.\n> 셔플 제휴 할인을 받으시려면, 티켓으로 문의해주세요."
        ))

class AddressRegisterSuccessView(ui.LayoutView):
    def __init__(self, address: str):
        super().__init__(timeout=None)
        container = AddressRegisterSuccessContainer(address)
        container.accent_color = 0xffffff
        self.add_item(container)
