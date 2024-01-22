from datetime import datetime
import enum
from typing import Any
import uuid
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship, mapped_column

Base = declarative_base()


class TimelimitActions(enum.Enum):
    KICK = "kick"
    BAN = "ban"
    NONE = "none"

class DiscordUser(BaseModel):
    id: str
    username: str
    avatar: str
    discriminator: str
    public_flags: int
    premium_type: int
    flags: int
    banner: Any
    accent_color: Any
    global_name: str
    avatar_decoration_data: Any
    banner_color: Any
    mfa_enabled: bool
    locale: str
    email: str
    verified: bool

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[str] = mapped_column(String, nullable=False)
    discord_token: Mapped["DiscordToken"] = relationship(
        back_populates="user"
    )


class DiscordToken(Base):
    __tablename__ = "discord_token"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=str(uuid.uuid4().hex))
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped["User"] = relationship(
        back_populates="discord_token"
    )

class Guild(Base):
    __tablename__ = "guild"

    guild_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    captcha_settings: Mapped["CaptchaSettings"] = relationship(
        back_populates="guild"
    )
    auth_requests: Mapped[list["AuthRequest"]] = relationship()
    


class CaptchaSettings(Base):
    __tablename__ = "captcha_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    time_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=900)  # 制限時間 (秒)
    time_limit_action: Mapped[String] = mapped_column(
        String, nullable=False, default=TimelimitActions.KICK.value
    )  # 制限時間を超えた場合のアクション
    guild_id: Mapped[int] = mapped_column(ForeignKey("guild.guild_id"))
    guild: Mapped["Guild"] = relationship(
        back_populates="captcha_settings"
    )


class AuthRequest(Base):
    __tablename__ = "auth_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow())
    guild_id: Mapped[int] = mapped_column(ForeignKey("guild.guild_id"))
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
