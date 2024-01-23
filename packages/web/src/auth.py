from typing import Annotated

from fastapi import Cookie, Depends
from jose import ExpiredSignatureError, jwt

from packages.shared.config import settings
from packages.shared.database.repository.user import (
    DiscordTokenRepository,
    UserRepository,
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


async def get_current_user_id(access_token: Annotated[str | None, Cookie()] = None):
    if access_token is None:
        return None
    try:
        payload = jwt.decode(
            access_token.replace("Bearer", "").strip(),
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
    except ExpiredSignatureError:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None

    return user_id


async def get_current_user(user_id: str = Depends(get_current_user_id)):
    if user_id is None:
        return None

    return await UserRepository.get(user_id)


async def get_current_token(user_id: str = Depends(get_current_user_id)):
    if user_id is None:
        return None

    return await DiscordTokenRepository.get(user_id)


async def is_authenticated(user_id: str = Depends(get_current_user)):
    return user_id is not None
