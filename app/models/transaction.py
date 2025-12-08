from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class TransactionType(str, enum.Enum):
    purchase = "purchase"
    usage = "usage"
    refund = "refund"


class Transaction(Base):
    __tablename__ = "transaction"

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Integer, nullable=False)  # Positive for purchase/refund, negative for usage
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="transactions")
