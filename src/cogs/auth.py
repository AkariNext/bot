import discord
from discord.ext import commands
from discord import Embed, app_commands


class AuthCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @app_commands.command(name="setup", description="Authenticate with the bot")
    async def auth(self, inter: discord.Interaction) -> None:
        embed = Embed(
            title="認証",
            description="ボタンをクリックして認証を完了してください",
            color=discord.Color.blurple(),
        )


        view = discord.ui.View(timeout=None)

        button = discord.ui.Button(
            label="認証",
            style=discord.ButtonStyle.green,
        )

        view.add_item(button)

        await inter.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AuthCog(bot))
