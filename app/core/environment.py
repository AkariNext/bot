import os

from dotenv import load_dotenv

class Env:
    def __init__(self, path: str | None=None) -> None:
        self.__path: str = path or '.env'
        self.refresh()

    def refresh(self) -> None:
        """環境変数をリフレッシュする"""
        load_dotenv(self.__path)

    def get(self, key: str, default=None) -> str | None:
        return os.environ.get(key, default=default)

ENV = Env()
