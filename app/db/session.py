from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from decouple import config

# 데이터베이스 URL
DATABASE_URL = config(
    "DATABASE_URL", default="sqlite:///./kritic.db")

# URL 변환 함수
def get_async_url(url: str) -> str:
    """동기 URL을 비동기 URL로 변환"""
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        # Railway uses postgres:// which needs to be replaced
        url = url.replace("postgres://", "postgresql://", 1)
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    # Already async URL
    return url

def get_sync_url(url: str) -> str:
    """URL을 동기 URL로 변환"""
    # Remove async drivers
    if "postgresql+asyncpg://" in url:
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif "sqlite+aiosqlite://" in url:
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    elif "postgres://" in url:
        return url.replace("postgres://", "postgresql://", 1)
    # Already sync URL or use psycopg2
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

# 비동기 URL 준비
async_url = get_async_url(DATABASE_URL)

# 비동기 엔진 및 세션 설정
async_engine = create_async_engine(
    async_url,
    echo=False,  # Set to False for production
)
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

# 동기 엔진 및 세션 설정 (테이블 생성용)
sync_database_url = get_sync_url(DATABASE_URL)
sync_engine = create_engine(
    sync_database_url,
    echo=False,  # Set to False for production
)
SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)
