from packages.shared.infrastructure.database import scoped_session
from packages.shared.models import DiscordToken, DiscordUser, User


class UserRepository:

    @staticmethod
    async def create_or_update(user: DiscordUser):
        with scoped_session() as session:
            found_user = session.query(User).filter(User.id == user.id).first()
            if found_user is None:
                created_user = User(id=user.id, username=user.username, avatar=user.avatar)
                session.add(created_user)
            else:
                found_user.username = user.username
                found_user.avatar = user.avatar
                session.add(found_user)

    @staticmethod
    async def get(user_id: str):
        with scoped_session() as session:
            return session.query(User).filter(User.id == user_id).first()

class DiscordTokenRepository:
    @staticmethod
    async def create_or_update(user_id: str, token:str, refresh_token:str):
        with scoped_session() as session:
            discord_token = session.query(DiscordToken).filter(DiscordToken.user_id == user_id).first()
            if discord_token is None:
                discord_token = DiscordToken(user_id=user_id, access_token=token, refresh_token=refresh_token)
                session.add(discord_token)
            else:
                discord_token.access_token = token
                discord_token.refresh_token = refresh_token
                session.add(discord_token)
                
    @staticmethod
    async def get(user_id: str):
        with scoped_session() as session:
            return session.query(DiscordToken).filter(DiscordToken.user_id == user_id).first()
