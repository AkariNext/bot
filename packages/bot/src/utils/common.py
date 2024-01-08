import discord
from discord.ext import commands


async def get_guild(bot: commands.Bot, guild_id: int) -> discord.guild.Guild:
    guild = bot.get_guild(guild_id)
    if guild is None:
        guild = await bot.fetch_guild(guild_id)
    return guild

async def get_member(guild: discord.guild.Guild, user_id: int) -> discord.member.Member:
    member = guild.get_member(user_id)
    if member is None:
        member = await guild.fetch_member(user_id)
    return member
