import datetime
from typing import List, Literal

import discord
from discord import ui

from models.User import VerificationData
from modules.database import Database
from modules.identificati0n_client import Verify
from modules.log import send_discord_log
from modules.utils import get_env_config

config = get_env_config()

BRAND_NAME = config.brand_name
ID_VERIFICATION_API_KEY = config.id_verification_api_key
REGISTER_LOG_WEBHOOK = config.register_log_webhook

class DefaultContainer(ui.Container):
    author = ui.TextDisplay(f"### 🪙 {BRAND_NAME} - 24시간 코인송금대행")
    sep1 = ui.Separator()

    def __init__(self, title: str, description: str):
        super().__init__()
        self.add_item(ui.TextDisplay(title))
        self.add_item(ui.TextDisplay(description))

class DefaultView(ui.LayoutView):
    def __init__(self, title: str, description: str):
        super().__init__(timeout=None)
        container = DefaultContainer(title, description)
        container.accent_color = 0xffffff
        self.add_item(container)

class CodeInputModal(ui.Modal):
    def __init__(self, verify_client: Verify):
        super().__init__(title="인증번호 입력", timeout=120)
        self.verify_client = verify_client

        self.smsCodeInput = discord.ui.TextInput(label="인증번호", min_length=6, max_length=6)

        self.add_item(self.smsCodeInput)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            view=DefaultView("### 🪪 본인인증 - 정보 확인 중", "인증 요청을 처리하는 중이에요. 잠시만 기다려주세요.")
        )
        
        check_result = await self.verify_client.verify(self.smsCodeInput.value)

        if not check_result["success"]:
            log_embed = discord.Embed(
                title = "❌ 회원가입 실패",
                description = f"{interaction.user.mention}님이 회원가입에 실패했어요.\nResp: {check_result['message']}",
                color = discord.Color.red()
            )
            await send_discord_log(
                discord_user_id=interaction.user.id,
                embed=log_embed,
                webhook_url=REGISTER_LOG_WEBHOOK
            )
            
            return await interaction.edit_original_response(
                view=DefaultView("### ❌ 본인인증 - 실패", check_result["message"])
            )

        identifier_alias = check_result["identifierAlias"]

        verification_data = check_result["verificationData"]

        try:
            await Database.register_user(
                identifier_alias,
                verification_data
            )
        except Exception as e:
            print(e)

            log_embed = discord.Embed(
                title = "⚠️ 회원가입 실패",
                description = str(e),
                color = discord.Color.yellow()
            )
            await send_discord_log(
                discord_user_id=interaction.user.id,
                embed=log_embed,
                webhook_url=REGISTER_LOG_WEBHOOK
            )

            return await interaction.edit_original_response(
                view=DefaultView(
                    "### ❌ 본인인증 - 실패",
                    f"{verification_data.name}님의 명의로 이미 연결된 계정이 있어요. 문의해주세요."
                )
            )

        log_embed = discord.Embed(
            title = "✅ 회원가입 성공",
            description = f"{interaction.user.mention}님이 회원가입에 성공했어요.",
            color = 0xffffff
        )
        log_embed.add_field(
            name = "이름", value = verification_data.name
        )
        log_embed.add_field(
            name = "생년월일", value = verification_data.birthdate
        )
        log_embed.add_field(
            name = "전화번호", value = verification_data.phone
        )
        log_embed.add_field(
            name = "통신사", value = verification_data.carrier
        )
        await send_discord_log(
            discord_user_id=interaction.user.id,
            embed=log_embed,
            webhook_url=REGISTER_LOG_WEBHOOK
        )
        
        await interaction.edit_original_response(
            view=DefaultView("### ✅ 본인인증 - 완료", "인증이 성공적으로 완료되었어요. 이제 서비스를 사용하실 수 있어요.")
        )

class CodeInputButton(ui.Button):
    def __init__(self, verify_client: Verify):
        super().__init__(label="입력하기", style=discord.ButtonStyle.success)
        self.verify_client = verify_client

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CodeInputModal(self.verify_client))

class CodeInputContainer(DefaultContainer):
    def __init__(self, verify_client: Verify):
        super().__init__("### 🪪 본인인증 - 인증번호 입력", "SMS로 전송된 6자리 인증번호를 입력해주세요.")
        self.add_item(ui.Separator())
        self.add_item(ui.ActionRow(CodeInputButton(verify_client)))

class CodeInputView(ui.LayoutView):
    def __init__(self, verify_client: Verify):
        super().__init__(timeout=180)
        container = CodeInputContainer(verify_client)
        container.accent_color = 0xffffff
        self.add_item(container)

class InfoInputModal(ui.Modal):
    carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]

    def __init__(self, carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]):
        super().__init__(title="인증 정보 입력하기", timeout=120)
        self.carrier = carrier

        self.nameInput = discord.ui.TextInput(label="이름", placeholder="홍길동", min_length=2, max_length=20)
        self.birthdayInput = discord.ui.TextInput(label="생년월일", placeholder="YYMMDD", min_length=6, max_length=6)
        self.genderInput = discord.ui.TextInput(label="성별코드", placeholder="성별코드 1자리 (1,2,3,4)", min_length=1, max_length=1)
        self.phoneInput = discord.ui.TextInput(label="전화번호", placeholder="01012345678", min_length=11, max_length=11)

        self.add_item(self.nameInput)
        self.add_item(self.birthdayInput)
        self.add_item(self.genderInput)
        self.add_item(self.phoneInput)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if isinstance(self.birthdayInput.value, int):
                raise Exception("잘못된 생년월일이에요. 확인 후 다시 입력해주세요.")
            
            if isinstance(self.phoneInput.value, int):
                raise Exception("잘못된 전화번호에요. 확인 후 다시 입력해주세요.")
            
            if isinstance(self.genderInput.value, int) or int(self.genderInput.value) < 1 or int(self.genderInput.value) > 8:
                raise Exception("잘못된 성별이에요. 확인 후 다시 입력해주세요.")

            birthdate, gender, phone = self.birthdayInput.value, self.genderInput.value, self.phoneInput.value

            year, month, day = int(birthdate[:2]), int(birthdate[2:4]), int(birthdate[4:6])

            today = datetime.datetime.today()
            currentyear = today.year % 100

            century = 2000 if year <= currentyear else 1900
            birthyear = century + year

            birthdate = datetime.datetime(birthyear, month, day)

            if birthdate > today:
                raise Exception("잘못된 생년월일이에요. 확인 후 다시 입력해주세요.")
            
            age = today.year - birthdate.year
            
            if (today.month, today.day) < (birthdate.month, birthdate.day):
                age -= 1

            user_data = await Database.get_user_info(str(interaction.user.id), True)
            if age >= 19 and (not user_data or not user_data.bypassAdultVerification):
                raise Exception("현재 사용자님은 인증하기 위해 티켓 문의가 필요해요. 문의하기 채널에서 문의해주세요.")

        except Exception as e:
            return await interaction.response.edit_message(
                view=DefaultView("### ❌ 본인인증 - 실패", str(e))
            )

        await interaction.response.edit_message(
            view=DefaultView("### 🪪 본인인증 - 정보 확인 중", "요청을 처리하는 중이에요. 잠시만 기다려주세요.")
        )
        verify_client = Verify(ID_VERIFICATION_API_KEY)
        verify_result = await verify_client.sendRequest(
            self.nameInput.value,
            self.birthdayInput.value + self.genderInput.value,
            self.phoneInput.value,
            self.carrier,
            interaction.user.id
        )
        if not verify_result["success"]:
            return await interaction.edit_original_response(
                view=DefaultView("### ❌ 본인인증 - 실패", verify_result["message"])
            )
        await interaction.edit_original_response(
            view=CodeInputView(verify_client)
        )

class InfoInputButton(ui.Button):
    carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]

    def __init__(self, carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]):
        super().__init__(label="입력하기", style=discord.ButtonStyle.success)
        self.carrier = carrier

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(InfoInputModal(self.carrier))

class InfoInputContainer(DefaultContainer):
    def __init__(self, carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]):
        super().__init__("### 🪪 본인인증 - 인증 정보 입력", "본인 명의의 정보를 입력해주세요.")
        self.add_item(ui.Separator())
        self.add_item(ui.ActionRow(InfoInputButton(carrier)))

class InfoInputView(ui.LayoutView):
    def __init__(self, carrier: Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]):
        super().__init__(timeout=None)
        container = InfoInputContainer(carrier)
        container.accent_color = 0xffffff
        self.add_item(container)

class TelecomSelect(ui.Select):
    values: List[Literal["SKT", "KT", "LGU", "MVNO_SKT", "MVNO_KT", "MVNO_LGU"]]

    def __init__(self):
        super().__init__(
            custom_id="telecom_select",
            placeholder="통신사를 선택해주세요.",
            options=[
                discord.SelectOption(label="SKT", value="SKT"),
                discord.SelectOption(label="KT", value="KT"),
                discord.SelectOption(label="LG U+", value="LGU"),
                discord.SelectOption(label="SKT 알뜰폰", value="MVNO_SKT"),
                discord.SelectOption(label="KT 알뜰폰", value="MVNO_KT"),
                discord.SelectOption(label="LG U+ 알뜰폰", value="MVNO_LGU"),
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        await interaction.response.edit_message(view=InfoInputView(choice))

class SelectCarrierContainer(DefaultContainer):
    def __init__(self):
        super().__init__("### 🪪 본인인증 - 통신사 선택", "안전한 서비스 이용을 위해 인증을 진행해주세요.")
        self.add_item(ui.Separator())
        self.add_item(ui.ActionRow(TelecomSelect()))

class SelectCarrierView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = SelectCarrierContainer()
        container.accent_color = 0xffffff
        self.add_item(container)