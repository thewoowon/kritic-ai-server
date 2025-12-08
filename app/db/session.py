from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from decouple import config

# 데이터베이스 URL (기본적으로 비동기 URL 사용)
DATABASE_URL = config(
    "DATABASE_URL", default="sqlite+aiosqlite:///./app/db/mnm.db")

# URL 변환 함수
def get_async_url(url: str) -> str:
    """동기 URL을 비동기 URL로 변환"""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://")
    return url

def get_sync_url(url: str) -> str:
    """비동기 URL을 동기 URL로 변환"""
    return url.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")

# 비동기 URL 준비
async_url = get_async_url(DATABASE_URL)

# 비동기 엔진 및 세션 설정
async_engine = create_async_engine(
    async_url,
    echo=True,
)
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

# 동기 엔진 및 세션 설정 (Alembic 전용)
sync_database_url = get_sync_url(async_url)
sync_engine = create_engine(
    sync_database_url,
    echo=True,
)
SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)
