import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


def decode_token(token: str):
    try:
        logger.info(f"Decoding token: {token}")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            logger.warning("Invalid token: Missing user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "JWT_VALIDATE_ERROR",
                    "message": "인증정보가 유효하지 않습니다.",
                    "name": "TokenValidationException",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"Token is valid. User ID: {user_id}")
        return user_id
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "JWT_VERIFY_EXPIRED",
                "message": "인증정보가 만료 됐습니다.",
                "name": "TokenExpiredException",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "JWT_VALIDATE_ERROR",
                "message": "인증정보가 유효하지 않습니다.",
                "name": "TokenValidationException",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)):
    logger.info(f"Received token: {token}")
    return decode_token(token)
