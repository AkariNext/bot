from datetime import datetime
import enum
from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship, mapped_column

Base = declarative_base()


class TimelimitActions(enum.Enum):
    KICK = "kick"
    BAN = "ban"
    NONE = "none"


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
