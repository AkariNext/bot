from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship, mapped_column

Base = declarative_base()


class TimelimitActions(Enum):
    KICK = "kick"
    BAN = "ban"
    NONE = "none"


class Guild(Base):
    __tablename__ = "guild"

    guild_id = Column(Integer, primary_key=True)
    captcha_settings: Mapped["CaptchaSettings"] = relationship(
        back_populates="guild"
    )
    auth_requests: Mapped[list["AuthRequest"]] = relationship()
    


class CaptchaSettings(Base):
    __tablename__ = "captcha_settings"

    id = Column(String, primary_key=True)
    time_limit = Column(Integer, nullable=False, default=900)  # 制限時間 (秒)
    time_limit_action = Column(
        String, nullable=False, default=TimelimitActions.KICK.value
    )  # 制限時間を超えた場合のアクション
    guild_id = mapped_column(ForeignKey("guild.guild_id"))
    guild: Mapped["Guild"] = relationship(
        back_populates="captcha_settings"
    )


class AuthRequest(Base):
    __tablename__ = "auth_requests"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow())
    guild_id: Mapped[int] = mapped_column(ForeignKey("guild.guild_id"))
    correct_answer = Column(String, nullable=False)
