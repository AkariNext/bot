
import os
import discord
from discord.ext import commands

from src.boot import ENV


# from src.infrastructures import db


INTENTS = discord.Intents.all()
COGS = [
    'src.cogs.link',
]


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=INTENTS,
        )

    async def setup_hook(self) -> None:
        # await db.init()
        for cog in COGS:
            await self.load_extension(cog)

        self.tree.copy_global_to(guild=discord.Object(id='530299114387406860'))
        await self.tree.sync(guild=discord.Object(id='530299114387406860'))

        return await super().setup_hook()

    async def on_ready(self):
        print('Bot is ready')

    async def on_message(self, message):
        print('Message received:', message.content)
        await self.process_commands(message)


# TOKEN = os.getenv('TOKEN')

# if TOKEN is None:
#     raise ValueError('Token is not set')

if __name__ == '__main__':
    bot = Bot()
    bot.run(ENV.get('BOT_TOKEN'))
