from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.models.analysis import Analysis, AnalysisStatus
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.services.analysis_service import AnalysisService
import asyncio

router = APIRouter()


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Mock user for MVP - in production, implement JWT authentication"""
    user = db.query(User).first()
    if not user:
        # Create a default user for testing
        user = User(
            name="Test User",
            email="test@kritic.com",
            phone_number="000-0000-0000",
            credits_balance=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/analyze", response_model=dict)
async def create_analysis(
    analysis_data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new analysis request"""

    print("analysis_data.models:", analysis_data.models)
    print("current_user.credits_balance:", current_user.credits_balance)

    # Calculate credit cost
    credit_cost = len(analysis_data.models) * 10

    # Check if user has enough credits
    if current_user.credits_balance < credit_cost:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Create analysis record
    analysis = Analysis(
        user_id=current_user.id,
        original_response=analysis_data.original_response,
        context=analysis_data.context,
        models_used=analysis_data.models,
        status=AnalysisStatus.pending,
        credits_used=credit_cost
    )
    db.add(analysis)

    # Deduct credits
    current_user.credits_balance -= credit_cost

    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.usage,
        amount=-credit_cost,
        description=f"Analysis using {', '.join(analysis_data.models)}"
    )
    db.add(transaction)

    db.commit()
    db.refresh(analysis)

    # Start analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis.id,
        analysis_data.original_response,
        analysis_data.context,
        analysis_data.models
    )

    return {"analysis_id": analysis.id}


async def run_analysis(
    analysis_id: int,
    original_response: str,
    context: str,
    models: List[str]
):
    """Run the analysis in the background"""
    from app.db.session import SyncSessionLocal

    db = SyncSessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return

        analysis.status = AnalysisStatus.processing
        db.commit()

        # Run the analysis
        service = AnalysisService()
        result = await service.analyze(original_response, context, models)

        # Update analysis with results
        analysis.results = result
        analysis.status = AnalysisStatus.completed
        db.commit()

    except Exception as e:
        print(f"Analysis failed: {e}")
        if analysis:
            analysis.status = AnalysisStatus.failed
            db.commit()
    finally:
        db.close()


@router.get("/analyze/{analysis_id}", response_model=dict)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analysis results"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    response_data = {
        "id": analysis.id,
        "original_response": analysis.original_response,
        "context": analysis.context,
        "status": analysis.status.value,
        "credits_used": analysis.credits_used,
        "created_at": analysis.created_at.isoformat(),
    }

    if analysis.status == AnalysisStatus.completed and analysis.results:
        response_data.update(analysis.results)

    return response_data


@router.get("/analyze/history", response_model=List[AnalysisResponse])
def get_analysis_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's analysis history"""
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()

    return analyses
