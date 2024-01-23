from packages.shared.infrastructure.database import scoped_session
from packages.shared.models import Guild


class GuildRepository:
    @staticmethod
    async def create_or_update(guild_id: int, owner_id: int) -> Guild:
        guild: Guild | None = None
        with scoped_session() as session:
            guild = session.query(Guild).filter_by(guild_id=guild_id).first()
            if guild is None:
                guild = Guild(guild_id=guild_id, owner_id=owner_id)
            else:
                guild.owner_id = owner_id
            session.add(guild)
        return guild

    @staticmethod
    async def get_guild_by_id(guild_id: int) -> Guild | None:
        """
        指定したIDのギルドデータを取得します。

        Parameters
        ----------
        guild_id: str
            取得したいギルドのID

        Returns
        -------
        Guild | None
            取得したギルドのデータ
        """
        with scoped_session() as session:
            return session.query(Guild).filter_by(guild_id=guild_id).first()
