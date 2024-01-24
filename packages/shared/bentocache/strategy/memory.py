import asyncio
from typing import Awaitable, Callable
from packages.shared.bentocache.strategy.interface import ICacheStrategy


class MemoryStrategy[T](ICacheStrategy[T]):
    def __init__(self):
        self._data: dict[str, T] = {}

    async def get(self, key: str) -> T | None:
        return self._data.get(key)

    async def set(self, key: str, value: T, ttl: float | None = None) -> None:
        self._data[key] = value
        if ttl:
            await asyncio.sleep(ttl)
            await self.delete(key)

    async def get_or_set(self, key: str, callback: Callable[..., Awaitable[T]], *, ttl: float | None = None) -> T:
        data = await self.get(key)
        if data is None:
            data = await callback()
            await self.set(key, data, ttl=ttl)
        return data
        
    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def clear(self) -> None:
        self._data = {}
