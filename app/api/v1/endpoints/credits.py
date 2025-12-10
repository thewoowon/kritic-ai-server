from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import stripe
from app.db.base import get_db
from app.schemas.transaction import CreditBalance, CreditPurchase, TransactionResponse, StripeCheckoutRequest
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.core.config import settings

router = APIRouter()

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


def get_current_user_from_header(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get user from Authorization header.
    For web OAuth flow, accepts 'Bearer <user_id>' temporarily.
    TODO: Implement proper JWT token validation.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        # Extract user_id from "Bearer <user_id>"
        scheme, user_id_str = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid authorization header")


@router.get("/credits/balance", response_model=CreditBalance)
def get_credit_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_header)
):
    """Get user's current credit balance"""
    return CreditBalance(balance=current_user.credits_balance)


@router.post("/credits/purchase", response_model=CreditBalance)
def purchase_credits(
    purchase: CreditPurchase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_header)
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
    current_user: User = Depends(get_current_user_from_header)
):
    """Get user's transaction history"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    return transactions


@router.post("/credits/create-checkout-session")
async def create_checkout_session(
    checkout_request: StripeCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_header)
):
    """Create Stripe checkout session for credit purchase"""
    try:
        # Credit packages
        packages = {
            "starter": {"credits": 100, "price": 1000},  # $10.00
            "pro": {"credits": 300, "price": 2500},      # $25.00
            "business": {"credits": 700, "price": 5000}   # $50.00
        }

        if checkout_request.package not in packages:
            raise HTTPException(status_code=400, detail="Invalid package")

        package = packages[checkout_request.package]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': package['price'],
                        'product_data': {
                            'name': f'{package["credits"]} Kritic Credits',
                            'description': f'Purchase {package["credits"]} credits for AI Reality Check analysis',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=checkout_request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=checkout_request.cancel_url,
            client_reference_id=str(current_user.id),
            metadata={
                'user_id': current_user.id,
                'credits': package['credits'],
                'package': checkout_request.package
            }
        )

        return {"checkout_url": checkout_session.url, "session_id": checkout_session.id}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/credits/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = int(session['metadata']['user_id'])
        credits = int(session['metadata']['credits'])
        package = session['metadata']['package']

        # Add credits to user
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits_balance += credits

            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                type=TransactionType.purchase,
                amount=credits,
                description=f"Purchased {package} package ({credits} credits) via Stripe"
            )
            db.add(transaction)
            db.commit()

    return {"status": "success"}
