import uuid
from discord import Interaction, app_commands
from discord.ext import commands

from packages.shared.infrastructure.database import session
from packages.shared.models import CaptchaSettings, Guild

class BasicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    @app_commands.command()
    async def setup(self, inter: Interaction):
        guild = Guild(
            guild_id=inter.guild_id,
        )
        captcha_settings_id = uuid.uuid4().hex
        captcha_settings = CaptchaSettings(
            id=captcha_settings_id,
            guild=guild,
        )
        
        session.add(guild)
        session.add(captcha_settings)

        session.commit()
        await inter.response.send_message("設定しました")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(BasicCog(bot))