from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL_SYNC, echo=False)


AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():

    async with AsyncSessionLocal() as session:
        yield session
