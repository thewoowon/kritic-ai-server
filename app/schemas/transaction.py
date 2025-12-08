from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: int
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: TransactionType
    amount: int
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreditPurchase(BaseModel):
    amount: int  # Number of credits to purchase
    payment_method: str  # Stripe token


class CreditBalance(BaseModel):
    balance: int
