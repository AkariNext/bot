import discord
from fastapi import APIRouter, Depends, Request
from packages.shared.models import User

from packages.web.const import TEMPLATES
from packages.web.src.auth import get_current_user
from packages.web.src.utils.discord import get_user_guilds

router = APIRouter(prefix="/dashboard")

@router.get("/")
async def index(request: Request, user: User = Depends(get_current_user), guilds: list[discord.Guild] = Depends(get_user_guilds)):
    
    return TEMPLATES.TemplateResponse("dashboard/index.html", {"request": request, "user": user, "guilds": guilds})
