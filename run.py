import asyncio
import multiprocessing

from packages.web import main as web_app
from packages.bot import main as bot_app

async def main():
    multiprocessing.Process(target=bot_app.run).start()
    multiprocessing.Process(target=web_app.run).start()


if __name__ == "__main__":
    asyncio.run(main())