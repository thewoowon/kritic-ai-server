from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.schemas.transaction import CreditBalance, CreditPurchase, TransactionResponse
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.api.v1.endpoints.analyze import get_current_user

router = APIRouter()


@router.get("/credits/balance", response_model=CreditBalance)
def get_credit_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's current credit balance"""
    return CreditBalance(balance=current_user.credits_balance)


@router.post("/credits/purchase", response_model=CreditBalance)
def purchase_credits(
    purchase: CreditPurchase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Purchase credits (Stripe integration would go here)"""

    # For MVP, we'll just add credits without actual payment processing
    # In production, integrate with Stripe API here

    current_user.credits_balance += purchase.amount

    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.purchase,
        amount=purchase.amount,
        description=f"Purchased {purchase.amount} credits"
    )
    db.add(transaction)
    db.commit()
    db.refresh(current_user)

    return CreditBalance(balance=current_user.credits_balance)


@router.get("/credits/history", response_model=List[TransactionResponse])
def get_transaction_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's transaction history"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    return transactions
