import logging

import discord
from discord.ext import commands
from rich.progress import track

from packages.bot.src.utils.cog import get_cogs
from packages.shared.config import settings
from packages.bot.src.utils.log import setup_logger

setup_logger()  # setup logger

_log = logging.getLogger(__name__)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.all(), log_level =logging.WARNING)
    
    async def on_ready(self):
        if self.user is None:
            raise RuntimeError('Bot is not logged in.')
        _log.info(f'Logged in as {self.user.name}')

    async def setup_hook(self) -> None:
        guild = discord.Object(id=settings.guild_id)

        for cog in track(get_cogs(), description='Loading cogs...'):
            await self.load_extension(cog)

        self.tree.copy_global_to(guild=guild)  # copy global commands to guild
        _log.info('Syncing tree...')
        await self.tree.sync(guild=guild)
        
        return await super().setup_hook()
        
def run():
    bot = Bot()
    _log.info('Starting bot...')
    bot.run(token=settings.bot_token, log_level=logging.WARNING)