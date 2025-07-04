"""
Tortoise ORM の設定
"""
from tortoise import Tortoise
import logging

# データベースファイルのパス
DB_PATH = "data/database/tts_bot.db"

# Tortoise ORM の設定
TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://{DB_PATH}"
    },
    "apps": {
        "models": {
            "models": ["app.database.models.voice_settings", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "Asia/Tokyo"
}


async def init_db():
    """データベースを初期化"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()
        logging.info("🗄️ Database initialized successfully")
    except Exception as e:
        logging.error(f"Database initialization error: {e}")
        raise


async def close_db():
    """データベース接続を閉じる"""
    await Tortoise.close_connections()
    logging.info("🗄️ Database connections closed")
