from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Lifespan: Starting up...")
    # Create database tables on startup
    from app.db.base import Base
    from app.db.session import sync_engine
    print("Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("Database tables created successfully!")
    yield
    print("Lifespan: Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS 설정
# 개발: 모든 오리진 허용, 프로덕션: BACKEND_CORS_ORIGINS 환경변수 사용
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 개발 환경: 모든 오리진 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Set all CORS enabled origins
# if settings.BACKEND_CORS_ORIGINS:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[str(origin)
#                        for origin in settings.BACKEND_CORS_ORIGINS],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

app.include_router(api_router, prefix=settings.API_V1_STR)

# @app.on_event("startup")
# async def startup_event():
#     # 앱 시작 시 한 번 실행
#     await refresh_rss_feeds()


def start_uvicorn():
    import uvicorn

    # 30009 포트로 변경
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


def main():
    start_uvicorn()


if __name__ == "__main__":
    main()
