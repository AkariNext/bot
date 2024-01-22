from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

    

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    bot_token: str = Field(default=None)
    guild_id: int = Field(default=None)
    turnstile_secret: str = Field(default=None)
    domain: str = Field(default=None)
    discord_client_id: str = Field(default=None)
    discord_client_secret: str = Field(default=None)
    discord_redirect_url: str = Field(default=None)
    secret_key: str = Field(default=None)


settings = Settings()
