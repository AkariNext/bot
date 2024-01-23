import uuid
from discord import Interaction, app_commands
from discord.ext import commands
from packages.shared.database.repository.guild import GuildRepository

from packages.shared.infrastructure.database import scoped_session
from packages.shared.models import CaptchaSettings, Guild


class BasicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot


    @app_commands.command()
    async def setup(self, inter: Interaction):
        if inter.guild is None:
            await inter.response.send_message("サーバー内で実行してください", ephemeral=True)
            return
        guild_id = inter.guild_id
        owner_id = inter.guild.owner_id
        if owner_id is None or guild_id is None:
            await inter.response.send_message("ギルドIDまたはギルドの所有者IDが取得できませんでした", ephemeral=True)
            return

        guild = await GuildRepository.create_or_update(guild_id=guild_id, owner_id=owner_id)
        captcha_settings_id = uuid.uuid4().hex
        captcha_settings = CaptchaSettings(
            id=captcha_settings_id,
            guild=guild,
        )
        

        with scoped_session() as session:
            session.add(guild)
            session.add(captcha_settings)

        await inter.response.send_message("設定しました")

    @app_commands.command()
    async def signup(self, inter: Interaction):
        await inter.response.send_message("認証が完了しました", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(BasicCog(bot))
