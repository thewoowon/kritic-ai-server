from fastapi import APIRouter
from app.api.v1.endpoints import analyze, credits

api_router = APIRouter()

# Kritic 프로젝트 - 분석과 크레딧 엔드포인트만 사용
api_router.include_router(
    analyze.router, prefix="", tags=["analyze"]
)
api_router.include_router(
    credits.router, prefix="", tags=["credits"]
)

# 기존 프로젝트 엔드포인트들 (필요시 주석 해제)
# from app.api.v1.endpoints import user, auth, data
# api_router.include_router(user.router, prefix="/users", tags=["users"])
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(data.router, prefix="/data", tags=["data"])
