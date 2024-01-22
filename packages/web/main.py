from datetime import datetime, timedelta, timezone
from glob import glob
from importlib import import_module
from pathlib import PurePath
import aiohttp
from fastapi.responses import RedirectResponse


import uvicorn
from fastapi import Depends, FastAPI, Request, Response
from fastapi_discord import DiscordOAuthClient
from sqlalchemy.orm import Session
from jose import jwt

from packages.shared.config import settings
from packages.shared.database.repository.user import (
    DiscordTokenRepository,
    UserRepository,
)
from packages.shared.infrastructure.database import get_db
from packages.shared.models import DiscordUser, User
from packages.web.const import TEMPLATES
from packages.web.src.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    get_current_user,
    is_authenticated,
)


discord = DiscordOAuthClient(
    settings.discord_client_id,
    settings.discord_client_secret,
    settings.discord_redirect_url,
    ("identify", "guilds", "email"),
)  # scopes

app = FastAPI()


async def get_user(token: str):
    async with aiohttp.ClientSession() as client:
        async with client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            return DiscordUser(**await resp.json())


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


@app.on_event("startup")
async def on_startup():
    await discord.init()


@app.get("/")
async def index(request: Request, user: User = Depends(get_current_user)):
    return TEMPLATES.TemplateResponse("top.html", {"request": request, "user": user})


@app.get("/login")
async def login(db: Session = Depends(get_db)):
    return RedirectResponse(discord.oauth_login_url, status_code=302)


@app.get("/callback")
async def callback(code: str, response: Response):
    token, refresh_token = await discord.get_access_token(code)
    user = await get_user(token)

    await UserRepository.create_or_update(user)
    await DiscordTokenRepository.create_or_update(user.id, token, refresh_token)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/authed")
async def authed(
    request: Request,
    user_id: str = Depends(get_current_user),
    is_authenticated: bool = Depends(is_authenticated),
):
    if is_authenticated is False:
        return RedirectResponse("/login")
    return TEMPLATES.TemplateResponse("authed.html", {"request": request})


for route in glob("packages/web/routes/*.py"):
    if "__init__" in route:
        continue

    app.include_router(
        import_module(PurePath(route).as_posix()[:-3].replace("/", ".")).router
    )


def run():
    uvicorn.run("packages.web.main:app", host="0.0.0.0", loop="asyncio", reload=True)
