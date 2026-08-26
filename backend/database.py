import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Text, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "recoverai.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()


class LivePaymentModel(Base):
    __tablename__ = "live_payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="created")
    payment_method = Column(String(50), default="Card")
    bank = Column(String(100), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_description = Column(Text, nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIIntelligenceResultModel(Base):
    __tablename__ = "ai_intelligence_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), index=True, nullable=False)
    recovery_probability = Column(Float, nullable=True)
    prediction_band = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    prediction_mode = Column(String(100), nullable=True)
    feature_completeness = Column(Float, nullable=True)
    root_cause = Column(Text, nullable=True)
    root_cause_confidence = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=True)
    recommendation_score = Column(Float, nullable=True)
    expected_recovery_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RecoveryActionModel(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    action_type = Column(String(50), nullable=False)
    status = Column(String(50), default="executed")
    execution_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class PaymentEventModel(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    event_description = Column(Text, nullable=False)
    metadata_json = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookEventModel(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    payment_id = Column(String(100), nullable=True)
    event_type = Column(String(100), nullable=False)
    processed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initializes SQLite database tables automatically."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency or helper to retrieve a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
