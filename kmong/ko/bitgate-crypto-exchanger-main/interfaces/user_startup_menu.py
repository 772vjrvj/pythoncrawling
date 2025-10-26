from typing import Union

from discord import ui

from interfaces.buttons import (CalcuateKRWFeeButton, ChargeButton, InfoButton,
                                PurchaseButton)
from modules.binance import Binance
from modules.kimp import get_kimp
from modules.utils import get_env_config

config = get_env_config()

BRAND_NAME = config.brand_name

class VendingView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout = None)
    
    async def create(self):
        binance = Binance()
        try:
            stock = await binance.get_stock()
            kimp = await get_kimp()
        except Exception as e:
            stock = "UNKNOWN(BAPI_ERROR)"
            kimp = "UNKNOWN(BAPI_ERROR)"

        container = VendingContainer(stock, kimp)
        container.accent_color = 0xffffff

        self.add_item(container)

class VendingContainer(ui.Container):    
    def __init__(self, stock: Union[dict[str, int], str], kimp: Union[float, str]):
        super().__init__()

        if isinstance(stock, str):
            stock_display = stock
        else:
            stock_display = f"{stock['KRW']:,}원 (≈ ${round(stock['USD'], 2)})"

        if isinstance(kimp, str):
            kimp_display = kimp
        else:
            kimp_display = f"{kimp}%"
        
        self.add_item(ui.TextDisplay(f"### 🪙 {BRAND_NAME} - 24시간 코인송금대행"))

        self.add_item(ui.Separator())

        self.add_item(ui.TextDisplay(f"**💰 실시간 재고**: `{stock_display}`"))
        self.add_item(ui.TextDisplay(f"**📈 실시간 김프**: `{kimp_display}`"))

        self.add_item(ui.Separator())

        charge_section = ui.Section(accessory=ChargeButton())
        charge_section.add_item(ui.TextDisplay("### 충전하기"))
        charge_section.add_item(ui.TextDisplay("빠르고 실패 없는 자동충전 시스템을 경험해보세요."))
        self.add_item(charge_section)

        self.add_item(ui.Separator())

        purchase_section = ui.Section(accessory=PurchaseButton())
        purchase_section.add_item(ui.TextDisplay("### 구매하기"))
        purchase_section.add_item(ui.TextDisplay("원하는 코인을 언제든 자동으로 구매하실 수 있어요."))
        self.add_item(purchase_section)

        self.add_item(ui.Separator())

        info_section = ui.Section(accessory=InfoButton())
        info_section.add_item(ui.TextDisplay("### 내 정보"))
        info_section.add_item(ui.TextDisplay("계정 잔액과 거래 내역, 수수료를 확인해보실 수 있어요."))
        self.add_item(info_section)

        self.add_item(ui.Separator())

        fee_section = ui.Section(accessory=CalcuateKRWFeeButton())
        fee_section.add_item(ui.TextDisplay("### 수수료 계산"))
        fee_section.add_item(ui.TextDisplay("금액만 입력하시면 편리하게 송금 로직과 동일한 방식으로 자동으로 계산해드려요."))
        self.add_item(fee_section)