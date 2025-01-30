from abc import ABC, abstractmethod
import asyncio
from contextlib import asynccontextmanager

from injector import Module, provider, singleton
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_scoped_session

class DatabaseConnection:
    @singleton
    def __init__(self, connection_url: str, migration_url: str, option: dict | None = None) -> None:
        if option is None:
            option = {}

        self.connection_url = connection_url
        self.migration_url  = migration_url
        self.option = option
        self.engine = self.get_engine()
        self.session = self.get_session(self.engine)

    @asynccontextmanager
    async def get_db(self):
        if self.session is None:
            raise Exception("Session is not initialized")

        async with self.session() as session:
            yield session
    
    async def close_session(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None

        if self.session:
            await self.session.close()
            self.session = None

    def get_url(self) -> str:
        return self.connection_url
    
    def get_migration_url(self) -> str:
        return self.migration_url

    def get_engine(self) -> AsyncEngine:
        return create_async_engine(self.connection_url,**self.option)

    def get_session(self, engine: AsyncEngine):
        session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=True
        )
        
        return async_scoped_session(session_factory, scopefunc=asyncio.current_task)



class ConfigInterface(ABC):
    @abstractmethod
    def db_url(self) -> str:
        pass
    
    @abstractmethod
    def migration_url(self) -> str:
        pass
    
    @abstractmethod
    def get_option(self) -> dict:
        pass


class AppConfig(Module, ConfigInterface):
    @singleton
    @provider
    def provide_database_connection(self) -> DatabaseConnection:
        return DatabaseConnection(self.db_url(), self.migration_url(), self.get_option())
    
    def db_url(self) -> str:
        return "sqlite+aiosqlite:///test.db"
    
    def migration_url(self) -> str:
        return "sqlite:///test.db"
    
    def get_option(self) -> dict:
        return {}
