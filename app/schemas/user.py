from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    # 기본 정보
    # 회원가입 시 필수
    name: str
    nickname: Optional[str] = None
    # 회원가입 시 필수
    email: str
    # 회원가입 시 필수
    phone_number: Optional[str] = None
    address: Optional[str] = None
    src: Optional[str] = None
    is_auto_login: int = 0
    job: Optional[str] = None
    job_description: Optional[str] = None
    is_job_open: Optional[int] = 0


class UserCreate(UserBase):
    # 그대로 상속
    # 패스워드 필요 없음
    pass


class UserUpdate(BaseModel):
    # 업데이트 가능 필드만 Optional로 정의
    nickname: Optional[str] = None
    address: Optional[str] = None
    src: Optional[str] = None
    accident_date: Optional[datetime] = None
    job: Optional[str] = None
    job_description: Optional[str] = None
    is_job_open: Optional[int] = None


class UserResponse(UserBase):
    # 응답에 id 추가
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
