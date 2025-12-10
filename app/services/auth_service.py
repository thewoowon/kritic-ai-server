
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.services.user_service import create_user
from app.core.security import decode_token
import requests
import jwt
try:
    from jwt.algorithms import RSAAlgorithm
except ImportError:
    from jwt import PyJWK
    RSAAlgorithm = None
from datetime import datetime, timedelta, timezone
from settings import (
    DEFAULT_PROFILE_PIC,
    GOOGLE_TOKEN_INFO_URL,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.models.user import User
from app.schemas.user import UserCreate
from app.models.token import Token
import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Apple 공개 키 URL
APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY,
                             algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY,
                             algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def google_auth(request: Request, db: Session):
    try:
        data = await request.json()
        id_token = data.get("id_token")
        is_auto_login = data.get("is_selected")

        if not id_token:
            raise HTTPException(status_code=400, detail="ID token is required")

        # Google 서버에 idToken 검증 요청
        try:
            response = requests.get(GOOGLE_TOKEN_INFO_URL, params={
                                    "id_token": id_token})
            response.raise_for_status()  # HTTP 에러 처리
        except requests.RequestException as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to verify token: {str(e)}")

        # 2. 검증 결과 확인
        token_info = response.json()
        email = token_info.get("email")

        if not email:
            raise HTTPException(
                status_code=400, detail="Email is missing in token")

        # 사용자 조회 또는 생성
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # 새로운 사용자 생성
            user = create_user(
                db=db,
                user=UserCreate(
                    name=token_info.get("name", "Unknown"),
                    nickname="",
                    email=email,
                    phone_number="",
                    address="",
                    src=DEFAULT_PROFILE_PIC,
                    is_auto_login=is_auto_login,
                    job="",
                    job_description="",
                    is_job_open=0,
                ),
            )

        # 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=refresh_token_expires
        )

        # Refresh Token을 DB에 저장 (Google)
        existing_token = db.query(Token).filter(Token.user_id == user.id).first()
        if existing_token:
            existing_token.refresh_token = refresh_token
            existing_token.is_active = True
        else:
            new_token = Token(
                user_id=user.id,
                refresh_token=refresh_token,
                is_active=True
            )
            db.add(new_token)
        db.commit()

        # 사용자 데이터 및 토큰 반환
        user_data = {
            "id": user.id,
            "name": user.name,
            "nickname": user.nickname,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": user.address,
            "src": user.src,
            "is_auto_login": user.is_auto_login,
            "job": user.job,
            "job_description": user.job_description,
            "is_job_open": user.is_job_open,
        }

        # RN 앱 형식에 맞게 헤더로 토큰 반환
        return JSONResponse(
            content={"user": user_data},
            status_code=200,
            headers={
                "Authorization": f"Bearer {access_token}",
                "RefreshToken": f"RefreshToken {refresh_token}",
            },
        )
    except Exception as e:
        print("Error:", e)
        print("Failed to verify token")
        raise HTTPException(status_code=400, detail="Invalid token")


async def google_auth_web(request: Request, db: Session):
    """
    Google OAuth for web - accepts either 'code' (authorization code flow) or 'token' (id_token flow)
    """
    try:
        data = await request.json()
        code = data.get("code")
        id_token = data.get("token")

        # Handle id_token flow (from NextAuth)
        if id_token:
            # Google 서버에 idToken 검증 요청
            try:
                response = requests.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": id_token})
                response.raise_for_status()
            except requests.RequestException as e:
                raise HTTPException(status_code=400, detail=f"Failed to verify token: {str(e)}")

            token_info = response.json()
            email = token_info.get("email")

            if not email:
                raise HTTPException(status_code=400, detail="Email is missing in token")

            # 사용자 조회 또는 생성
            user = db.query(User).filter(User.email == email).first()

            if not user:
                # 새로운 사용자 생성 (초기 100 크레딧 자동 부여)
                user = create_user(
                    db=db,
                    user=UserCreate(
                        name=token_info.get("name", "Unknown"),
                        nickname="",
                        email=email,
                        phone_number="",
                        address="",
                        src=token_info.get("picture", DEFAULT_PROFILE_PIC),
                        is_auto_login=False,
                        job="",
                        job_description="",
                        is_job_open=0,
                    ),
                )

            # JWT 토큰 생성 (30일 유효)
            access_token_expires = timedelta(days=30)
            access_token = create_access_token(
                data={"sub": user.email, "user_id": user.id},
                expires_delta=access_token_expires
            )

            return JSONResponse(
                content={
                    "user_id": user.id,
                    "access_token": access_token
                },
                status_code=200,
            )

        # Handle authorization code flow (original implementation)
        if not code:
            raise HTTPException(status_code=400, detail="code or token is required")

        REDIRECT_URI = "https://lululala.at/auth/callback/google"
        print("REDIRECT_URI:", REDIRECT_URI)

        # 🔹 1. Google 서버에서 Access Token 요청
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }

        token_res = requests.post(token_url, data=token_data)
        token_json = token_res.json()

        print("token_json:", token_json)

        if "access_token" not in token_json:
            raise HTTPException(
                status_code=400, detail="Failed to get access token")

        access_token = token_json["access_token"]

        # 🔹 2. Access Token을 사용해 사용자 정보 요청
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_res = requests.get(user_info_url, headers={
                                "Authorization": f"Bearer {access_token}"})
        user_json = user_res.json()

        if "email" not in user_json:
            raise HTTPException(
                status_code=400, detail="Failed to get user info")

        email = user_json["email"]

        if not email:
            raise HTTPException(
                status_code=400, detail="Email is missing in token")

        # 사용자 조회 또는 생성
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # 새로운 사용자 생성 (초기 100 크레딧 자동 부여)
            user = create_user(
                db=db,
                user=UserCreate(
                    name=user_json.get("name", "Unknown"),
                    nickname="",
                    email=email,
                    phone_number="",
                    address="",
                    src=user_json.get("picture", DEFAULT_PROFILE_PIC),
                    is_auto_login=False,
                    job="",
                    job_description="",
                    is_job_open=0,
                ),
            )

        # 토큰 생성
        access_token_expires = timedelta(minutes=10)

        # 10분 뒤 만료되는 토큰 발급
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
        )

        # 사용자 데이터 및 토큰 반환
        user_data = {
            "id": user.id,
            "name": user.name,
            "nickname": user.nickname,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": user.address,
            "src": user.src,
            "is_auto_login": user.is_auto_login,
            "job": user.job,
            "job_description": user.job_description,
            "is_job_open": user.is_job_open,
        }

        return JSONResponse(
            content={
                "user_id": user.id,
                "user": user_data,
                "access_token": access_token,
            },
            status_code=200,
        )
    except Exception as e:
        print("Error:", e)
        print("Failed to verify token")
        return JSONResponse(
            content={"user": "", "access_token": ""},
            status_code=200,
        )


def naver_auth(access_token: str):
    response = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid token")
    user_info = response.json()
    return JSONResponse(content={"user": user_info}, status_code=200)


def kakao_auth(access_token: str):
    response = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid token")
    user_info = response.json()
    return JSONResponse(content={"user": user_info}, status_code=200)


async def apple_notification(request: Request, db: Session):
    try:
        payload = await request.json()
        notification_type = payload.get("notification_type")
        sub = payload.get("sub")

        if notification_type == "REVOKE":
            # 사용자 계정 처리 (ex. Apple 로그인 해제)
            print(f"User {sub} revoked Apple login")

        return {"status": "received"}
    except Exception as e:
        print("Error", e)
        print("Failed to verify token")
        raise HTTPException(status_code=400, detail="Invalid token")


def get_apple_public_keys():
    response = requests.get(APPLE_PUBLIC_KEYS_URL)
    return response.json()["keys"]


def decode_and_verify_identity_token(identity_token: str, audience: str):
    """Apple의 identityToken을 검증 및 디코딩"""

    # 1. Apple 공개 키 가져오기
    apple_keys = get_apple_public_keys()

    # 2. identityToken의 헤더에서 'kid' 값을 가져옴
    header = jwt.get_unverified_header(identity_token)
    key = next((k for k in apple_keys if k["kid"] == header["kid"]), None)

    if key is None:
        raise ValueError(
            "Invalid identityToken: No matching Apple public key found.")

    print("key:", key)

    # 3. Apple 공개 키를 PEM 형식으로 변환
    public_key = RSAAlgorithm.from_jwk(key)  # ✅ RSAAlgorithm 사용

    print(public_key)

    # 4. JWT 디코딩 및 검증
    decoded_token = jwt.decode(
        identity_token,
        public_key,
        algorithms=["RS256"],
        audience=audience,  # 반드시 iOS의 번들 ID와 일치해야 함
        issuer="https://appleid.apple.com"
    )

    print("decoded_token:", decoded_token)

    return decoded_token


async def apple_auth(request: Request, db: Session):
    try:
        print("apple_auth")
        payload = await request.json()
        identity_token = payload.get("identityToken")
        # authorization_code = payload.get("authorizationCode")

        decoded_token = decode_and_verify_identity_token(
            identity_token, "com.lululala.gngm")

        # Apple이 제공한 이메일 (최초 로그인 시만 제공)
        email = decoded_token.get("email")

        full_name = decoded_token.get("full_name")

        if not email:
            raise HTTPException(
                status_code=400, detail="Email is missing in token")

        if not full_name:
            full_name = {
                "given_name": "Unknown",
                "family_name": "Unknown"
            }

        # 사용자 조회 또는 생성
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # 새로운 사용자 생성
            user = create_user(
                db=db,
                user=UserCreate(
                    name=full_name.get("given_name", "Unknown") +
                    " " + full_name.get("family_name", "Unknown"),
                    nickname="",
                    email=email,
                    phone_number="",
                    address="",
                    src=DEFAULT_PROFILE_PIC,
                    is_auto_login=False,
                    job="",
                    job_description="",
                    is_job_open=0,
                ),
            )

        # 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=refresh_token_expires
        )

        # Refresh Token을 DB에 저장 (Apple)
        existing_token = db.query(Token).filter(Token.user_id == user.id).first()
        if existing_token:
            existing_token.refresh_token = refresh_token
            existing_token.is_active = True
        else:
            new_token = Token(
                user_id=user.id,
                refresh_token=refresh_token,
                is_active=True
            )
            db.add(new_token)
        db.commit()

        # 사용자 데이터 및 토큰 반환
        user_data = {
            "id": user.id,
            "name": user.name,
            "nickname": user.nickname,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": user.address,
            "src": user.src,
            "is_auto_login": user.is_auto_login,
            "job": user.job,
            "job_description": user.job_description,
            "is_job_open": user.is_job_open,
        }

        # RN 앱 형식에 맞게 헤더로 토큰 반환
        return JSONResponse(
            content={"user": user_data},
            status_code=200,
            headers={
                "Authorization": f"Bearer {access_token}",
                "RefreshToken": f"RefreshToken {refresh_token}",
            },
        )

    except Exception as e:
        print("Error:", e)
        print("Failed to verify token")
        raise HTTPException(status_code=400, detail="Invalid token")


async def refresh_token_func(request: Request, db: Session):
    try:
        # 1. Request Body에서 refreshToken 추출
        data = await request.json()
        refresh_token = data.get("refreshToken")

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required"
            )

        # 2. Refresh Token 디코딩 및 검증
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = payload.get("user_id")
        email = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # 3. DB에서 refresh_token 조회
        token_obj = db.query(Token).filter(
            Token.user_id == user_id,
            Token.refresh_token == refresh_token
        ).first()

        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        if not token_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive refresh token"
            )

        # 4. 새로운 Access Token & Refresh Token 발급
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        new_access_token = create_access_token(
            data={"sub": email, "user_id": user_id}, expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            data={"sub": email, "user_id": user_id}, expires_delta=refresh_token_expires
        )

        # 5. DB의 refresh_token 업데이트
        token_obj.refresh_token = new_refresh_token
        db.commit()

        # 6. RN 앱 형식에 맞게 헤더로 반환
        return JSONResponse(
            content={"message": "Token refreshed successfully"},
            status_code=200,
            headers={
                "Authorization": f"Bearer {new_access_token}",
                "RefreshToken": f"RefreshToken {new_refresh_token}",
            },
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


def guest_login(db: Session):
    try:
        # guest login은 email이 guest@lululala.com
        user = db.query(User).filter(
            User.email == "guest@lululala.com").first()

        print("user:", user)

        # 토큰 생성 -> 1시간 뒤 만료되는 토큰 발급
        access_token_expires = timedelta(minutes=60)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=refresh_token_expires
        )

        # Refresh Token을 DB에 저장 (Guest)
        existing_token = db.query(Token).filter(Token.user_id == user.id).first()
        if existing_token:
            existing_token.refresh_token = refresh_token
            existing_token.is_active = True
        else:
            new_token = Token(
                user_id=user.id,
                refresh_token=refresh_token,
                is_active=True
            )
            db.add(new_token)
        db.commit()

        # 사용자 데이터 및 토큰 반환
        user_data = {
            "id": user.id,
            "name": user.name,
            "nickname": user.nickname,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": user.address,
            "src": user.src,
            "is_auto_login": user.is_auto_login,
            "job": user.job,
            "job_description": user.job_description,
            "is_job_open": user.is_job_open,
        }

        # RN 앱 형식에 맞게 헤더로 토큰 반환
        return JSONResponse(
            content={"user": user_data},
            status_code=200,
            headers={
                "Authorization": f"Bearer {access_token}",
                "RefreshToken": f"RefreshToken {refresh_token}",
            },
        )

    except Exception as e:
        print("Error:", e)
        print("Failed to verify token")
        raise HTTPException(status_code=400, detail="Invalid token")
