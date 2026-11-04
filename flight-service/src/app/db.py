from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
