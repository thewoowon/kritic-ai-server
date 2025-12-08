from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from fastapi.responses import JSONResponse


def create_user(db: Session, user: UserCreate):
    db_user = User(name=user.name,
                   nickname=user.nickname,
                   email=user.email,
                   phone_number=user.phone_number,
                   address=user.address,
                   src=user.src)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def update_user(db: Session, user_id: int, request: Request):

    context = await request.json()
    user = UserUpdate(**context)

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.nickname = user.nickname if user.nickname else db_user.nickname
    db_user.address = user.address if user.address else db_user.address
    db_user.src = user.src if user.src else db_user.src
    db_user.accident_date = user.accident_date if user.accident_date else db_user.accident_date
    db_user.job = user.job if user.job else db_user.job
    db_user.job_description = user.job_description if user.job_description else db_user.job_description
    db_user.is_job_open = user.is_job_open if user.is_job_open else db_user.is_job_open
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    # Kritic 프로젝트: 관련된 분석과 트랜잭션은 cascade로 삭제됨
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)


def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_user_by_nickname(db: Session, nickname: str):
    user = db.query(User).filter(User.nickname == nickname).first()
    if not user:
        return JSONResponse(content={
            "message": "Nickname is available", "is_available": True}, status_code=200)
    return JSONResponse(content={"message": "Nickname is already taken", "is_available": False}, status_code=200)


def get_user_by_email(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
# Compare this snippet from app/api/v1/endpoints/user.py:
