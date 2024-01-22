from __future__ import annotations
import datetime

import logging
import random
import traceback
import uuid


import discord
from captcha.image import ImageCaptcha
from discord.ext import commands, tasks
from discord import Embed, Interaction, app_commands
from packages.bot.src.utils.common import get_guild, get_member

from packages.shared.infrastructure.database import scoped_session
from packages.shared.models import AuthRequest, CaptchaSettings, Guild


_log = logging.getLogger(__name__)


class InputAnswerModal(discord.ui.Modal, title="Captcha"):
    name = discord.ui.TextInput(
        label="Name",
        placeholder="Your name here...",
        required=True,
    )

    async def on_submit(self, inter: discord.Interaction):
        with scoped_session() as session:
            auth_request = (
                session.query(AuthRequest)
                .filter(AuthRequest.user_id == inter.user.id)
                .first()
            )
            if auth_request is None:
                await inter.response.send_message(
                    "認証が見つかりませんでした", ephemeral=True
                )
                return
            if auth_request.correct_answer != self.name.value:
                await inter.response.send_message("答えが違います", ephemeral=True)
                return
            session.delete(auth_request)

        await inter.response.send_message("認証が完了しました", ephemeral=True)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        traceback.print_exception(type(error), error, error.__traceback__)


class AuthCog(commands.Cog):
    group = app_commands.Group(name="auth", description="auth commands")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.check_auth_not_completed.start()

    @group.command(name="setup", description="setup auth channel")
    async def setup(self, inter: Interaction):
        button = discord.ui.Button(
            style=discord.ButtonStyle.green, label="Verify", custom_id="start_verify"
        )
        view = discord.ui.View().add_item(button)

        await inter.response.send_message(
            embed=discord.Embed(
                title="🤖 Verification required",
                description="雑談などのチャンネルにアクセスするには人間か確認する必要があります",
                color=discord.Color.blue(),
            ),
            view=view,
        )

    @commands.Cog.listener()
    async def on_interaction(self, inter: discord.Interaction):
        if inter.data is None:
            return
        component_type = inter.data.get("component_type")
        match component_type:
            case 2:
                await self.on_button_click(inter)

    async def on_button_click(self, inter: discord.Interaction):
        if inter.data is None:
            return

        custom_id = inter.data.get("custom_id")

        match custom_id:
            case "start_verify":
                with scoped_session() as session:
                    _id = str(uuid.uuid4())
                    correct_answer = str(random.randint(1000, 9999))
                    session.add(
                        AuthRequest(
                            id=_id,
                            user_id=inter.user.id,
                            guild_id=inter.guild_id,
                            correct_answer=correct_answer,
                        )
                    )
                embed = Embed(title="画像に表示されている数字を入力してください")
                image = ImageCaptcha().generate(correct_answer)
                file = discord.File(image, filename="captcha.png")

                embed.set_image(url="attachment://captcha.png")

                button = discord.ui.Button(
                    style=discord.ButtonStyle.green,
                    label="答えを送信",
                    custom_id="complete_verify",
                )
                view = discord.ui.View().add_item(button)

                await inter.response.send_message(
                    embed=embed, file=file, view=view, ephemeral=True
                )

            case "complete_verify":
                await inter.response.send_modal(InputAnswerModal())

    @tasks.loop(seconds=5)
    async def check_auth_not_completed(self):
        with scoped_session() as session:
            results = (
                session.query(Guild, CaptchaSettings)
                .join(CaptchaSettings, Guild.guild_id == CaptchaSettings.guild_id)
                .all()
            )

        for result in results:
            guilds, captcha_settings = result.tuple()
            for auth_request in guilds.auth_requests:
                time_limit = auth_request.created_at + datetime.timedelta(
                    seconds=captcha_settings.time_limit
                )

                if auth_request.created_at > time_limit:
                    guild = await get_guild(self.bot, guilds.guild_id)
                    member = await get_member(guild, auth_request.user_id)

                    match captcha_settings.time_limit_action:
                        case "kick":
                            await member.kick()
                        case "ban":
                            await member.ban()

                    session.delete(auth_request)


async def setup(bot: commands.Bot):
    _log.info("Loading AuthCog...")
    await bot.add_cog(AuthCog(bot=bot))
