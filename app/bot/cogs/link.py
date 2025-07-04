import re

from discord import Embed, TextChannel
import discord
from discord.ext import commands

class LinkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener('on_message')
    async def link_check(self, message: discord.Message):
        pattern = re.compile(r'https://discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)')
        if found := pattern.search(message.content):
            print('Guild ID:', found.group(1))
            print('Channel ID:', found.group(2))
            print('Message ID:', found.group(3))
            channel_id = int(found.group(2))
            message_id = int(found.group(3))

            found_channel = await self.bot.fetch_channel(channel_id)
            if isinstance(found_channel, TextChannel):
                found_message = await found_channel.fetch_message(message_id)
                
                embed = Embed(
                    description=found_message.content,
                    color=discord.Color.dark_green()
                )

                if len(found_message.attachments) > 0:
                    if found_message.attachments[0].content_type in ['image/png', 'image/jpeg', 'image/gif', 'video/mp4']:
                        embed.set_image(url=found_message.attachments[0].url)

                embed.set_footer(text=f'In {found_channel.name} - {found_message.created_at.strftime('%Y/%m/%d - %H:%M:%S')}', icon_url=found_channel.guild.icon)
                
                embed.set_author(
                    name=found_message.author.display_name,
                    icon_url=found_message.author.display_avatar
                )
                
                view = discord.ui.View(timeout=None)
                
                button = discord.ui.Button(
                    label='Jump to message',
                    style=discord.ButtonStyle.link,
                    url=found_message.jump_url)
                
                view.add_item(button)
                
                await message.channel.send(embed=embed, view=view)
        await self.bot.process_commands(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(LinkCog(bot))
