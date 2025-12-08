from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.data_service import init_data
from app.dependencies import get_db

router = APIRouter()


@router.post("/init")
def init(db: Session = Depends(get_db)):
    return init_data(db=db)
