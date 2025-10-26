import ast
import contextlib
import io
import traceback
from typing import cast

import discord

from modules.utils import get_env_config

config = get_env_config()

OWNER_DISCORD_IDS = config.owner_discord_ids

class ManagementModal(discord.ui.Modal, title="내용을 입력해주세요."):
    code = discord.ui.TextInput(label="내용 입력", style=discord.TextStyle.paragraph, required=True, max_length=2000)

    def __init__(self, bot, author_id):
        super().__init__()
        self.bot = bot
        self.author_id = author_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in OWNER_DISCORD_IDS and interaction.user.id != self.author_id:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        code = self.code.value
        namespace: dict = {}
        stdout = io.StringIO()

        await interaction.response.send_message("명령을 실행하는 중...", ephemeral=True)

        try:
            parsed = ast.parse(code, mode="exec")
            func_body = parsed.body

            if func_body and isinstance(func_body[-1], ast.Expr):
                last_expr = cast(ast.Expr, func_body.pop())
                assign = ast.Assign(
                    targets=[ast.Name("__eval_result", ast.Store())],
                    value=last_expr.value,
                )
                func_body.append(assign)
                func_body.append(ast.Return(value=ast.Name("__eval_result", ast.Load())))
            else:
                func_body.append(ast.Return(value=ast.Constant(None)))

            async_func = ast.AsyncFunctionDef(
                name="__user_code",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=func_body,
                decorator_list=[],
                returns=None,
                type_comment=None,
            )
            module = ast.Module(body=[async_func], type_ignores=[])
            ast.fix_missing_locations(module)

            exec(compile(module, "<user_eval>", "exec"), globals(), namespace)

            with contextlib.redirect_stdout(stdout):
                last_value = await namespace["__user_code"]()

            output = stdout.getvalue().rstrip()
            parts = []

            if output:
                parts.append(f"**출력:**\n```\n{output}\n```")
            if last_value is not None:
                parts.append(f"**값:** `{last_value!r}`")
            if not parts:
                parts.append("실행했지만 출력이나 반환값이 없습니다.")

            result_message = "\n".join(parts)

            # 원래 보낸 메시지를 가져와서 수정
            msg = await interaction.original_response()
            await msg.edit(content=result_message)

        except Exception:
            tb = traceback.format_exc()
            error_message = f"**오류:**\n```\n{tb}\n```"
            msg = await interaction.original_response()
            await msg.edit(content=error_message)