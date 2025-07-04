
import discord
from discord.ext import commands

from app.core.environment import ENV


INTENTS = discord.Intents.all()
COGS = [
    'app.bot.cogs.link',
    'app.bot.cogs.role',
    'app.bot.cogs.tts',
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
        print(f'Logged in as: {self.user.name} ({self.user.id})')

    async def on_message(self, message):
        print('Message received:', message.content)
        await self.process_commands(message)


if __name__ == '__main__':
    bot = Bot()
    bot.run(ENV.get('BOT_TOKEN'))
