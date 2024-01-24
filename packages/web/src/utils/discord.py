import aiohttp
import discord
from fastapi import Depends
from pydantic import BaseModel

from packages.shared.config import settings
from packages.shared.models import DiscordToken
from packages.web.src.auth import get_current_token

def _bot_client():
    client: discord.Client | None = None
    async def _():
        nonlocal client
        if client is None:
            client = discord.Client(intents=discord.Intents.all())
            await client.login(settings.bot_token)
        return client
    return _

get_bot_client = _bot_client()


async def http_client():
    client = aiohttp.ClientSession()
    try:
        yield client
    finally:
        await client.close()
        
        

class Guild(BaseModel):
    id: str
    name: str
    icon: str | None
    owner: bool
    permissions: int
    permissions_new: str
    features: list[str]


async def get_user_guilds(
    client: aiohttp.ClientSession = Depends(http_client),
    token: DiscordToken = Depends(get_current_token),
):
    res = await client.get(
        "https://discord.com/api/users/@me/guilds",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    
    guilds = [Guild(**raw_guild) for raw_guild in await res.json()]
    return guilds
