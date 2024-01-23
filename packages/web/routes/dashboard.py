import discord
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from packages.shared.infrastructure.database import get_db
from packages.shared.models import Guild, User
from packages.web.const import TEMPLATES
from packages.web.src.auth import get_current_user, is_authenticated
from packages.web.src.utils.common import get_current_path
from packages.web.src.utils.discord import get_user_guilds

router = APIRouter(prefix="/dashboard")


@router.get("/")
async def index(
    request: Request,
    user: User = Depends(get_current_user),
    guilds: list[discord.Guild] = Depends(get_user_guilds),
):
    return TEMPLATES.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": user,
            "guilds": guilds,
            "current_path": await get_current_path(request),
        },
    )


@router.get("/{guild_id}")
async def show_guild_index(
    request: Request,
    guild_id: int,
    is_auth: bool = Depends(is_authenticated),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    if is_auth is False:
        return RedirectResponse("/login")
    found_guild = (
        session.query(Guild)
        .join(
            User, Guild.managers, isouter=True
        )  # 外部結合にしないとマネージャーがいないギルドが取得できない
        .filter(
            or_(
                and_(Guild.guild_id == guild_id, Guild.owner_id == user.id),
                and_(Guild.guild_id == guild_id, Guild.managers.any(id=user.id)),
            )
        )
        .first()
    )

    if found_guild is None:
        return TEMPLATES.TemplateResponse(
            "dashboard/$guild_id/not_setup.html", {"request": request, "user": user}
        )

    return found_guild

    # return TEMPLATES.TemplateResponse("dashboard/guild_id.html", {"request": request, "user": user, "guilds": guilds})
