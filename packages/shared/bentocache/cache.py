# inspired by https://github.com/Julien-R44/bentocache

from typing import Awaitable, Callable, NotRequired, TypedDict
from packages.shared.bentocache.strategy.interface import ICacheStrategy

class StoreParams(TypedDict):
    l1_layer: ICacheStrategy
    l2_layer: NotRequired[ICacheStrategy]

class CacheStack:
    def __init__(self, store: StoreParams) -> None:
        
        self.l1_layer: ICacheStrategy = store['l1_layer']
        self.l2_layer: ICacheStrategy | None = store.get('l2_layer')
    

class BentoCache:
    def __init__(self, store: StoreParams, prefix: str = 'bento'):
        self.stack = CacheStack(store)

    def namespace[T](self, name:str):
        return Cache[T](name, self.stack)

class Cache[T]:
    def __init__(self, name: str, stack: CacheStack) -> None:
        self.name = name
        self.stack = stack
        
    def get_key(self, key: str) -> str:
        return f"{self.name}:{key}"
    
    async def get(self, key: str) -> T | None:
        data = await self.stack.l1_layer.get(self.get_key(key))
        if data is None and self.stack.l2_layer:
            return await self.stack.l2_layer.get(self.get_key(key))
    
    async def set(self, key: str, value: T, ttl: float | None = None) -> None:
        await self.stack.l1_layer.set(self.get_key(key), value, ttl=ttl)
        if self.stack.l2_layer:
            await self.stack.l2_layer.set(self.get_key(key), value, ttl=ttl)

    async def get_or_set(self, key: str, callback: Callable[..., Awaitable[T]], *, ttl: float | None = None) -> T:
        data = await self.get(key)
        if data is None:
            data = await callback()
            await self.set(key, data, ttl=ttl)
        return data

    async def delete(self, key: str):
        await self.stack.l1_layer.delete(self.get_key(key))
        if self.stack.l2_layer:
            await self.stack.l2_layer.delete(self.get_key(key))
