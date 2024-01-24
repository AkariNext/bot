from abc import ABC, abstractmethod
from typing import Awaitable, Callable


class ICacheStrategy[T](ABC):
    @abstractmethod
    def __init__(self) -> None:
        ...
    
    @abstractmethod
    async def get(self, key: str) -> T:
        """キーに対応する値を取得する"""
        ...

    @abstractmethod
    async def get_or_set(self, key: str, callback: Callable[..., Awaitable[T]], *, ttl: float | None = None) -> T:
        """キーに対応する値を取得する。キーがなければcallbackで取得した値をセットする"""
        ...

    @abstractmethod
    async def set(self, key: str, value: T, *, ttl: float | None = None) -> None:
        """キーと値をセットする"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """キーを削除する"""
        ...


    @abstractmethod
    async def clear(self) -> None:
        """すべてのキーを削除する"""
        ...

