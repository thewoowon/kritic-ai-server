from sqlalchemy import Column, String, Text, Integer, JSON, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Analysis(Base):
    __tablename__ = "analysis"

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    original_response = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    models_used = Column(JSON, nullable=False)  # List of model names
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.pending, nullable=False)
    results = Column(JSON, nullable=True)  # Stores the complete analysis results
    credits_used = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="analyses")
